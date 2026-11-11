"""Aggregate before/after metrics for the 34 tests with the lab-11 formulas; judge verdicts: lab-11 judge output (baseline answers) +
llm_log/raw/judge_after_out.json for the answers that changed. Writes eval/metrics_before.json, eval/metrics_after.json, eval/rag_comparison.json."""
import json, statistics as st, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
def pct(xs, p):
    xs = sorted(xs); k = (len(xs) - 1) * p; f = int(k); c = min(f + 1, len(xs) - 1); return xs[f] + (xs[c] - xs[f]) * (k - f)
base_j = {x["id"].split(":")[1]: x for x in json.load(open(ROOT / "baseline/judge_A_out.json"))} if (ROOT / "baseline/judge_A_out.json").exists() else {}
new_j = {x["id"].split(":")[1]: x for x in json.load(open(ROOT / "llm_log/raw/judge_after_out.json"))}
def metrics(res, jd):
    res = {x["id"]: x for x in res}; M = {}; claims = [c for j in jd.values() for c in j["claims"]]
    M["claims_total"] = len(claims); M["claims_supported"] = sum(c["verdict"] == "supported" for c in claims); M["faithfulness_claims"] = M["claims_supported"] / len(claims)
    per = [sum(c["verdict"] == "supported" for c in j["claims"]) / len(j["claims"]) for j in jd.values() if j["claims"]]; M["answers_fully_faithful"] = f"{sum(p == 1 for p in per)}/{len(per)}"
    rec = [x["context_recall"] for x in res.values() if x["context_recall"] is not None]; M["context_recall"] = st.mean(rec); M["context_recall_full"] = f"{sum(r == 1 for r in rec)}/{len(rec)}"
    cit = [c["citation_ok"] for c in claims if c.get("citation_ok") is not None]; M["citation_support"] = sum(cit) / len(cit)
    tot = sum(x["n_cited"] + x["n_invalid"] for x in res.values()); M["citation_validity"] = 1 - sum(x["n_invalid"] for x in res.values()) / tot
    na = [x for x in res.values() if x["expected"] == "NO_ANSWER"]; an = [x for x in res.values() if x["expected"] == "ANSWER" and x["category"] == "answerable"]
    M["abstention_correct"] = sum(x["abstained"] for x in na) / len(na); M["false_abstention"] = sum(x["abstained"] for x in an) / len(an)
    cf = [x for x in res.values() if x["category"] == "conflict"]; M["conflict_detected"] = sum(x["status"] == "CONFLICT" for x in cf) / len(cf)
    inj = [x for x in res.values() if x["category"] == "injection"]; M["injection_resisted"] = sum(x["injection_resisted"] for x in inj) / len(inj)
    M["status_ok"] = sum(x["status_ok"] for x in res.values()); M["n"] = len(res)
    v = [x["latency"]["retrieve_ms"] for x in res.values()]; M["retrieve_ms_p50"] = pct(v, .5); M["retrieve_ms_p95"] = pct(v, .95)
    M["in_tokens_mean"] = st.mean(x["in_tokens"] for x in res.values()); return M
before = json.load(open(ROOT / "eval/results_before.json")); after = json.load(open(ROOT / "eval/results_after.json"))
jb = base_j; ja = {k: (new_j[k] if k in new_j else v) for k, v in base_j.items()}
Mb, Ma = metrics(before, jb), metrics(after, ja); json.dump(Mb, open(ROOT / "eval/metrics_before.json", "w"), indent=1); json.dump(Ma, open(ROOT / "eval/metrics_after.json", "w"), indent=1)
ch = [b["id"] for b, a in zip(before, after) if b["answer"] != a["answer"] or b["context_ids"] != a["context_ids"]]
cmp = dict(before=Mb, after=Ma, changed_tests=ch, status_changes=[(b["id"], b["status"], a["status"]) for b, a in zip(before, after) if b["status"] != a["status"]], unchanged_answers=34 - len([1 for b, a in zip(before, after) if b["answer"] != a["answer"]]))
json.dump(cmp, open(ROOT / "eval/rag_comparison.json", "w"), indent=1); print(json.dumps(dict(before=Mb, after=Ma, changed=ch), indent=1))
