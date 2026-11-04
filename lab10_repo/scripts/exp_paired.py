"""Paired bootstrap (2000 resamples, seed 42) of per-query differences between configurations -> docs/evidence/paired.json"""
import json, numpy as np
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
S = json.load(open(ROOT / "docs/evidence/search_eval.json"))["configs"]
H = "Hybrid (BM25+bge, RRF k=60)"; RR = "Hybrid+rerank (MaxSim top30->5)"
def paired(a, b, k, seed=42):
    qa, qb = S[a]["per_query"], S[b]["per_query"]; ids = [q for q in qa if qa[q][k] is not None]
    d = np.array([qa[q][k] - qb[q][k] for q in ids]); rnd = np.random.default_rng(seed)
    bs = [d[rnd.integers(0, len(d), len(d))].mean() for _ in range(2000)]
    return dict(diff=float(d.mean()), ci=[float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))])
out = {}
for a, b in [(H, "Dense bge-small"), (H, "BM25"), (RR, H), ("BM25", "Dense bge-small"), ("Dense bge-small", "Dense MiniLM")]:
    out[f"{a} − {b}"] = {k: paired(a, b, k) for k in ("r5", "mrr", "ndcg")}
json.dump(out, open(ROOT / "docs/evidence/paired.json", "w"), indent=1, ensure_ascii=False)
