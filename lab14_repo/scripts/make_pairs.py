"""Build the labelling set: 150 candidate pairs stratified by combined-score band + 10 blocking-recall probes
(high embedding similarity but NOT produced by blocking). Seeds fixed. Writes data/pairs_candidates.json and llm_log/in/pairs_batch_*.json (blind: no scores shown)."""
import sys, json, random, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from quality import dedup as D
from quality.common import ROOT
random.seed(14)
S = D.Store(); P = D.blocking(S); Pset = set(P)
rows = [(a, b, D.score(D.features(S, a, b))) for a, b in P]
bands = [(.98, 9), (.90, .98), (.80, .90), (.70, .80), (.60, .70), (.50, .60), (0, .50)]
quota = {0: 15, 1: 15, 2: 20, 3: 25, 4: 25, 5: 25, 6: 25}   # = 150
sel = []
for i, (lo, hi) in enumerate(bands):
    pool = [r for r in rows if lo <= r[2] < hi]; random.shuffle(pool); sel += [(r, f"band{i}") for r in pool[:quota[i]]]
# top up to 150 from the neighbouring bands if a band is short
chosen = {(r[0], r[1]) for r, _ in sel}
rest = [r for r in rows if (r[0], r[1]) not in chosen]; random.shuffle(rest)
while len(sel) < 150: sel.append((rest.pop(), "topup"))
# blocking-recall probes: highest embedding cosine among non-candidate pairs, one per doc pair family
E = S.E; sim = E @ E.T; n = len(S.c); probes = []
for a in range(n):
    for b in range(a + 1, n):
        if (a, b) not in Pset: probes.append((float(sim[a, b]), a, b))
probes.sort(reverse=True); pr = []
for s, a, b in probes:
    if len(pr) >= 10: break
    pr.append(((a, b, D.score(D.features(S, a, b))), "probe"))
allp = sel + pr; random.shuffle(allp); out = []
for k, ((a, b, s), tag) in enumerate(allp, 1):
    if random.random() < .5: a, b = b, a
    f = D.features(S, a, b)
    out.append(dict(pair_id=f"PR{k:03d}", a=S.c[a]["chunk_id"], b=S.c[b]["chunk_id"], score=round(s, 4), band=tag, probe=(tag == "probe"), **{k2: (round(v, 4) if isinstance(v, float) else v) for k2, v in f.items()}))
json.dump(out, open(ROOT / "data/pairs_candidates.json", "w"), indent=1)
by = {c["chunk_id"]: c for c in S.c}
for part in range(4):
    chunk = out[part * 40:(part + 1) * 40]
    items = [dict(pair_id=p["pair_id"], A=dict(id=p["a"], doc=by[p["a"]]["doc_id"], section=by[p["a"]]["section"], text=by[p["a"]]["text"]),
                  B=dict(id=p["b"], doc=by[p["b"]]["doc_id"], section=by[p["b"]]["section"], text=by[p["b"]]["text"])) for p in chunk]
    json.dump(items, open(ROOT / f"llm_log/in/pairs_batch_{part+1}.json", "w"), ensure_ascii=False, indent=0)
print(len(out), "pairs;", sum(p["probe"] for p in out), "probes; bands", {b: sum(p["band"] == b for p in out) for b in sorted({p['band'] for p in out})})
