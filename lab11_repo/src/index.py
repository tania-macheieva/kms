"""FAISS HNSW vector store with metadata, tombstone deletes, upsert-by-doc and compaction."""
from __future__ import annotations
import json, time
from pathlib import Path
import numpy as np, faiss

M, EF_CONSTRUCTION, EF_SEARCH = 32, 200, 64   # fixed HNSW parameters (docs/embeddings_cmp.md)


class VectorStore:
    """Rows are append-only; row i <-> meta[i]. faiss HNSW cannot delete, so delete = tombstone (alive[i]=False)
    and queries pass an IDSelector of allowed rows. compact() rebuilds the graph without dead rows."""

    def __init__(self, dim: int, m=M, ef_construction=EF_CONSTRUCTION, ef_search=EF_SEARCH):
        self.dim, self.m, self.efc, self.efs = dim, m, ef_construction, ef_search
        self._new(); self.meta: list[dict] = []; self.alive: list[bool] = []

    def _new(self):
        self.index = faiss.IndexHNSWFlat(self.dim, self.m, faiss.METRIC_INNER_PRODUCT)
        self.index.hnsw.efConstruction = self.efc; self.index.hnsw.efSearch = self.efs

    # ---- build / update ----
    def add(self, vecs: np.ndarray, metas: list[dict]):
        self.index.add(np.ascontiguousarray(vecs, dtype=np.float32)); self.meta += metas; self.alive += [True] * len(metas)

    def delete_doc(self, doc_id: str) -> int:
        n = 0
        for i, m in enumerate(self.meta):
            if self.alive[i] and m["doc_id"] == doc_id: self.alive[i] = False; n += 1
        return n

    def upsert_doc(self, doc_id: str, vecs, metas) -> tuple[int, int]:
        """Replace all chunks of a document: tombstone the old rows, append the new ones."""
        return self.delete_doc(doc_id), (self.add(vecs, metas) or len(metas))

    def dead_ratio(self) -> float:
        return 1 - sum(self.alive) / max(len(self.alive), 1)

    def compact(self):
        keep = [i for i, a in enumerate(self.alive) if a]
        vecs = np.vstack([self.index.reconstruct(i) for i in keep]) if keep else np.zeros((0, self.dim), np.float32)
        metas = [self.meta[i] for i in keep]; self._new(); self.meta, self.alive = [], []
        if len(keep): self.add(vecs, metas)

    # ---- query ----
    def allowed(self, pred=None) -> np.ndarray:
        return np.array([i for i, (a, m) in enumerate(zip(self.alive, self.meta)) if a and (pred is None or pred(m))], dtype=np.int64)

    def search(self, q: np.ndarray, k=10, pred=None, ef_search=None):
        ok = self.allowed(pred)
        if len(ok) == 0: return []
        p = faiss.SearchParametersHNSW(); p.sel = faiss.IDSelectorBatch(ok); p.efSearch = ef_search or self.efs
        # a restrictive selector makes HNSW traverse more nodes; widen efSearch so that k hits are still found
        if len(ok) < len(self.meta): p.efSearch = max(p.efSearch, min(len(self.meta), 4 * k + int(len(self.meta) / max(len(ok), 1)) * 8))
        D, I = self.index.search(np.ascontiguousarray(q.reshape(1, -1), dtype=np.float32), k, params=p)
        return [(int(i), float(d)) for i, d in zip(I[0], D[0]) if i >= 0]

    def vector(self, i: int): return self.index.reconstruct(int(i))

    def save(self, path):
        path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
        faiss.write_index(self.index, str(path) + ".faiss")
        json.dump(dict(meta=self.meta, alive=self.alive, m=self.m, efc=self.efc, efs=self.efs, dim=self.dim), open(str(path) + ".json", "w"))

    @classmethod
    def load(cls, path):
        j = json.load(open(str(path) + ".json")); s = cls(j["dim"], j["m"], j["efc"], j["efs"])
        s.index = faiss.read_index(str(path) + ".faiss"); s.index.hnsw.efSearch = s.efs; s.meta, s.alive = j["meta"], j["alive"]; return s
