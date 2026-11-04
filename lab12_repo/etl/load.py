"""ELT: raw CSV -> DuckDB staging -> star schema (sql/ddl.sql) -> data-quality checks -> Parquet + dataset version.
Run: python3 etl/load.py   (needs data/raw/*.csv; make them with python3 etl/generate.py)"""
import duckdb, pandas as pd, json, hashlib, sys, platform
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; RAW = ROOT / "data/raw"; PQ = ROOT / "data/parquet"; DB = ROOT / "data/warehouse.duckdb"
IRI_BASE = "http://example.org/knowledge-hub/biomed/"; DATASET_VERSION = "1.0.0"
sys.path.insert(0, str(ROOT))

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def build_taxon(con):
    t = pd.read_csv(RAW / "taxonomy_final.csv", encoding="utf-8-sig", dtype=str).fillna("")
    t = t.rename(columns={"id": "notation"}); by = {r.notation: r for r in t.itertuples()}; t["taxon_key"] = range(1, len(t) + 1); key = dict(zip(t.notation, t.taxon_key))
    def chain(n):
        out = []
        while n: out.append(n); n = by[n].parent
        return out[::-1]                                   # root ... n
    kids = set(t.parent) - {""}; rows = []
    for r in t.itertuples():
        c = chain(r.notation)
        rows.append((r.taxon_key, IRI_BASE + r.notation, r.notation, r.label, r.label_uk or None, int(r.level), key.get(r.parent) if r.parent else None,
                     by[c[1]].label if len(c) > 1 else None, by[c[2]].label if len(c) > 2 else None, " > ".join(by[x].label for x in c), r.notation not in kids))
    con.executemany("INSERT INTO dim_taxon VALUES (?,?,?,?,?,?,?,?,?,?,?)", rows)

def main():
    for f in ("calls_raw.csv", "samples_raw.csv", "pipelines_raw.csv", "genes_raw.csv", "pipeline_day_raw.csv", "taxonomy_final.csv"):
        assert (RAW / f).exists(), f"missing {f}: run python3 etl/generate.py"
    DB.unlink(missing_ok=True); con = duckdb.connect(str(DB))
    con.execute((ROOT / "sql/ddl.sql").read_text())
    # ---- staging (E, L): raw files as they are
    con.execute(f"CREATE OR REPLACE TABLE stg_calls AS SELECT *, row_number() OVER () AS _row FROM read_csv_auto('{(RAW / 'calls_raw.csv').as_posix()}', header=true, all_varchar=true, parallel=false)")
    for n, f in (("samples", "samples_raw.csv"), ("pipelines", "pipelines_raw.csv"), ("genes", "genes_raw.csv"), ("pipe_day", "pipeline_day_raw.csv")):
        con.execute(f"CREATE OR REPLACE TABLE stg_{n} AS SELECT * FROM read_csv_auto('{(RAW / f).as_posix()}', header=true, all_varchar=true)")
    # ---- T: dimensions
    build_taxon(con)
    con.execute("INSERT INTO dim_date SELECT CAST(strftime(d,'%Y%m%d') AS INT), d::DATE, year(d), quarter(d), month(d), monthname(d), weekofyear(d), isodow(d), isodow(d)>=6 FROM (SELECT unnest(generate_series(DATE '2025-01-01', DATE '2026-12-31', INTERVAL 1 DAY)) AS d)")
    con.execute("INSERT INTO dim_sample SELECT row_number() OVER (ORDER BY sample_code), sample_code, cohort, tissue, platform, batch, qc_status FROM stg_samples")
    con.execute("INSERT INTO dim_gene SELECT row_number() OVER (ORDER BY gene_symbol), gene_symbol, chromosome FROM stg_genes")
    con.execute("""INSERT INTO dim_pipeline SELECT row_number() OVER (ORDER BY p.family, p.valid_from), p.family, p.tool, p.version, p.valid_from::DATE, p.valid_to::DATE, p.valid_to = '9999-12-31',
                   (SELECT taxon_key FROM dim_taxon WHERE notation='C060'), (SELECT taxon_key FROM dim_taxon WHERE label = p.filter_procedure) FROM stg_pipelines p""")
    # ---- quarantine bad call rows BEFORE the fact load (one reason per row; duplicates: first occurrence in the file wins)
    con.execute("""CREATE TABLE rejected_calls AS SELECT * FROM (
      SELECT c.*, CASE WHEN try_cast(c.call_date AS DATE) IS NULL THEN 'bad_date' WHEN c.gene_symbol IS NULL OR c.gene_symbol = '' THEN 'null_gene'
                       WHEN s.sample_code IS NULL THEN 'unknown_sample' WHEN try_cast(c.read_depth AS INT) NOT BETWEEN 1 AND 1000 THEN 'depth_out_of_range'
                       WHEN c._row > min(c._row) OVER (PARTITION BY c.call_id) THEN 'duplicate_call_id' END AS reject_reason
      FROM stg_calls c LEFT JOIN stg_samples s USING (sample_code)) WHERE reject_reason IS NOT NULL""")
    con.execute("CREATE TABLE stg_calls_ok AS SELECT c.* FROM stg_calls c ANTI JOIN rejected_calls r ON r._row = c._row")   # materialised: only valid rows reach the casts
    # ---- T: facts (surrogate-key lookup; SCD2 version valid on the call date; taxonomy lookup by label inside the right branch)
    tx = lambda role_notation: f"(SELECT t.taxon_key FROM dim_taxon t WHERE t.label = c.{role_notation[0]} AND t.facet_label = '{role_notation[1]}')"
    con.execute(f"""INSERT INTO fact_variant_call
      SELECT c.call_id::INT, CAST(strftime(c.call_date::DATE,'%Y%m%d') AS INT), s.sample_key, g.gene_key, p.pipeline_key,
             {tx(('variant_type','genetic variant'))}, {tx(('origin','Variant by origin'))}, {tx(('clinical_significance','Variant by clinical significance'))},
             1, c.is_pass::INT, c.review_minutes::DOUBLE, c.read_depth::INT, c.qual::DOUBLE, c.alt_fraction::DOUBLE
      FROM stg_calls_ok c
      JOIN dim_sample s ON s.sample_code = c.sample_code JOIN dim_gene g ON g.gene_symbol = c.gene_symbol
      JOIN dim_pipeline p ON p.family = c.pipeline_family AND c.call_date::DATE BETWEEN p.valid_from AND p.valid_to""")
    con.execute("""INSERT INTO fact_pipeline_day SELECT CAST(strftime(d.snap_date::DATE,'%Y%m%d') AS INT), p.pipeline_key, d.runs_started::INT, d.cpu_hours::DOUBLE, d.queue_backlog::DOUBLE
                   FROM stg_pipe_day d JOIN dim_pipeline p ON p.family = d.pipeline_family AND d.snap_date::DATE BETWEEN p.valid_from AND p.valid_to""")
    # ---- data-quality checks
    checks = []
    def chk(name, sql, expect_zero=True, note=""):
        v = con.execute(sql).fetchone()[0]; checks.append(dict(name=name, sql=" ".join(sql.split()), value=int(v), ok=(v == 0) if expect_zero else bool(v), note=note))
    chk("raw_vs_loaded_reconciliation", "SELECT (SELECT count(*) FROM stg_calls) - (SELECT count(*) FROM fact_variant_call) - (SELECT count(*) FROM rejected_calls)", note="raw rows = loaded + rejected")
    chk("not_null_foreign_keys", "SELECT count(*) FROM fact_variant_call WHERE date_key IS NULL OR sample_key IS NULL OR gene_key IS NULL OR pipeline_key IS NULL OR variant_type_key IS NULL OR origin_key IS NULL OR significance_key IS NULL")
    chk("unique_call_id", "SELECT count(*) - count(DISTINCT call_id) FROM fact_variant_call")
    chk("range_read_depth_qual_af", "SELECT count(*) FROM fact_variant_call WHERE read_depth NOT BETWEEN 1 AND 1000 OR qual NOT BETWEEN 0 AND 255 OR alt_fraction NOT BETWEEN 0 AND 1")
    chk("flag_is_pass_binary", "SELECT count(*) FROM fact_variant_call WHERE is_pass NOT IN (0,1)")
    chk("dates_in_calendar_2025_2026", "SELECT count(*) FROM fact_variant_call f LEFT JOIN dim_date d USING (date_key) WHERE d.date_key IS NULL OR d.year NOT IN (2025, 2026)")
    for tbl, col, dim, dk in (("fact_variant_call", "sample_key", "dim_sample", "sample_key"), ("fact_variant_call", "gene_key", "dim_gene", "gene_key"), ("fact_variant_call", "pipeline_key", "dim_pipeline", "pipeline_key"),
                              ("fact_variant_call", "variant_type_key", "dim_taxon", "taxon_key"), ("fact_variant_call", "origin_key", "dim_taxon", "taxon_key"), ("fact_variant_call", "significance_key", "dim_taxon", "taxon_key"),
                              ("fact_variant_call", "date_key", "dim_date", "date_key"), ("fact_pipeline_day", "pipeline_key", "dim_pipeline", "pipeline_key")):
        chk(f"orphans_{tbl}.{col}", f"SELECT count(*) FROM {tbl} f LEFT JOIN {dim} d ON f.{col} = d.{dk} WHERE d.{dk} IS NULL", note="no orphans")
    chk("taxon_role_variant_type_under_C022", "SELECT count(*) FROM fact_variant_call f JOIN dim_taxon t ON t.taxon_key = f.variant_type_key WHERE t.facet_label <> 'genetic variant' OR NOT t.is_leaf")
    chk("taxon_role_origin_under_C029", "SELECT count(*) FROM fact_variant_call f JOIN dim_taxon t ON t.taxon_key = f.origin_key WHERE t.facet_label <> 'Variant by origin'")
    chk("taxon_role_significance_under_C032", "SELECT count(*) FROM fact_variant_call f JOIN dim_taxon t ON t.taxon_key = f.significance_key WHERE t.facet_label <> 'Variant by clinical significance'")
    chk("scd2_no_overlap_per_family", "SELECT count(*) FROM dim_pipeline a JOIN dim_pipeline b ON a.family = b.family AND a.pipeline_key < b.pipeline_key AND a.valid_from <= b.valid_to AND b.valid_from <= a.valid_to")
    chk("scd2_one_current_per_family", "SELECT count(*) FROM (SELECT family FROM dim_pipeline GROUP BY 1 HAVING sum(is_current::INT) <> 1)")
    chk("pipeline_day_complete_4_per_day", "SELECT count(*) FROM (SELECT date_key FROM fact_pipeline_day GROUP BY 1 HAVING count(*) <> 4)")
    chk("iri_unique_and_wellformed", f"SELECT count(*) FROM dim_taxon WHERE iri NOT LIKE '{IRI_BASE}C%'")
    chk("quarantine_detected_defects", "SELECT count(*) FROM rejected_calls", expect_zero=False, note="5 dirty rows injected by the generator must be caught")
    n_fact = con.execute("SELECT count(*) FROM fact_variant_call").fetchone()[0]; rej = con.execute("SELECT reject_reason, count(*) n FROM rejected_calls GROUP BY 1 ORDER BY 1").fetchall()
    # ---- Parquet + version
    PQ.mkdir(parents=True, exist_ok=True)
    tables = ["dim_date", "dim_taxon", "dim_sample", "dim_gene", "dim_pipeline", "fact_variant_call", "fact_pipeline_day", "rejected_calls"]
    for t in tables: con.execute(f"COPY (SELECT * FROM {t}) TO '{(PQ / (t + '.parquet')).as_posix()}' (FORMAT PARQUET, COMPRESSION ZSTD)")
    counts = {t: con.execute(f"SELECT count(*) FROM {t}").fetchone()[0] for t in tables}
    ver = dict(dataset="dkh_variant_calls", version=DATASET_VERSION, generator="etl/generate.py", seed=42, generator_sha256=sha(ROOT / "etl/generate.py"), ddl_sha256=sha(ROOT / "sql/ddl.sql"), taxonomy_source="Lab 5 taxonomy_final.csv", taxonomy_sha256=sha(RAW / "taxonomy_final.csv"),
               raw_sha256={f: sha(RAW / f) for f in ("calls_raw.csv", "samples_raw.csv", "pipelines_raw.csv", "genes_raw.csv", "pipeline_day_raw.csv")}, row_counts=counts,
               parquet_sha256={t: sha(PQ / (t + ".parquet")) for t in tables}, duckdb=duckdb.__version__, pandas=pd.__version__, python=platform.python_version(), synthetic=True)
    (ROOT / "data/VERSION.json").write_text(json.dumps(ver, indent=1), encoding="utf-8")
    rep = dict(dataset_version=DATASET_VERSION, fact_rows=n_fact, rejected=dict(rej), checks=checks, passed=sum(c["ok"] for c in checks), total=len(checks))
    (ROOT / "docs").mkdir(exist_ok=True); (ROOT / "docs/dq_report.json").write_text(json.dumps(rep, indent=1, ensure_ascii=False), encoding="utf-8")
    con.close(); print("fact rows", n_fact, "| rejected", dict(rej), "| DQ", rep["passed"], "/", rep["total"])
    for c in checks:
        if not c["ok"]: print("  FAIL", c["name"], c["value"])

if __name__ == "__main__": main()
