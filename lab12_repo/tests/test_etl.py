import sys, json, duckdb, pytest, pandas as pd
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT))
@pytest.fixture(scope="module")
def con(): return duckdb.connect(str(ROOT / "data/warehouse.duckdb"), read_only=True)
def test_fact_size_and_grain(con):
    n, d = con.execute("SELECT count(*), count(DISTINCT call_id) FROM fact_variant_call").fetchone(); assert n >= 1000 and n == d
def test_no_orphans(con):
    for col, dim, k in (("sample_key", "dim_sample", "sample_key"), ("gene_key", "dim_gene", "gene_key"), ("pipeline_key", "dim_pipeline", "pipeline_key"), ("date_key", "dim_date", "date_key"), ("variant_type_key", "dim_taxon", "taxon_key"), ("origin_key", "dim_taxon", "taxon_key"), ("significance_key", "dim_taxon", "taxon_key")):
        assert con.execute(f"SELECT count(*) FROM fact_variant_call f LEFT JOIN {dim} d ON f.{col}=d.{k} WHERE d.{k} IS NULL").fetchone()[0] == 0
def test_dq_report_all_pass():
    r = json.load(open(ROOT / "docs/dq_report.json")); assert r["total"] >= 5 and r["passed"] == r["total"] and r["rejected"]
def test_quarantine_caught_all_five_defects():
    r = json.load(open(ROOT / "docs/dq_report.json")); assert sum(r["rejected"].values()) == 5
def test_parquet_and_version():
    v = json.load(open(ROOT / "data/VERSION.json")); assert v["version"] and v["seed"] == 42
    for t, n in v["row_counts"].items(): assert len(pd.read_parquet(ROOT / f"data/parquet/{t}.parquet")) == n
def test_taxonomy_iri_matches_skos():
    import rdflib; g = rdflib.Graph().parse(ROOT / "data/raw/taxonomy.ttl"); ids = {str(s) for s in g.subjects(rdflib.RDF.type, rdflib.SKOS.Concept)}
    iris = {r[0] for r in duckdb.connect(str(ROOT / "data/warehouse.duckdb"), read_only=True).execute("SELECT iri FROM dim_taxon").fetchall()}; assert ids <= iris
def test_scd2_calls_use_valid_version(con):
    assert con.execute("SELECT count(*) FROM fact_variant_call f JOIN dim_pipeline p USING(pipeline_key) JOIN dim_date d USING(date_key) WHERE d.full_date NOT BETWEEN p.valid_from AND p.valid_to").fetchone()[0] == 0
def test_generator_deterministic(tmp_path):
    import importlib, etl.generate as g, hashlib
    h = lambda: hashlib.sha256((ROOT / "data/raw/calls_raw.csv").read_bytes()).hexdigest(); a = h(); importlib.reload(g); g.main(42); assert h() == a
def test_olap_has_at_least_8_queries_and_verified():
    assert len(list((ROOT / "sql/olap").glob("*.sql"))) >= 8 and all(o["ok"] for o in json.load(open(ROOT / "eval/olap_verify.json")))
