"""Metrics for R3 C2: python scripts/eval_metrics.py eval/v0.json eval/v1.json eval/v2.json -> eval/metrics.json"""
import sys, json, statistics as st, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
def metrics(res):
    ok = [r for r in res if r.get("judge") and r["judge"]["ok"]]; by = {}
    for t in ("success", "unknown", "conflict"):
        rs = [r for r in res if r["scenario"]["type"] == t]; by[t] = dict(n=len(rs), ok=sum(r["judge"]["ok"] for r in rs))
    return dict(n=len(res), success_share=round(len(ok) / len(res), 3), by_type=by, mean_steps=round(st.mean(r["steps"] for r in res), 2), mean_tool_calls=round(st.mean(len(r["tool_calls"]) for r in res), 2),
                redrafts=sum(r["redrafts"] for r in res), mean_tokens=round(st.mean(r["tokens_in"] + r["tokens_out"] for r in res)), mean_cost_usd=round(st.mean(r["cost_usd"] for r in res), 5), total_cost_usd=round(sum(r["cost_usd"] for r in res), 4),
                failed=[r["qid"] for r in res if not r["judge"]["ok"]])
if __name__ == "__main__":
    out = {}
    for f in sys.argv[1:]: out[pathlib.Path(f).stem] = metrics(json.load(open(f, encoding="utf-8")))
    json.dump(out, open(ROOT / "eval/metrics.json", "w"), indent=1); print(json.dumps(out, indent=1))
