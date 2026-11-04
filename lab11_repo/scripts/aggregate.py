"""Aggregate metrics for a config: python3 scripts/aggregate.py A  -> eval/metrics_A.json (+ prints kappa for manual checks)."""
import json, sys, statistics as st
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]

def pct(xs, p):
    xs = sorted(xs); k = (len(xs) - 1) * p; f = int(k); c = min(f + 1, len(xs) - 1); return xs[f] + (xs[c] - xs[f]) * (k - f)

def kappa(a, b):
    labs = sorted(set(a) | set(b)); n = len(a); po = sum(x == y for x, y in zip(a, b)) / n
    pe = sum((a.count(l) / n) * (b.count(l) / n) for l in labs)
    return po, (1.0 if pe == 1 else (po - pe) / (1 - pe))

def main(cfg):
    res = {x["id"]: x for x in json.load(open(ROOT / f"eval/results_{cfg}.json"))}
    jd = {x["id"].split(":")[1]: x for x in json.load(open(ROOT / f"llm_log/raw/judge_{cfg}_out.json"))}
    M = {}
    claims = [c for j in jd.values() for c in j["claims"]]
    M["claims_total"] = len(claims); M["claims_supported"] = sum(c["verdict"] == "supported" for c in claims)
    M["faithfulness_claims"] = M["claims_supported"] / len(claims)
    per = [sum(c["verdict"] == "supported" for c in j["claims"]) / len(j["claims"]) for j in jd.values() if j["claims"]]
    M["faithfulness_answer_mean"] = st.mean(per); M["answers_fully_faithful"] = sum(p == 1 for p in per); M["answers_judged"] = len(per)
    rec = [x["context_recall"] for x in res.values() if x["context_recall"] is not None]
    M["context_recall"] = st.mean(rec); M["context_recall_n"] = len(rec); M["context_recall_full"] = sum(r == 1 for r in rec)
    cit = [c["citation_ok"] for c in claims if c.get("citation_ok") is not None]
    M["citation_support"] = sum(cit) / len(cit); M["citation_judged_n"] = len(cit)
    tot = sum(x["n_cited"] + x["n_invalid"] for x in res.values()); M["citation_validity"] = 1 - sum(x["n_invalid"] for x in res.values()) / tot if tot else None
    M["citations_total"] = tot; M["uncited_sentences"] = sum(x["uncited"] for x in res.values())
    na = [x for x in res.values() if x["expected"] == "NO_ANSWER"]; an = [x for x in res.values() if x["expected"] == "ANSWER" and x["category"] == "answerable"]
    M["abstention_correct"] = sum(x["abstained"] for x in na) / len(na); M["abstention_n"] = len(na)
    M["false_abstention"] = sum(x["abstained"] for x in an) / len(an); M["answerable_n"] = len(an)
    cf = [x for x in res.values() if x["category"] == "conflict"]; M["conflict_detected"] = sum(x["status"] == "CONFLICT" for x in cf) / len(cf); M["conflict_n"] = len(cf)
    inj = [x for x in res.values() if x["category"] == "injection"]; M["injection_resisted"] = sum(x["injection_resisted"] for x in inj) / len(inj); M["injection_n"] = len(inj)
    M["status_ok"] = sum(x["status_ok"] for x in res.values()); M["n"] = len(res)
    for nm, key in (("retrieve_ms", "retrieve_ms"), ("graph_ms", "graph_ms")):
        v = [x[key] for x in res.values() if x[key] is not None]; M[nm] = dict(p50=pct(v, .5), p95=pct(v, .95), mean=st.mean(v))
    M["in_tokens_mean"] = st.mean(x["in_tokens"] for x in res.values()); M["out_tokens_mean"] = st.mean(x["out_tokens"] for x in res.values())
    M["in_tokens_total"] = sum(x["in_tokens"] for x in res.values()); M["out_tokens_total"] = sum(x["out_tokens"] for x in res.values())
    # manual checks vs judge
    mc = json.load(open(ROOT / "eval/manual_checks.json")); a, b = [], []
    if cfg != "A": mc["checked"] = []   # manual checks were done on the A run only
    for t in mc["checked"]:
        if t not in jd: continue
        for i, c in enumerate(jd[t]["claims"]):
            a.append(c["verdict"]); b.append(mc["overrides"].get(f"{t}:{i}", c["verdict"]))
    # modelled LLM latency/cost (ASSUMPTIONS, not measurements): t = 0.4 s + 0.05 ms/input token + 8 ms/output token; price $1/MTok in, $5/MTok out
    llm = [0.4 + x["in_tokens"] * 5e-5 + x["out_tokens"] * 8e-3 for x in res.values()]; tot_s = [l + (x["retrieve_ms"] + (x["graph_ms"] or 0)) / 1000 for l, x in zip(llm, res.values())]
    M["e2e_s_modelled"] = dict(p50=pct(tot_s, .5), p95=pct(tot_s, .95)); M["cost_usd_total_modelled"] = M["in_tokens_total"] * 1e-6 + M["out_tokens_total"] * 5e-6; M["cost_usd_per_query_modelled"] = M["cost_usd_total_modelled"] / len(res)
    if not a: M["manual"] = None; json.dump(M, open(ROOT / f"eval/metrics_{cfg}.json", "w"), indent=1); print(json.dumps(M, indent=1)); return
    po, k = kappa(a, b); M["manual"] = dict(answers=len(mc["checked"]), claims=len(a), agreement=po, kappa=k, judge_unsupported=a.count("unsupported"), human_unsupported=b.count("unsupported"))
    json.dump(M, open(ROOT / f"eval/metrics_{cfg}.json", "w"), indent=1)
    print(json.dumps(M, indent=1))
if __name__ == "__main__": main(sys.argv[1])
