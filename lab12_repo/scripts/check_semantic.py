"""Consistency: the same business question answered by 3 different paths must give identical numbers:
 (1) SQL generated from the semantic layer, (2) hand-written OLAP SQL (sql/olap), (3) pandas on Parquet (independent code)."""
import duckdb, json, sys, pandas as pd
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT))
from semantic import sl
con = duckdb.connect(str(ROOT / "data/warehouse.duckdb"), read_only=True); P = lambda n: pd.read_parquet(ROOT / f"data/parquet/{n}.parquet")
f, d, p, g, t = P("fact_variant_call"), P("dim_date"), P("dim_pipeline"), P("dim_gene"), P("dim_taxon"); m = f.merge(d, on="date_key").merge(p, on="pipeline_key").merge(g, on="gene_key")
out = []
def same(a, b, tol=1e-9): return len(a) == len(b) and all(abs(float(x) - float(y)) <= tol for x, y in zip(a, b))
def add(q, path_vals, note=""):
    ref = path_vals[0][1]; out.append(dict(question=q, paths={n: len(v) for n, v in path_vals}, consistent=all(same(ref, v) for _, v in path_vals[1:]), note=note))
# Q1: pass rate by year
a = sl.run(con, "pass_rate", by=["year"]).pass_rate.tolist()
b = con.execute("SELECT round(100.0*sum(is_pass)/count(*),1) FROM fact_variant_call JOIN dim_date USING(date_key) GROUP BY year ORDER BY year").fetchall(); b = [x[0] for x in b]
c = (m.groupby("year").is_pass.sum() / m.groupby("year").is_pass.count() * 100).round(1).tolist(); add("What is the pass rate by year?", [("semantic layer", a), ("hand SQL", b), ("pandas", c)])
# Q2: avg quality by family, version
a = sl.run(con, "avg_qual", by=["family", "version"]).avg_qual.tolist(); b = con.execute("SELECT round(avg(qual),1) FROM fact_variant_call JOIN dim_pipeline USING(pipeline_key) GROUP BY family, version ORDER BY family, version").fetchall(); b = [x[0] for x in b]
c = m.groupby(["family", "version"]).qual.mean().round(1).tolist(); add("What is the average call quality per tool version?", [("semantic layer", a), ("hand SQL (q13-style)", b), ("pandas", c)])
# Q3: pathogenic share per gene (taxonomy role through IRI/notation)
a = sl.run(con, "pathogenic_share", by=["gene"]).pathogenic_share.tolist()
b = con.execute("SELECT round(100.0*count(*) FILTER (WHERE sg.label='pathogenic variant')/count(*),1) FROM fact_variant_call f JOIN dim_gene g USING(gene_key) JOIN dim_taxon sg ON sg.taxon_key=f.significance_key GROUP BY g.gene_symbol ORDER BY g.gene_symbol").fetchall(); b = [x[0] for x in b]
pk = int(t[t.notation == "C033"].taxon_key.iloc[0]); c = ((m.significance_key == pk).groupby(m.gene_symbol).mean() * 100).round(1).tolist(); add("What share of calls is pathogenic, per gene?", [("semantic layer", a), ("hand SQL (label)", b), ("pandas (by key of IRI C033)", c)])
# Q4: average daily backlog by month
a = sl.run(con, "avg_daily_backlog", by=["year", "month"]).avg_daily_backlog.tolist(); b = [r[3] for r in json.load(open(ROOT / "eval/olap_results.json"))["q14_semi_additive_backlog"]["rows"]]
pd_ = P("fact_pipeline_day").merge(d, on="date_key"); c = (pd_.groupby(["year", "month"]).queue_backlog.sum() / pd_.groupby(["year", "month"]).date_key.nunique()).round(1).tolist(); add("What is the average daily queue backlog per month?", [("semantic layer", a), ("OLAP file q14", b), ("pandas", c)])
# Negative example: why one definition matters
naive = sl.run(con, "pass_rate", by=["year", "month"]).pass_rate.mean(); right = float(sl.run(con, "pass_rate").pass_rate.iloc[0])
demo = dict(note='small here; grows when group sizes are unbalanced', naive_average_of_monthly_pass_rates=round(naive, 2), ratio_of_sums_pass_rate=right, difference_pp=round(naive - right, 2))
json.dump(dict(checks=out, naive_vs_correct=demo, validate_errors=sl.validate()), open(ROOT / "eval/semantic_consistency.json", "w"), indent=1)
for o in out: print("OK " if o["consistent"] else "BAD", o["question"], o["paths"])
print(demo, "metric definition errors:", sl.validate())
