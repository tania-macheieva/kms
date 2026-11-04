"""Uncached embedding throughput (the caches hide it): encode 100 chunks per model -> docs/evidence/timing.json"""
import json, sys, time, random
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT))
from src import chunking, hybrid
from src.embed import Embedder
docs = hybrid.load_docs(); ch = chunking.chunk_corpus(docs, "heading", max_words=250, min_words=40)
txt = [c.text for c in random.Random(42).sample(ch, 100)]; out = dict(n_sample=100, n_chunks=len(ch))
for m in ("minilm", "bge"):
    e = Embedder(m); e.encode(txt[:4]); t0 = time.perf_counter(); e.encode(txt); dt = time.perf_counter() - t0
    out[m] = dict(sample_s=dt, chunks_per_s=100 / dt, corpus_est_s=dt * len(ch) / 100)
    print(m, out[m])
json.dump(out, open(ROOT / "docs/evidence/timing.json", "w"), indent=1)
