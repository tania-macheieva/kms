"""Hybrid (rule chosen on DEV), citation check, cost model, error classification on TEST. Writes eval/*.json, eval/errors.csv, results/hybrid_*.jsonl"""
import sys, json, csv, collections, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from common import *
from evaluate import evaluate, prf

rd = lambda p: [json.loads(l) for l in open(ROOT / p, encoding="utf-8")]
gold = rd("data/gold.jsonl"); P = {p["id"]: p for p in load_passages()}
dev = {"rules": rd("results/rules_dev.jsonl"), "llm": rd("results/llm_dev_v2.jsonl")}
test = {"rules": rd("results/rules_test.jsonl"), "llm": rd("results/llm_test_v2.jsonl")}

# hybrid policy: per entity type / relation type pick the method with better DEV F1 (ties -> llm)
ed = {m: evaluate(gold, dev[m], "dev") for m in dev}
pol = {"entity": {}, "relation": {}}
for kind, types in (("entity", ENT_TYPES), ("relation", list(REL_TYPES))):
    for t in types:
        fa, fb = ed["rules"][kind]["by_type"][t]["F1"], ed["llm"][kind]["by_type"][t]["F1"]
        pol[kind][t] = "rules" if fa > fb else "llm"
def hybrid(rows_by_method):
    out = []
    for m, rows in rows_by_method.items():
        for r in rows:
            t = r["type"] if r["kind"] == "entity" else r["relation"]
            if pol[r["kind"]][t] == m: out.append(dict(r, method="hybrid:" + m))
    return out
for split, src in (("dev", dev), ("test", test)):
    h = hybrid(src)
    with open(ROOT / f"results/hybrid_{split}.jsonl", "w", encoding="utf-8") as f:
        for r in h: f.write(json.dumps(r, ensure_ascii=False) + "\n")
res = {m: evaluate(gold, test[m], "test") for m in test}
res["hybrid"] = evaluate(gold, rd("results/hybrid_test.jsonl"), "test")
res["dev"] = ed; res["dev"]["hybrid"] = evaluate(gold, rd("results/hybrid_dev.jsonl"), "dev"); res["policy"] = pol

# citation confirmation: evidence verbatim AND contains object (or subject) surface form
def confirmed(r):
    txt = P[r["passage_id"]]["text"]; ev = r["evidence"]
    return ev in txt and (norm(r["object"]) in norm(ev) or norm(r["subject"]) in norm(ev))
cit = {}
for m in test:
    rels = [r for r in test[m] if r["kind"] == "relation"]
    cit[m] = {"relations": len(rels), "evidence_not_verbatim": sum(r["evidence"] not in P[r["passage_id"]]["text"] for r in rels),
              "not_confirmed": sum(not confirmed(r) for r in rels)}
    cit[m]["share_not_confirmed"] = round(cit[m]["not_confirmed"] / max(len(rels), 1), 3)
st = json.load(open(ROOT / "results/llm_test_v2.stats.json"))
cit["llm"]["first_attempt_bad_evidence"] = sum(s["first_bad_evidence"] for s in st); cit["llm"]["retried_passages"] = sum(s["attempts"] > 1 for s in st)
res["citations"] = cit

# cost model (disclosed): tokens ~ chars/4; price assumption haiku-class $1 / $5 per MTok (NOT verified)
sysp = open(ROOT / "llm_log/prompts/extract_v2.txt").read()
tp = [p for p in P.values() if p["split"] == "test"]; docs = sorted({p["doc_id"] for p in tp})
tin = sum((len(sysp) + len(p["text"]) + 30) / 4 for p in tp)
tout = sum(len(json.dumps({"entities": [], "relations": []})) / 4 for p in tp) + sum(len(json.dumps(r)) / 4 for r in test["llm"])
usd = tin / 1e6 * 1.0 + tout / 1e6 * 5.0
rt = json.load(open(ROOT / "results/rules_test.time.json"))
res["cost"] = {"test_passages": len(tp), "test_docs": len(docs), "llm_in_tokens": round(tin), "llm_out_tokens": round(tout), "llm_usd_total_modelled": round(usd, 4),
               "llm_usd_per_passage": round(usd / len(tp), 5), "llm_usd_per_document": round(usd / len(docs), 4),
               "rules_cpu_s_total": rt["cpu_seconds"], "rules_cpu_s_per_document": round(rt["cpu_seconds"] / len(docs), 2), "rules_usd": 0.0,
               "assumption": "tokens=chars/4; $1/$5 per MTok haiku-class (unverified); no retries occurred; prompt caching ignored"}

# error classification (automatic categories) on TEST for the hybrid and for both methods
def classify(method, rows):
    G = {(g["passage_id"], norm(g["subject"]), g["relation"], norm(g["object"])): g for g in gold if g["kind"] == "relation" and g["split"] == "test"}
    out = []
    pr = {(r["passage_id"], norm(r["subject"]), r["relation"], norm(r["object"])): r for r in rows if r["kind"] == "relation"}
    for k, r in pr.items():
        if k in G: continue
        pid, s, rel, o = k
        if (pid, o, rel, s) in G: cat = "wrong direction"
        elif any(g[0] == pid and g[1] == s and g[3] == o for g in G): cat = "wrong relation type"
        elif any(g[0] == pid and g[2] == rel and g[3] == o for g in G): cat = "wrong subject"
        elif not confirmed(r): cat = "fabricated (evidence does not support)"
        else: cat = "extra statement (not in gold)"
        out.append((method, "FP", cat, pid, r["subject"], rel, r["object"], r["evidence"][:90].replace("\n", " ")))
    for k, g in G.items():
        if k not in pr:
            cat = "missed (no candidate)" if not any(x[0] == k[0] and x[3] == k[3] for x in pr) else "missed (matched by other subject)"
            out.append((method, "FN", cat, k[0], g["subject"], g["relation"], g["object"], g["evidence"][:90].replace("\n", " ")))
    return out
errs = classify("rules", test["rules"]) + classify("llm", test["llm"])
with open(ROOT / "eval/errors.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["method", "type", "category", "passage_id", "subject", "relation", "object", "evidence"]); w.writerows(errs)
res["error_categories"] = {m: dict(collections.Counter((e[1] + ": " + e[2]) for e in errs if e[0] == m)) for m in ("rules", "llm")}
json.dump(res, open(ROOT / "eval/test_summary.json", "w"), indent=1)
for m in ("rules", "llm", "hybrid"):
    print(m, res[m]["entity"]["overall"], res[m]["relation"]["overall"])
print("dev hybrid", res["dev"]["hybrid"]["entity"]["overall"]["F1"], res["dev"]["hybrid"]["relation"]["overall"]["F1"])
print(pol); print(cit); print(res["cost"]); print(res["error_categories"])
