"""R5: evaluate >= 4 configurations on the final gold set -> docs/evidence/search_eval.json"""
import json, sys, time
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT))
from src import chunking, hybrid, evaluate
from src.embed import Embedder

docs = hybrid.load_docs(); gold = evaluate.load_gold(); ans = [g for g in gold if g["answerable"]]
ch = chunking.chunk_corpus(docs, "heading", max_words=250, min_words=40)
Rb = hybrid.Retriever(ch, docs, "bge", tag="heading-250"); Rm = hybrid.Retriever(ch, docs, "minilm", tag="heading-250")
CONF = [("BM25", Rb, "bm25"), ("Dense MiniLM", Rm, "dense"), ("Dense bge-small", Rb, "dense"), ("Hybrid (BM25+bge, RRF k=60)", Rb, "hybrid"), ("Hybrid (BM25+MiniLM, RRF)", Rm, "hybrid"), ("Hybrid+rerank (MaxSim top30->5)", Rb, "hybrid_rerank")]
out = dict(n_queries=len(gold), n_answerable=len(ans), configs={})
for name, R, mode in CONF:
    for g in gold[:3]: R.search(g["query"], mode, 10)       # warm-up
    res = evaluate.run(R, gold, mode, 10); a = evaluate.agg(res)
    bytype = {t: evaluate.agg([x for x in res if x["type"] == t]) for t in ("keyword", "paraphrase", "multi_step", "uk_cross", "uk_internal")}
    ms = np.array([x["ms"] for x in res]); a["ms_p95"] = float(np.percentile(ms, 95))
    out["configs"][name] = dict(mode=mode, model=R.model, overall=a, by_type=bytype, per_query={x["qid"]: dict(r5=x.get("r5"), mrr=x.get("mrr"), ndcg=x.get("ndcg"), ms=x["ms"]) for x in res},
                                top_scores={x["qid"]: (x["scores"][0] if x["scores"] else 0.0) for x in res})
    print(name, {k: round(a[k], 3) for k in ("r5", "r10", "mrr", "ndcg", "ms")}, flush=True)
# no-answer analysis: can the top-1 dense score separate unanswerable queries? (AUC over answerable vs no-answer)
def auc(pos, neg):
    return float(np.mean([(p > n) + 0.5 * (p == n) for p in pos for n in neg]))
na = [g["qid"] for g in gold if not g["answerable"]]
for name in ("Dense MiniLM", "Dense bge-small"):
    ts = out["configs"][name]["top_scores"]; pos = [ts[g["qid"]] for g in ans]; neg = [ts[q] for q in na]
    out.setdefault("no_answer", {})[name] = dict(auc=auc(pos, neg), mean_answerable=float(np.mean(pos)), mean_no_answer=float(np.mean(neg)), max_no_answer=float(np.max(neg)), min_answerable=float(np.min(pos)))
out["corpus"] = dict(chunks=len(ch), bge_embed_s=Rb.t_embed, minilm_embed_s=Rm.t_embed)
json.dump(out, open(ROOT / "docs/evidence/search_eval.json", "w"), indent=1)
