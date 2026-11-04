"""R3: HNSW indexes for two embedding models on the chosen chunking (heading): quality, latency, build time, efSearch sweep."""
import json, sys, time
from pathlib import Path
import numpy as np, faiss
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT))
from src import chunking, hybrid, evaluate, index
from src.embed import Embedder

STRAT = json.load(open(ROOT / "docs/evidence/chosen_chunking.json")) if (ROOT / "docs/evidence/chosen_chunking.json").exists() else dict(strategy="heading", kwargs=dict(max_words=250, min_words=40))
docs = hybrid.load_docs(); gold = evaluate.load_gold(); sub = json.load(open(ROOT / "eval/subsets.json"))
g20 = [g for g in gold if g["qid"] in sub["r3"]]; gans = [g for g in gold if g["answerable"]]
ch = chunking.chunk_corpus(docs, STRAT["strategy"], **STRAT["kwargs"]); out = dict(chunking=STRAT, n_chunks=len(ch), params=dict(M=index.M, efConstruction=index.EF_CONSTRUCTION, efSearch=index.EF_SEARCH), models={})
for m in ("minilm", "bge"):
    emb = Embedder(m); R = hybrid.Retriever(ch, docs, m, tag="heading-250", embedder=emb)
    # rebuild the HNSW alone for a clean build-time measurement
    st = index.VectorStore(R.vecs.shape[1]); t0 = time.perf_counter(); st.add(R.vecs, R.metas); tb = time.perf_counter() - t0
    flat = faiss.IndexFlatIP(R.vecs.shape[1]); flat.add(R.vecs)
    qv = emb.encode([g["query"] for g in gans], query=True); _, I_ex = flat.search(qv, 10)
    sweep = {}
    for ef in (16, 64, 128, 256):
        st.index.hnsw.efSearch = ef; ts = []
        for v in qv:
            t0 = time.perf_counter(); st.index.search(v.reshape(1, -1), 10); ts.append((time.perf_counter() - t0) * 1000)
        _, I = st.index.search(qv, 10); ann = float(np.mean([len(set(a) & set(b)) / 10 for a, b in zip(I, I_ex)]))
        sweep[ef] = dict(search_ms_median=float(np.median(ts)), ann_recall_at_10=ann)
    st.index.hnsw.efSearch = index.EF_SEARCH
    qs = [g["query"] for g in g20]; te = []
    for q in qs:
        t0 = time.perf_counter(); emb.encode([q], query=True); te.append((time.perf_counter() - t0) * 1000)
    res = evaluate.run(R, g20, "dense", 10); resall = evaluate.run(R, gans, "dense", 10)
    by_lang = {l: evaluate.agg([x for x in res if x["lang"] == l]) for l in ("en", "uk")}
    out["models"][m] = dict(dim=int(R.vecs.shape[1]), embed_s=R.t_embed, build_s=tb, index_mb=round(R.vecs.nbytes / 1e6 * 1.0, 2), query_encode_ms=float(np.median(te)),
                             q20=evaluate.agg(res), q20_by_lang=by_lang, all=evaluate.agg(resall), sweep=sweep, per_query=[dict(qid=x["qid"], lang=x["lang"], r5=x["r5"], ms=x["ms"]) for x in res])
    print(m, round(out["models"][m]["q20"]["r5"], 3), {k: round(v["r5"], 2) for k, v in by_lang.items()}, flush=True)
json.dump(out, open(ROOT / "docs/evidence/index.json", "w"), indent=1)
