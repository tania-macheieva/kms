"""R2: compare chunking strategies with a fixed embedding model (bge) -> docs/evidence/chunking.json"""
import json, sys, time
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT))
from src import chunking, hybrid, evaluate
from src.embed import Embedder

docs = hybrid.load_docs(); gold = evaluate.load_gold(); sub = json.load(open(ROOT / "eval/subsets.json"))
g10 = [g for g in gold if g["qid"] in sub["r2"]]; gans = [g for g in gold if g["answerable"]]
bge = Embedder("bge"); mini = Embedder("minilm")
CFG = {  # name -> (strategy, kwargs)
    "fixed-200/40": ("fixed", dict(size=200, overlap=40)), "heading-250": ("heading", dict(max_words=250, min_words=40)),
    "hierarchical-70/500": ("hierarchical", dict(child_words=70, parent_words=500)), "semantic": ("semantic", {}),
    # size/overlap sweep for the fixed strategy
    "fixed-100/20": ("fixed", dict(size=100, overlap=20)), "fixed-400/80": ("fixed", dict(size=400, overlap=80)), "fixed-200/0": ("fixed", dict(size=200, overlap=0)),
}
out = {}
for name, (s, kw) in CFG.items():
    t0 = time.perf_counter(); ch = chunking.chunk_corpus(docs, s, emb=mini, **kw); tch = time.perf_counter() - t0
    R = hybrid.Retriever(ch, docs, "bge", tag=name.replace("/", "_"), embedder=bge)
    w = [len(c.text.split()) for c in ch]; row = dict(strategy=s, params=kw, n_chunks=len(ch), mean_words=sum(w) / len(w), max_words=max(w), t_chunk=tch, t_embed=R.t_embed)
    for mode in ("dense", "hybrid"):
        r10 = evaluate.run(R, g10, mode, 10); ra = evaluate.run(R, gans, mode, 10)
        row[mode] = dict(q10=evaluate.agg(r10), all=evaluate.agg(ra), q10_per_query=[dict(qid=x["qid"], r5=x["r5"], ctx=x["ctx"]) for x in r10])
    out[name] = row; print(name, len(ch), round(row["dense"]["q10"]["r5"], 3), round(row["dense"]["all"]["r5"], 3), round(row["dense"]["q10"]["ctx"]), flush=True)
    json.dump(out, open(ROOT / "docs/evidence/chunking.json", "w"), indent=1)

main = ["fixed-200/40", "heading-250", "hierarchical-70/500", "semantic"]
best = max(main, key=lambda k: (out[k]["dense"]["all"]["r5"], out[k]["dense"]["all"]["mrr"]))
json.dump(dict(strategy=out[best]["strategy"], kwargs=out[best]["params"], name=best), open(ROOT / "docs/evidence/chosen_chunking.json", "w"))
print("chosen", best)
