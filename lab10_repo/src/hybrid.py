"""Retriever: BM25 + dense (FAISS HNSW) + RRF fusion + late-interaction reranker + metadata pre-filter."""
from __future__ import annotations
import json, re, time
from pathlib import Path
import numpy as np
from rank_bm25 import BM25Okapi
from .embed import Embedder, cached_encode
from .index import VectorStore

ROOT = Path(__file__).resolve().parents[1]
STOP = set("a an and are as at be by for from how i in is it of on or that the this to was what when where which who why with do does can should my your".split())
RRF_K = 60


def tok(s: str):
    return [w for w in re.findall(r"\w+", s.lower()) if w not in STOP]


def load_docs():
    man = json.load(open(ROOT / "data/docs_manifest.json", encoding="utf-8"))
    return [dict(d, text=(ROOT / "data/docs_clean" / f"{d['doc_id']}.md").read_text(encoding="utf-8")) for d in man]


def make_pred(types=None, sensitivity=None, date_from=None, date_to=None, lang=None):
    """Metadata pre-filter (applied before ranking, not after): returns a predicate over chunk metadata or None."""
    if not any([types, sensitivity, date_from, date_to, lang]): return None
    def pred(m):
        return ((not types or m["type"] in types) and (not sensitivity or m["sensitivity"] in sensitivity) and
                (not date_from or m["date"] >= date_from) and (not date_to or m["date"] <= date_to) and (not lang or m["lang"] == lang))
    return pred


class Retriever:
    def __init__(self, chunks, docs, model="bge", tag="x", embedder: Embedder | None = None):
        self.emb = embedder or Embedder(model); self.model = model; self.chunks = list(chunks)
        dm = {d["doc_id"]: d for d in docs}
        self.metas = [dict(row=i, chunk_id=c.id, doc_id=c.doc_id, start=c.start, end=c.end, section=c.section,
                           type=dm[c.doc_id]["type"], sensitivity=dm[c.doc_id]["sensitivity"], date=dm[c.doc_id]["date"], lang=dm[c.doc_id]["lang"])
                      for i, c in enumerate(self.chunks)]
        t0 = time.perf_counter(); self.vecs = cached_encode(self.emb, [c.text for c in self.chunks], tag); self.t_embed = time.perf_counter() - t0
        t0 = time.perf_counter(); self.store = VectorStore(self.vecs.shape[1]); self.store.add(self.vecs, self.metas); self.t_index = time.perf_counter() - t0
        self.bm25 = BM25Okapi([tok(c.text) for c in self.chunks]); self._tokvec = {}

    # ---- single rankers: return [(row, score)] ----
    def r_bm25(self, q, k=50, pred=None):
        s = self.bm25.get_scores(tok(q)); ok = np.array([pred is None or pred(m) for m in self.metas])
        s = np.where(ok, s, -np.inf); top = np.argsort(-s)[:k]
        return [(int(i), float(s[i])) for i in top if s[i] > 0]

    def r_dense(self, q, k=50, pred=None, ef=None):
        v = self.emb.encode([q], query=True)[0]; return self.store.search(v, k, pred, ef)

    @staticmethod
    def rrf(lists, k=RRF_K, top=50):
        sc = {}
        for lst in lists:
            for r, (row, _) in enumerate(lst, 1): sc[row] = sc.get(row, 0) + 1 / (k + r)
        return sorted(sc.items(), key=lambda x: -x[1])[:top]

    def r_hybrid(self, q, k=50, pred=None):
        return self.rrf([self.r_bm25(q, 50, pred), self.r_dense(q, 50, pred)], top=k)

    def _tv(self, row):
        if row not in self._tokvec: self._tokvec[row] = self.emb.tokens(self.chunks[row].text)
        return self._tokvec[row]

    def r_rerank(self, q, cands, topn=5):
        """Late-interaction (MaxSim) rerank: mean over query tokens of the best cosine to any chunk token."""
        qv = self.emb.tokens(q)
        sc = [(row, float((qv @ self._tv(row).T).max(1).mean())) for row, _ in cands]
        return sorted(sc, key=lambda x: -x[1])[:topn]

    def search(self, q, mode="hybrid", k=10, pred=None, rerank_in=30):
        if mode == "bm25": r = self.r_bm25(q, k, pred)
        elif mode == "dense": r = self.r_dense(q, k, pred)
        elif mode == "hybrid": r = self.r_hybrid(q, k, pred)
        elif mode == "hybrid_rerank":
            c = self.r_hybrid(q, rerank_in, pred); rr = self.r_rerank(q, c, 5)
            top5 = {row for row, _ in rr}; r = rr + [x for x in c if x[0] not in top5]   # reranked top-5, then remaining RRF order
        else: raise ValueError(mode)
        return self._dedupe(r[:k * 2])[:k]

    def _dedupe(self, r):
        """Hierarchical children share a parent context: keep the best child per parent."""
        seen, out = set(), []
        for row, s in r:
            c = self.chunks[row]; key = (c.doc_id, c.context_span)
            if c.context_span != (c.start, c.end) and key in seen: continue
            seen.add(key); out.append((row, s))
        return out

    def spans(self, r):  # for metrics: the child span that was matched
        return [(self.chunks[row].doc_id, self.chunks[row].start, self.chunks[row].end) for row, _ in r]

    def ctx_words(self, r, n=5):
        return float(np.mean([len(self.chunks[row].context.split()) for row, _ in r[:n]])) if r else 0.0
