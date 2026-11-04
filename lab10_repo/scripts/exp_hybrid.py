"""R4: hybrid retrieval traces, rerank effect, pre-filter checks, wins/losses -> docs/evidence/hybrid.json"""
import json, sys
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT))
from src import chunking, hybrid, evaluate, metrics
from src.embed import Embedder

docs = hybrid.load_docs(); gold = evaluate.load_gold(); G = {g["qid"]: g for g in gold}
ch = chunking.chunk_corpus(docs, "heading", max_words=250, min_words=40)
R = hybrid.Retriever(ch, docs, "bge", tag="heading-250")
MODES = ("bm25", "dense", "hybrid", "hybrid_rerank")


def first_rank(rows, ev):
    for i, x in enumerate(metrics.gains(R.spans([(r, 0) for r in rows]), ev), 1):
        if x: return i
    return None


def show(row, n=110):
    c = R.chunks[row]; return dict(row=row, chunk_id=c.id, section=c.section[:60], text=c.text.replace("\n", " ")[:n])


res = {m: {x["qid"]: x for x in evaluate.run(R, gold, m, 10)} for m in MODES}
out = dict(n_queries=len(gold), first_rank={}, wins=[], losses=[], rerank={}, prefilter={}, traces=[])
INF = 99
for g in gold:
    if not g["answerable"]: continue
    out["first_rank"][g["qid"]] = {m: first_rank(res[m][g["qid"]]["rows"], g["evidence"]) for m in MODES}
fr = lambda q, m: out["first_rank"][q][m] or INF
# hybrid wins: better first-hit than BOTH single retrievers (fusion gain) or rescues a miss of one; sorted by gain
cand = []
for q in out["first_rank"]:
    d, b, h = fr(q, "dense"), fr(q, "bm25"), fr(q, "hybrid")
    cand.append((min(d, b) - h, q))
for gain, q in sorted(cand, reverse=True)[:8]:
    if gain > 0: out["wins"].append(dict(qid=q, query=G[q]["query"], type=G[q]["type"], ranks=out["first_rank"][q], gain=gain))
loss = sorted([(fr(q, "hybrid") - min(fr(q, "dense"), fr(q, "bm25")), q) for q in out["first_rank"]], reverse=True)
out["losses"] = [dict(qid=q, query=G[q]["query"], type=G[q]["type"], ranks=out["first_rank"][q], loss=l) for l, q in loss[:6] if l > 0]
out["win_loss_counts"] = dict(hybrid_better_than_both=sum(1 for g_, q in cand if g_ > 0), hybrid_worse_than_best_single=sum(1 for l, q in loss if l > 0), equal=sum(1 for g_, q in cand if g_ == 0))
out["vs_dense"] = dict(better=sum(fr(q, "hybrid") < fr(q, "dense") for q in out["first_rank"]), worse=sum(fr(q, "hybrid") > fr(q, "dense") for q in out["first_rank"]))
out["vs_bm25"] = dict(better=sum(fr(q, "hybrid") < fr(q, "bm25") for q in out["first_rank"]), worse=sum(fr(q, "hybrid") > fr(q, "bm25") for q in out["first_rank"]))
# traces for the selected examples (pipeline stages visible)
for q in [w["qid"] for w in out["wins"][:3]] + [l["qid"] for l in out["losses"][:1]]:
    qq = G[q]["query"]; bm = R.r_bm25(qq, 5); de = R.r_dense(qq, 5); hy = R.r_hybrid(qq, 5); ev = G[q]["evidence"]
    mark = lambda lst: [dict(show(r, 70), relevant=bool(metrics.gains(R.spans([(r, 0)]), ev)[0])) for r, _ in lst[:3]]
    out["traces"].append(dict(qid=q, query=qq, evidence=[e["quote"][:140] for e in ev], bm25=mark(bm), dense=mark(de), hybrid=mark(hy), ranks=out["first_rank"][q]))
# rerank effect
chg_set = chg_order = 0; ex = []
for g in gold:
    if not g["answerable"]: continue
    a, b = res["hybrid"][g["qid"]]["rows"][:5], res["hybrid_rerank"][g["qid"]]["rows"][:5]
    if set(a) != set(b): chg_set += 1
    if a != b:
        chg_order += 1
        if len(ex) < 2 and set(a) == set(b): ex.append(dict(qid=g["qid"], query=g["query"], before=[show(r, 60) for r in a], after=[show(r, 60) for r in b]))
imp = sum(1 for q in out["first_rank"] if fr(q, "hybrid_rerank") < fr(q, "hybrid")); wors = sum(1 for q in out["first_rank"] if fr(q, "hybrid_rerank") > fr(q, "hybrid"))
out["rerank"] = dict(top5_set_changed=chg_set, top5_order_or_set_changed=chg_order, n=len(out["first_rank"]), first_hit_improved=imp, first_hit_worse=wors, examples=ex, rerank_in=30, rerank_out=5,
                     ms_hybrid=float(np.median([x["ms"] for x in res["hybrid"].values()])), ms_rerank=float(np.median([x["ms"] for x in res["hybrid_rerank"].values()])))
# a case where the rerank changed the first hit
for q in out["first_rank"]:
    if fr(q, "hybrid_rerank") != fr(q, "hybrid"):
        out["rerank"]["first_hit_example"] = dict(qid=q, query=G[q]["query"], before=fr(q, "hybrid"), after=fr(q, "hybrid_rerank")); break
# pre-filter checks
pf = {}
uk_q = "Яке сховище використовується для SPARQL-запитів?"
nofilt = R.search(uk_q, "hybrid", 10); filt = R.search(uk_q, "hybrid", 10, hybrid.make_pred(sensitivity=["public"]))
cnt = lambda r: {s: sum(R.metas[row]["sensitivity"] == s for row, _ in r) for s in ("public", "internal", "restricted")}
pf["sensitivity"] = dict(query=uk_q, no_filter=cnt(nofilt), public_only=cnt(filt), passed=cnt(filt)["restricted"] == 0 and cnt(filt)["internal"] == 0 and len(filt) == 10 and cnt(nofilt)["restricted"] > 0)
q2 = "how to filter variants by expression"; f2 = R.search(q2, "hybrid", 10, hybrid.make_pred(types=["manual"])); n2 = R.search(q2, "hybrid", 10)
pf["type"] = dict(query=q2, no_filter_types={t: sum(R.metas[r]["type"] == t for r, _ in n2) for t in {R.metas[r]["type"] for r, _ in n2}}, manual_only={t: sum(R.metas[r]["type"] == t for r, _ in f2) for t in {R.metas[r]["type"] for r, _ in f2}},
                  passed=len(f2) == 10 and all(R.metas[r]["type"] == "manual" for r, _ in f2))
dates = sorted({d["date"] for d in docs}); cut = dates[len(dates) // 2]
q3 = "how do I run the pipeline"; f3 = R.search(q3, "hybrid", 10, hybrid.make_pred(date_from=cut)); n3 = R.search(q3, "hybrid", 10)
pf["date"] = dict(query=q3, date_from=cut, min_date_unfiltered=min(R.metas[r]["date"] for r, _ in n3), min_date_filtered=min(R.metas[r]["date"] for r, _ in f3), n=len(f3), passed=len(f3) == 10 and all(R.metas[r]["date"] >= cut for r, _ in f3))
q4 = "how to call variants with bcftools mpileup"; combo = R.search(q4, "hybrid_rerank", 5, hybrid.make_pred(types=["manual", "readme"], sensitivity=["public"], date_from="2026-01-01"))
pf["combined_rerank"] = dict(query=q4, results=[show(r, 60) for r, _ in combo], passed=len(combo) == 5 and all(R.metas[r]["type"] in ("manual", "readme") and R.metas[r]["sensitivity"] == "public" for r, _ in combo))
# the filter is applied BEFORE ranking: with a filter selecting 7 chunks we still get all 7 back (post-filtering of top-10 would drop most)
few = hybrid.make_pred(types=["output-reference"], sensitivity=["public"], date_from="2026-10-26")
nf = sum(1 for m in R.metas if few(m)); got = R.search("quality control report", "dense", 10, few)
pf["prefilter_vs_postfilter"] = dict(matching_chunks=nf, returned=len(got), post_filter_returned=sum(1 for r, _ in R.search("quality control report", "dense", 10) if few(R.metas[r])), passed=len(got) == min(10, nf))
out["prefilter"] = pf
json.dump(out, open(ROOT / "docs/evidence/hybrid.json", "w"), indent=1, ensure_ascii=False)
print(out["win_loss_counts"], out["vs_dense"], out["vs_bm25"], {k: v["passed"] for k, v in pf.items()}); print(out["rerank"]["top5_set_changed"], out["rerank"]["first_hit_improved"], out["rerank"]["first_hit_worse"])
