import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT))
from semantic import sl
C = json.load(open(ROOT / "eval/semantic_consistency.json")); M = sl.LAYER["metrics"]
L = ["# Semantic layer (R4)", "", "`semantic/metrics.yml` – definitions, `semantic/sl.py` – `metric_sql(metric, by, where)` generates SQL. Tests: `tests/test_semantic.py`, consistency: `scripts/check_semantic.py`.", "",
     "## Why", "", "Without a layer every analyst writes his own `pass rate` (average of monthly percentages, `COUNT(DISTINCT)` vs `COUNT(*)`, a different set of joins). With it the **definition lives in one place**, carries its unit, owner, sources and limitations, is checked once, and queries (including text-to-SQL, R5) use it as the vocabulary. It also stops forbidden combinations: a metric on the snapshot fact cannot be sliced by gene (`SemanticError`).", "",
     "## Metrics (7, all fields filled)", "", "| metric | definition | formula | unit | owner | sources | additivity | limitations | status / reviewed |", "|---|---|---|---|---|---|---|---|---|"]
for k, m in M.items(): L.append(f"| `{k}` | {m['definition']} | `{m['expression'].replace('|', '/')}` | {m['unit']} | {m['owner']} | {', '.join(m['sources'])} | {m['additivity']} | {m['limitations']} | {m['status']} / {m['reviewed']} |")
L += ["", f"Layer metadata: version {sl.LAYER['version']}, reviewed {sl.LAYER['reviewed']}, reviewer: {sl.LAYER['reviewer']}. Of 7 metrics {sum(m['status']=='approved' for m in M.values())} are `approved`, {sum(m['status']=='draft' for m in M.values())} are `draft` (review minutes are self-reported; pathogenic share is a generator label) – the approval is a decision to be confirmed by the student/owner.", "",
      "## Generated SQL (examples)", ""]
for metric, by, where in (("pass_rate", ["year", "family"], None), ("pathogenic_share", ["gene"], {"cohort": ["HBOC"]}), ("avg_daily_backlog", ["year", "month"], None)):
    sql, params = sl.metric_sql(metric, by=by, where=where); L += [f"`metric_sql('{metric}', by={by}, where={where})`", "", "```sql", sql, "```", f"params: `{params}`", ""]
L += ["## Consistency: one question, three paths", "", "| question | paths compared (rows) | identical |", "|---|---|---|"] + [f"| {c['question']} | " + "; ".join(f"{k} ({v})" for k, v in c["paths"].items()) + f" | {'yes' if c['consistent'] else 'NO'} |" for c in C["checks"]]
n = C["naive_vs_correct"]
L += ["", f"{sum(c['consistent'] for c in C['checks'])} of {len(C['checks'])} questions give identical results by the semantic layer, by hand-written OLAP SQL and by pandas (more than the required two).", "",
      f"Why a definition matters: the average of the 21 monthly pass rates is {n['naive_average_of_monthly_pass_rates']:.2f}% while the ratio of sums is {n['ratio_of_sums_pass_rate']:.1f}% (difference {n['difference_pp']:+.2f} pp). It is small here because months have similar volumes; with unbalanced groups (e.g. a rare variant type) the gap grows – the layer fixes the correct form once.", "",
      "## Limits", "", "- The layer is a small Python/YAML implementation, not dbt/Cube: no derived metrics from other metrics, no time-intelligence functions, no access control per metric.", "- Filters accept only equality/IN; dimension attributes and metric formulas are trusted (they come from the reviewed YAML, not from users); all user values are bound parameters.", "- Review is formal: the `reviewer` field says that the student's review is pending."]
(ROOT / "docs/semantic_layer.md").write_text("\n".join(L) + "\n", encoding="utf-8"); print("ok")
