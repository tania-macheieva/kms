"""Cold start (R3): (A) a NEW USER (no history; role + topics declared at onboarding), (B) a NEW DOCUMENT/section (no interactions; inserted into the graph with add_item, scored by content).
python -m reco.cold --seeds 0 1 2 3 4 --out eval/cold.json"""
from __future__ import annotations
import argparse, json, collections, math, random
import numpy as np
from .data import load_items, load_embeddings, eligible, ROOT
from .entities import build_entities
from .graphdb import ItemGraph
from .synth import generate, DAYS, TOPICS, topic_of
from .models import Popularity, GraphReco, KNNReco, Hybrid, recommend
from .eval import CUTOFF, split, metrics_for, coverage
class TopicPop:
    """new user with n=0 history: popularity restricted to the topics declared at onboarding (round-robin over topics)"""
    name = "topic-popularity"
    def __init__(self, items, pop, topics): self.items, self.pop, self.topics = items, pop, topics
    def scores(self, cands, hist=None, now=None, **kw):
        s = self.pop.scores(cands); ok = np.array([topic_of(self.items[i]["doc"]) in self.topics for i in cands]); return np.where(ok, s + 1e6, s)
def new_user_experiment(W, ks=(0, 1, 3)):
    """Every user with test positives is treated as NEW: train history is discarded; the first k test events are given as history; declared topics = top-2 latent topics (onboarding form)."""
    items = W.items; us, hist, roles, seen, pos = split(W.rows, items, CUTOFF, DAYS); train = [r for r in W.rows if r[3] < CUTOFF]; pop = Popularity(items, train)
    prof = {p["user"]: p for p in W.profiles}; idx = {it["id"]: i for i, it in enumerate(items)}; G = GraphReco(W.G, items); K = KNNReco(W.E, items); H = Hybrid(dict(graph=G, knn=K, popularity=pop), dict(graph=1, knn=1, popularity=0.2), "weighted")
    ev = collections.defaultdict(list); first = {}
    for u, role, it, day, h in sorted(W.rows, key=lambda r: (r[3], r[4])):
        if day >= CUTOFF: first.setdefault(u, []).append((idx[it], day))
    out = {}
    for k in ks:
        res = {}
        for name in ("popularity", "topic-popularity", "knn", "graph", "hybrid"):
            P, R, N, ok = [], [], [], []
            for u in us:
                evs = first.get(u, [])[:k]; hset = {i for i, _ in evs}; p = pos[u] - hset
                if not p: continue
                tops = [t for t, _ in sorted(prof_topics(prof[u]).items(), key=lambda x: -x[1])[:2]]; h = evs; sn = set(hset)
                m = {"popularity": pop, "topic-popularity": TopicPop(items, pop, tops), "knn": K, "graph": G, "hybrid": H}[name]
                if name in ("knn", "graph") and k == 0: P.append(0); R.append(0); N.append(0); continue      # these need history: without it they return nothing useful
                r = recommend(m, items, roles[u], h, CUTOFF + 1, sn, k=10) if h or name in ("popularity", "topic-popularity", "hybrid") else []
                hit5 = sum(1 for i in r[:5] if i in p); P.append(hit5 / 5); R.append(hit5 / len(p)); N.append(sum(1 / math.log2(j + 2) for j, i in enumerate(r[:10]) if i in p) / sum(1 / math.log2(j + 2) for j in range(min(len(p), 10))))
            res[name] = dict(p5=float(np.mean(P)), r5=float(np.mean(R)), ndcg10=float(np.mean(N)), n=len(P), per_user=N)
        out[k] = res
    return out
def prof_topics(p): return p["topics"]
def new_item_experiment(W, frac=0.12, mode="section", seed=0):
    """Hold out cold items: they have NO train events and are absent from the graph until `add_item` (content edges: MENTIONS, IN_DOC, NEXT) and from popularity counts.
    mode 'section': random verified sections of known documents; mode 'document': one whole document. Metric: hit-rate@10 = share of (user, cold item read in test) pairs where the item is in the user's top-10 (history = train)."""
    items = W.items; rng = random.Random(seed); idx = {it["id"]: i for i, it in enumerate(items)}
    docs = collections.defaultdict(list)
    for i, it in enumerate(items):
        if it["kind"] == "doc" and it["verified"] and it["sensitivity"] == "public" and topic_of(it["doc"]): docs[it["doc"]].append(i)
    if mode == "section": cold = set(rng.sample([i for v in docs.values() for i in v], int(frac * sum(len(v) for v in docs.values()))))
    else: d = rng.choice([d for d, v in docs.items() if len(v) >= 6]); cold = set(docs[d])
    ent_of, idf, types = W.ent_of, W.idf, W.types; keep = [i for i in range(len(items)) if i not in cold]
    G = ItemGraph([items[i] for i in keep], [ent_of[i] for i in keep], idf, types)
    train = [r for r in W.rows if r[3] < CUTOFF and idx[r[2]] not in cold]; pop = Popularity(items, train)
    us, hist, roles, seen, pos = split([r for r in W.rows if not (r[3] < CUTOFF and idx[r[2]] in cold)], items, CUTOFF, DAYS)
    models = {}; before = None
    def make(G):
        g = GraphReco(G, items); k = KNNReco(W.E, items); return {"popularity": pop, "knn": k, "graph": g, "hybrid": Hybrid(dict(graph=g, knn=k, popularity=pop), dict(graph=1, knn=1, popularity=0.2), "weighted")}
    def run(models, with_cold):
        r = {}
        for name, m in models.items():
            hits = tot = 0
            for u in us:
                tc = pos[u] & cold
                if not tc: continue
                recs = recommend(m, items, roles[u], hist[u], CUTOFF, seen[u], k=10, restrict=(None if with_cold else set(range(len(items))) - cold)) if False else recommend(m, items, roles[u], hist[u], CUTOFF, seen[u], k=10)
                tot += len(tc); hits += len(tc & set(recs))
            r[name] = dict(hit10=hits / max(tot, 1), pairs=tot)
        return r
    res_before = run(make(G), False)            # graph does not contain the cold items yet (graph scores 0 for them); kNN/embeddings do (content only)
    for i in sorted(cold, key=lambda i: items[i]["id"]): G.add_item(items[i], ent_of[i], idf, types)
    res_after = run(make(G), True); G.close()
    return dict(n_cold=len(cold), before_insert=res_before, after_insert=res_after)
def main():
    from .eval import World
    ap = argparse.ArgumentParser(); ap.add_argument("--seeds", type=int, nargs="+", default=[0, 1, 2, 3, 4]); ap.add_argument("--out", default=str(ROOT / "eval/cold.json")); a = ap.parse_args(); allr = {}
    for s in a.seeds:
        W = World(s); r = dict(new_user=new_user_experiment(W), new_section=new_item_experiment(W, mode="section", seed=s), new_document=new_item_experiment(W, mode="document", seed=s))
        for k in r["new_user"]:
            for m in r["new_user"][k]: r["new_user"][k][m].pop("per_user", None)
        allr[s] = r; W.close(); print("seed", s, json.dumps(r)[:600], flush=True)
    json.dump(allr, open(a.out, "w"), indent=1)
if __name__ == "__main__": main()
