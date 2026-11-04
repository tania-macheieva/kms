"""Strict evaluation: entity = (passage, norm text, type); relation = (passage, norm subj, rel, norm obj).
Usage: python src/evaluate.py --pred results/rules_dev.jsonl --split dev [--json out.json]"""
import argparse, json, collections, sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from common import *

def prf(tp, fp, fn):
    p = tp / (tp + fp) if tp + fp else 0.0; r = tp / (tp + fn) if tp + fn else 0.0
    return {"tp": tp, "fp": fp, "fn": fn, "P": round(p, 3), "R": round(r, 3), "F1": round(2 * p * r / (p + r), 3) if p + r else 0.0}

def keys(rows, kind):
    out = {}
    for r in rows:
        if r["kind"] != kind: continue
        if kind == "entity": out[(r["passage_id"], norm(r["text"]), r["type"])] = r
        else: out[(r["passage_id"], norm(r["subject"]), r["relation"], norm(r["object"]))] = r
    return out

def evaluate(gold, pred, split):
    gold = [g for g in gold if split in ("all", g["split"])]
    pids = {g["passage_id"] for g in gold}
    pred = [r for r in pred if r["passage_id"] in pids]
    res = {}
    for kind, tkey in (("entity", 2), ("relation", 2)):
        G, P = keys(gold, kind), keys(pred, kind)
        res[kind] = {"overall": prf(len(G.keys() & P.keys()), len(P.keys() - G.keys()), len(G.keys() - P.keys())), "by_type": {}}
        types = ENT_TYPES if kind == "entity" else list(REL_TYPES)
        for t in types:
            idx = -1 if kind == "entity" else 2 - 1
            gk = {k for k in G if (k[2] == t if kind == "entity" else k[2] == t)}
            pk = {k for k in P if (k[2] == t if kind == "entity" else k[2] == t)}
            res[kind]["by_type"][t] = prf(len(gk & pk), len(pk - gk), len(gk - pk))
    # lenient relations: ignore subject (object + relation + passage)
    G = {(k[0], k[2], k[3]) for k in keys(gold, "relation")}; P = {(k[0], k[2], k[3]) for k in keys(pred, "relation")}
    res["relation_lenient_subject_ignored"] = prf(len(G & P), len(P - G), len(G - P))
    return res

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--pred", required=True); ap.add_argument("--split", default="dev"); ap.add_argument("--json")
    a = ap.parse_args()
    gold = [json.loads(l) for l in open(ROOT / "data/gold.jsonl", encoding="utf-8")]
    pred = [json.loads(l) for l in open(a.pred, encoding="utf-8")]
    r = evaluate(gold, pred, a.split)
    if a.json: json.dump(r, open(a.json, "w"), indent=1)
    for k in ("entity", "relation"):
        print(k, r[k]["overall"])
        for t, v in r[k]["by_type"].items(): print("  ", t, v)
    print("lenient", r["relation_lenient_subject_ignored"])
