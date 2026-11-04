"""Independent check of OLAP results with pandas on the Parquet files (no SQL, no DuckDB)."""
import pandas as pd, json, math
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; P = lambda n: pd.read_parquet(ROOT / f"data/parquet/{n}.parquet")
res = json.load(open(ROOT / "eval/olap_results.json")); f, d, s, p, t, g = (P(x) for x in ("fact_variant_call", "dim_date", "dim_sample", "dim_pipeline", "dim_taxon", "dim_gene"))
rows = lambda q: pd.DataFrame(res[q]["rows"], columns=res[q]["columns"]); out = []
def cmp(name, sql_val, pd_val, tol=0.051): out.append(dict(check=name, sql=sql_val, pandas=pd_val, ok=abs(sql_val - pd_val) <= tol))
m = f.merge(d, on="date_key").merge(s, on="sample_key").merge(p, on="pipeline_key").merge(g, on="gene_key")
# 1. q01 ROLLUP: calls and pass% for 2025 Q3 and grand total
q = rows("q01_rollup_time"); r = q[(q.year == 2025) & (q.quarter == 3)].iloc[0]; x = m[(m.year == 2025) & (m.quarter == 3)]
cmp("q01 2025-Q3 calls", r.calls, len(x), 0); cmp("q01 2025-Q3 pass%", r.pass_pct, round(100 * x.is_pass.mean(), 1)); gt = q[q.year.isna()].iloc[0]; cmp("q01 grand total calls", gt.calls, len(m), 0); cmp("q01 grand total pass%", gt.pass_pct, round(100 * m.is_pass.mean(), 1))
# 2. q03 CUBE: HBOC x tumor cell, and the (ALL, blood) margin
q = rows("q03_cube_cohort_tissue"); r = q[(q.cohort == "HBOC") & (q.tissue == "tumor")].iloc[0]; x = m[(m.cohort == "HBOC") & (m.tissue == "tumor")]
cmp("q03 HBOC/tumor calls", r.calls, len(x), 0); cmp("q03 HBOC/tumor pass%", r.pass_pct, round(100 * x.is_pass.mean(), 1)); r = q[(q.cohort == "ALL") & (q.tissue == "blood")].iloc[0]; cmp("q03 ALL/blood calls", r.calls, int((m.tissue == "blood").sum()), 0)
# 3. q09 window rank: top sample of each qc group
q = rows("q09_window_rank_samples"); agg = m.groupby(["qc_status", "sample_code"]).review_minutes.sum().round(1).reset_index()
for qc in ("pass", "recheck"): top = agg[agg.qc_status == qc].sort_values("review_minutes", ascending=False).iloc[0]; r = q[(q.qc_status == qc) & (q.rnk == 1)].iloc[0]; cmp(f"q09 top review minutes ({qc})", r.review_min, top.review_minutes); out[-1]["same_sample"] = bool(r.sample_code == top.sample_code)
# 4. q13 SCD2: GATK 4.5.0.0 average quality and pass%
q = rows("q13_scd2_versions"); r = q[(q.family == "GATK") & (q.version == "4.5.0.0")].iloc[0]; x = m[(m.family == "GATK") & (m.version == "4.5.0.0")]
cmp("q13 GATK 4.5 avg_qual", r.avg_qual, round(x.qual.mean(), 1)); cmp("q13 GATK 4.5 pass%", r.pass_pct, round(100 * x.is_pass.mean(), 1)); cmp("q13 GATK 4.5 calls", r.calls, len(x), 0)
json.dump(out, open(ROOT / "eval/olap_verify.json", "w"), indent=1, default=float); print(len(out), "checks;", sum(o["ok"] for o in out), "ok")
for o in out: print(" ", "OK " if o["ok"] else "BAD", o["check"], o["sql"], o["pandas"])
