"""Offline evaluation with a temporal split (R2). python -m reco.eval --seeds 0 1 2 3 4 --out eval/results.json
Split (documented in docs/reco_eval.md): events with day < CUTOFF are TRAIN, day >= CUTOFF are TEST. Positives of a user = items read in TEST that the user did not read in TRAIN.
Anything fitted on data (popularity counts, tuned weights, user histories) uses TRAIN only; tuning uses an inner split of TRAIN (history < VAL_CUT, positives in [VAL_CUT, CUTOFF)); content (text, embeddings, entity graph) has no timestamp later than the cut."""
from __future__ import annotations
import argparse, json, math, itertools, collections, pathlib, time
import numpy as np
from .data import load_items, load_embeddings, eligible, ROOT
from .entities import build_entities
from .graphdb import ItemGraph
from .synth import generate, DAYS
from .models import Popularity, GraphReco, KNNReco, Hybrid, recommend
CUTOFF, VAL_CUT = 63, 49
def split(rows, items, lo, hi):
    """history = events with day < lo ; positives = new items in [lo, hi)"""
    idx = {it["id"]: i for i, it in enumerate(items)}; hist = collections.defaultdict(list); roles = {}; seen = collections.defaultdict(set); pos = collections.defaultdict(set)
    for u, role, it, day, _ in rows:
        roles[u] = role
        if day < lo: hist[u].append((idx[it], day)); seen[u].add(idx[it])
    for u, role, it, day, _ in rows:
        if lo <= day < hi and idx[it] not in seen[u]: pos[u].add(idx[it])
    users = [u for u in sorted(hist) if pos.get(u)]; return users, hist, roles, seen, pos
def metrics_for(recs, pos, users, pop, n_cat):
    """recs: user -> ranked list (>=10). -> per-user arrays + coverage/novelty helpers"""
    P, R, N, nov = [], [], [], []
    for u in users:
        r = recs[u]; p = pos[u]; hit5 = sum(1 for i in r[:5] if i in p); P.append(hit5 / 5); R.append(hit5 / len(p))
        dcg = sum(1 / math.log2(k + 2) for k, i in enumerate(r[:10]) if i in p); idcg = sum(1 / math.log2(k + 2) for k in range(min(len(p), 10))); N.append(dcg / idcg)
        nov.append(np.mean([-math.log2(pop.pop_share(i)) for i in r[:5]]))
    return dict(p5=np.array(P), r5=np.array(R), ndcg10=np.array(N), novelty=np.array(nov))
def coverage(recs, users, n_cat): return len({i for u in users for i in recs[u][:5]}) / n_cat
def make_recs(model, items, users, hist, roles, seen, now, verified_only=True):
    return {u: recommend(model, items, roles[u], hist[u], now, seen[u], k=10, verified_only=verified_only) for u in users}
class World:
    def __init__(self, seed, n_users=64):
        self.items = load_items(); self.E = load_embeddings(self.items); self.ent_of, self.idf, self.types = build_entities(self.items); self.G = ItemGraph(self.items, self.ent_of, self.idf, self.types)
        self.rows, self.profiles = generate(self.items, n_users=n_users, seed=seed); self.seed = seed
        self.n_cat = len({i for r in {"reader", "analyst", "clinician"} for i in eligible(self.items, r)})
    def close(self): self.G.close()
def fit_and_eval(W, lo, hi, params, users=None):
    """fit models on events with day < lo, evaluate on positives in [lo, hi)"""
    items = W.items; us, hist, roles, seen, pos = split(W.rows, items, lo, hi); users = users or us; train = [r for r in W.rows if r[3] < lo]
    pop = Popularity(items, train); G = GraphReco(W.G, items, **params["graph"]); K = KNNReco(W.E, items, **params["knn"]); models = {"popularity": pop, "graph": G, "knn": K}
    models["hybrid-weighted"] = Hybrid(models, params["hyb_w"], "weighted"); models["hybrid-rrf"] = Hybrid(models, params["hyb_rrf"], "rrf")
    out = {}
    for name, m in models.items():
        recs = make_recs(m, items, users, hist, roles, seen, lo); out[name] = dict(per_user=metrics_for(recs, pos, users, pop, W.n_cat), coverage=coverage(recs, users, W.n_cat), recs=recs)
    return out, users, pos, pop
def tune(W):
    """grid search on the inner validation split (history < VAL_CUT, positives in [VAL_CUT, CUTOFF)); objective: nDCG@10"""
    best = {}; items = W.items
    def score(params, which):
        out, *_ = fit_and_eval(W, VAL_CUT, CUTOFF, params); return float(out[which]["per_user"]["ndcg10"].mean())
    base = dict(graph=dict(ent_w=1.0, next_w=3.0, doc_w=0.5, half_life=14.0), knn=dict(m=3, half_life=14.0), hyb_w=dict(graph=1, knn=1, popularity=0.2), hyb_rrf=dict(graph=1, knn=1, popularity=0.3))
    g_best = (-1, None)
    for nw, dw, hl in itertools.product([1.0, 3.0, 6.0], [0.0, 0.5], [7.0, 14.0, 28.0]):
        p = json.loads(json.dumps(base)); p["graph"].update(next_w=nw, doc_w=dw, half_life=hl); s = score(p, "graph")
        if s > g_best[0]: g_best = (s, p["graph"])
    k_best = (-1, None)
    for m, hl in itertools.product([1, 3, 5], [7.0, 14.0, 28.0]):
        p = json.loads(json.dumps(base)); p["knn"].update(m=m, half_life=hl); s = score(p, "knn")
        if s > k_best[0]: k_best = (s, p["knn"])
    base["graph"], base["knn"] = g_best[1], k_best[1]; hw = (-1, None); hr = (-1, None)
    for wg, wk, wp in itertools.product([0.0, 0.5, 1.0, 2.0], [0.0, 0.5, 1.0, 2.0], [0.0, 0.1, 0.3]):
        if wg == wk == 0: continue
        p = json.loads(json.dumps(base)); p["hyb_w"] = dict(graph=wg, knn=wk, popularity=wp); p["hyb_rrf"] = dict(graph=wg, knn=wk, popularity=wp)
        out, *_ = fit_and_eval(W, VAL_CUT, CUTOFF, p); a, b = float(out["hybrid-weighted"]["per_user"]["ndcg10"].mean()), float(out["hybrid-rrf"]["per_user"]["ndcg10"].mean())
        if a > hw[0]: hw = (a, p["hyb_w"])
        if b > hr[0]: hr = (b, p["hyb_rrf"])
    base["hyb_w"], base["hyb_rrf"] = hw[1], hr[1]; base["val_ndcg10"] = dict(graph=g_best[0], knn=k_best[0], hybrid_weighted=hw[0], hybrid_rrf=hr[0]); return base
def bootstrap(per_user, recs, users, n_cat, B=1000, seed=0):
    rng = np.random.default_rng(seed); n = len(users); res = collections.defaultdict(list)
    for _ in range(B):
        ix = rng.integers(0, n, n)
        for k in ("p5", "r5", "ndcg10", "novelty"): res[k].append(per_user[k][ix].mean())
        res["coverage"].append(len({i for j in ix for i in recs[users[j]][:5]}) / n_cat)
    return {k: (float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))) for k, v in res.items()}
def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--seeds", type=int, nargs="+", default=[0, 1, 2, 3, 4]); ap.add_argument("--out", default=str(ROOT / "eval/results.json")); a = ap.parse_args(); allr = {}
    for seed in a.seeds:
        t = time.time(); W = World(seed); params = tune(W); out, users, pos, pop = fit_and_eval(W, CUTOFF, DAYS, params); res = dict(params=params, n_users=len(users), n_positives=int(sum(len(pos[u]) for u in users)), n_events=len(W.rows), n_train=sum(r[3] < CUTOFF for r in W.rows), n_test=sum(r[3] >= CUTOFF for r in W.rows), configs={})
        for name, o in out.items():
            pu = o["per_user"]; ci = bootstrap(pu, o["recs"], users, W.n_cat, seed=seed)
            res["configs"][name] = dict(**{k: float(pu[k].mean()) for k in pu}, coverage=o["coverage"], ci=ci, per_user={k: pu[k].tolist() for k in pu}, recs={u: [W.items[i]["id"] for i in r[:10]] for u, r in o["recs"].items()} if seed == 0 else None)
        res["users"] = users; allr[str(seed)] = res; print(f"seed {seed}: {len(users)} users, {res['n_positives']} positives, {time.time()-t:.0f}s", {k: round(v["ndcg10"], 3) for k, v in res["configs"].items()}, flush=True); W.close()
    json.dump(allr, open(a.out, "w")); print("saved", a.out)
if __name__ == "__main__": main()
