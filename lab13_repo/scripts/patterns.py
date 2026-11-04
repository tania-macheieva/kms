"""R5: association rules over chunk-level entity sets (method A entities, whole external corpus, 24 docs), with chance/stability checks.
Seed 13. Outputs eval/patterns.json."""
import sys, json, csv, itertools, collections, pathlib, random
import numpy as np
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from common import *
from extract_rules import find_entities
rng = np.random.default_rng(13)
aliases = {norm(r["alias"]): r["canonical"] for r in csv.DictReader(open(ROOT / "data/aliases.csv"))}
chunks = [json.loads(l) for l in open(ROOT / "data/corpus_lab10.jsonl", encoding="utf-8")]
chunks = [c for c in chunks if not c["doc_id"].startswith("int_")]
KEEP = {"Tool", "FileFormat", "Metric", "Resource", "Procedure"}
items, docs = [], []
for c in chunks:
    s = set()
    for st, en, t, ty in find_entities(c["text"], c["doc_id"]):
        if ty in KEEP:
            n = norm(t); s.add(f"{norm(aliases.get(n, n))}|{ty}")
    items.append(s); docs.append(c["doc_id"])
N = len(items); D = sorted(set(docs)); didx = np.array([D.index(d) for d in docs])
vocab = sorted({i for s in items for i in s}); V = {v: k for k, v in enumerate(vocab)}
X = np.zeros((N, len(vocab)), dtype=bool)
for r, s in enumerate(items):
    for i in s: X[r, V[i]] = True
MINSUP = 12 / N
sup1 = X.mean(0); frequent = [k for k in range(len(vocab)) if sup1[k] >= MINSUP]
def rules_from(Xm, minsup, minconf, minlift):
    n = len(Xm); out = []; s1 = Xm.mean(0)
    for a in range(Xm.shape[1]):
        if s1[a] < minsup: continue
        for b in range(Xm.shape[1]):
            if a == b or s1[b] < minsup: continue
            both = (Xm[:, a] & Xm[:, b]).sum() / n
            if both < minsup: continue
            conf = both / s1[a]; lift = conf / s1[b]
            if conf >= minconf and lift >= minlift: out.append((a, b, both, conf, lift))
    return out
cand = rules_from(X, MINSUP, 0.6, 1.5)
# 2-item antecedents are not mined: single-antecedent rules only (documented limitation)
def stats(Xm, a, b):
    n = len(Xm); both = (Xm[:, a] & Xm[:, b]).sum(); sa = Xm[:, a].sum(); sb = Xm[:, b].sum()
    return (both / n, both / sa if sa else 0, (both / sa) / (sb / n) if sa and sb else 0)
def perm_p(a, b, B=2000):
    """Null: shuffle the consequent column WITHIN documents (keeps each document's base rate) -> p(lift >= observed)."""
    obs = stats(X, a, b)[2]; cnt = 0; col = X[:, b].copy()
    groups = [np.where(didx == d)[0] for d in range(len(D))]
    for _ in range(B):
        sh = col.copy()
        for g in groups: sh[g] = col[rng.permutation(g)]
        Xs = X.copy(); Xs[:, b] = sh
        if stats(Xs, a, b)[2] >= obs: cnt += 1
    return (cnt + 1) / (B + 1)
def boot(a, b, B=300):
    ok = 0; lifts = []
    for _ in range(B):
        sel = rng.choice(len(D), len(D), replace=True); idx = np.concatenate([np.where(didx == d)[0] for d in sel])
        s, c, l = stats(X[idx], a, b); lifts.append(l)
        ok += (l >= 1.5 and c >= 0.6)
    return ok / B, float(np.percentile(lifts, 5)), float(np.percentile(lifts, 95))
half = {h: np.isin(didx, [i for i in range(len(D)) if i % 2 == h]) for h in (0, 1)}
res = []
for a, b, s, c, l in sorted(cand, key=lambda t: -t[4] * t[2]):
    ndocs = len(set(didx[X[:, a] & X[:, b]]))
    res.append({"antecedent": vocab[a], "consequent": vocab[b], "support": round(s, 4), "n_chunks": int(round(s * N)), "confidence": round(c, 3), "lift": round(l, 2), "n_docs": ndocs, "_a": a, "_b": b})
res = res[:40]
for r in res:
    a, b = r.pop("_a"), r.pop("_b")
    r["perm_p_within_docs"] = round(perm_p(a, b), 4)
    r["boot_stable_share"], r["boot_lift_p5"], r["boot_lift_p95"] = boot(a, b)
    r["half_lift"] = [round(stats(X[half[h]], a, b)[2], 2) for h in (0, 1)]
out = {"chunks": N, "docs": len(D), "vocab": len(vocab), "frequent_items": len(frequent), "min_support_chunks": 12, "min_conf": 0.6, "min_lift": 1.5, "n_candidate_rules": len(cand), "rules_top40": res}
json.dump(out, open(ROOT / "eval/patterns.json", "w"), indent=1, ensure_ascii=False)
print(N, len(D), len(vocab), len(frequent), len(cand))
for r in res[:25]: print(r)
