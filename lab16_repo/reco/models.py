"""Recommenders (R1): popularity baseline, graph (Cypher paths over the item graph), embedding kNN, hybrid (weighted / RRF) + filters.
History = list of (item_index, day). All models score only *candidate* items: eligible (role, verified, freshness) and not yet read by the user."""
from __future__ import annotations
import numpy as np, collections, math
from .data import eligible
def decay_weights(hist, now, half_life):
    """recency weight of each history item (0.5 ** (age/half_life)); several reads of one item are merged (max)"""
    w = {}
    for i, d in hist: w[i] = max(w.get(i, 0.0), 0.5 ** (max(now - d, 0) / half_life))
    return w
class Popularity:
    """number of distinct train users who read the item (+ small content-free tie-break), computed from TRAIN events only"""
    name = "popularity"
    def __init__(self, items, train_events):
        self.cnt = collections.Counter(); self.users = len({e[0] for e in train_events}); idx = {it["id"]: i for i, it in enumerate(items)}
        for u, i in {(e[0], idx[e[2]]) for e in train_events if e[2] in idx}: self.cnt[i] += 1
    def scores(self, cands, hist=None, now=None, **kw): return np.array([self.cnt.get(i, 0) for i in cands], dtype=float) + 1e-6 * np.arange(len(cands))[::-1] / max(len(cands), 1)
    def pop_share(self, i): return (self.cnt.get(i, 0) + 1) / (self.users + 1)
class GraphReco:
    """score(c) = sum_h w_h * ( ent_w * sum_{e in H∩C} idf_e  +  next_w * [h-NEXT-c or c-NEXT-h]  +  doc_w * [same doc] ), computed by Cypher path queries.
    `components()` returns raw per-item components + best path, so that weights can be re-combined without re-querying (used for tuning and explanations)."""
    name = "graph"
    def __init__(self, G, items, ent_w=1.0, next_w=3.0, doc_w=0.5, half_life=14.0): self.G, self.items, self.ent_w, self.next_w, self.doc_w, self.half_life = G, items, ent_w, next_w, doc_w, half_life; self._cache = {}
    def components(self, hist, now):
        w = decay_weights(hist, now, self.half_life); key = (tuple(sorted(w.items())),)
        if key in self._cache: return self._cache[key]
        H = [dict(id=self.items[i]["id"], w=float(x)) for i, x in w.items()]; comp = {}
        def add(c, k, s, path):
            d = comp.setdefault(c, dict(ent=0.0, next=0.0, doc=0.0, paths=[])); d[k] += s; d["paths"].append((s, path))
        for c, h, e, s, t in self.G.q("UNWIND $H AS h MATCH (a:Chunk {id: h.id})-[:MENTIONS]->(e:Entity)<-[:MENTIONS]-(c:Chunk) WHERE c.id <> a.id RETURN c.id, a.id, e.name, h.w * e.idf, e.type", H=H): add(c, "ent", s, dict(kind="entity", via=h, entity=e, etype=t))
        for c, h, s in self.G.q("UNWIND $H AS h MATCH (a:Chunk {id: h.id})-[:NEXT]-(c:Chunk) RETURN c.id, a.id, h.w", H=H): add(c, "next", s, dict(kind="next", via=h))
        for c, h, s in self.G.q("UNWIND $H AS h MATCH (a:Chunk {id: h.id})-[:IN_DOC]->(d:Doc)<-[:IN_DOC]-(c:Chunk) WHERE c.id <> a.id RETURN c.id, a.id, h.w", H=H): add(c, "doc", s, dict(kind="doc", via=h))
        self._cache[key] = comp; return comp
    def scores(self, cands, hist, now, **kw):
        comp = self.components(hist, now); pos = {it["id"]: i for i, it in enumerate(self.items)}; out = np.zeros(len(cands))
        for j, i in enumerate(cands):
            c = comp.get(self.items[i]["id"])
            if c: out[j] = self.ent_w * c["ent"] + self.next_w * c["next"] + self.doc_w * c["doc"]
        return out
    def explain_path(self, cand_idx, hist, now):
        comp = self.components(hist, now).get(self.items[cand_idx]["id"]);
        if not comp: return None
        ws = dict(entity=self.ent_w, next=self.next_w, doc=self.doc_w); s, p = max(comp["paths"], key=lambda x: x[0] * ws[x[1]["kind"]]); return p
class KNNReco:
    """item-kNN on bge embeddings: score(c) = weighted mean of the top-m cosine similarities between c and the user's history items"""
    name = "knn"
    def __init__(self, E, items, m=3, half_life=14.0): self.E, self.items, self.m, self.half_life = E, items, m, half_life
    def scores(self, cands, hist, now, **kw):
        w = decay_weights(hist, now, self.half_life)
        if not w: return np.zeros(len(cands))
        hi = np.array(list(w)); hw = np.array([w[i] for i in hi]); S = self.E[np.array(cands)] @ self.E[hi].T * hw[None, :]; m = min(self.m, S.shape[1]); top = -np.sort(-S, axis=1)[:, :m]; return top.mean(1)
    def explain_path(self, cand_idx, hist, now):
        w = decay_weights(hist, now, self.half_life)
        if not w: return None
        hi = np.array(list(w)); sims = self.E[hi] @ self.E[cand_idx]; j = int(np.argmax(sims)); return dict(kind="similar", via=self.items[int(hi[j])]["id"], cosine=round(float(sims[j]), 3))
def _norm(x):
    lo, hi = float(np.min(x)), float(np.max(x)); return (x - lo) / (hi - lo) if hi > lo else np.zeros_like(x)
class Hybrid:
    """mode='weighted': sum_k w_k * minmax(score_k) (popularity enters as log1p); mode='rrf': sum_k w_k / (k_rrf + rank_k). Candidates with a zero score of a model get rank = |C| (no vote) in RRF."""
    def __init__(self, parts: dict, weights: dict, mode="weighted", k_rrf=60): self.parts, self.weights, self.mode, self.k_rrf = parts, weights, mode, k_rrf; self.name = f"hybrid-{mode}"
    def scores(self, cands, hist, now, **kw):
        tot = np.zeros(len(cands)); n = len(cands)
        for k, wk in self.weights.items():
            if wk == 0: continue
            s = self.parts[k].scores(cands, hist, now)
            if k == "popularity": s = np.log1p(s)
            if self.mode == "weighted": tot += wk * _norm(s)
            else:
                order = np.argsort(-s, kind="stable"); rank = np.empty(n); rank[order] = np.arange(1, n + 1); rank[s <= 0] = n * 10; tot += wk / (self.k_rrf + rank)
        return tot
def recommend(model, items, role, hist, now, seen, k=10, verified_only=True, max_age_days=None, as_of=None, return_scores=False):
    """filters first (R1 C2): role/sensitivity, verified, freshness, not seen -> then rank"""
    kw = {} if as_of is None else dict(as_of=as_of); cands = [i for i in eligible(items, role, verified_only, max_age_days, **kw) if i not in seen]
    if not cands: return ([] if not return_scores else [])
    s = model.scores(cands, hist, now); order = np.lexsort((np.arange(len(cands)), -s))[:k]; out = [(cands[j], float(s[j])) for j in order]
    return out if return_scores else [i for i, _ in out]
