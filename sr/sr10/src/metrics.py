"""Span-based relevance and ranking metrics (recall@k, MRR@10, nDCG@10).

A retrieved chunk covers an evidence span if it is in the same document and overlaps >= 50% of the span's length.
Binary gain with 'novel coverage': a chunk scores 1 only if it covers an evidence span not covered by a higher-ranked chunk
(so overlapping chunks of the fixed strategy cannot count the same evidence twice). A span may list alternatives ("also").
recall@k = covered evidence spans / total spans (multi-step queries have 2)."""
from __future__ import annotations
import math

THRESH = 0.5


def covers(chunk_doc, cs, ce, span) -> bool:
    for s in [span] + span.get("also", []):
        if s["doc_id"] != chunk_doc: continue
        ov = min(ce, s["end"]) - max(cs, s["start"])
        if ov >= THRESH * (s["end"] - s["start"]): return True
    return False


def gains(ranked, evidence):
    """ranked: [(doc_id, start, end)] best first -> list of 0/1 gains (novel coverage) and list of newly covered span indices."""
    seen, g = set(), []
    for d, s, e in ranked:
        new = [i for i, sp in enumerate(evidence) if i not in seen and covers(d, s, e, sp)]
        seen.update(new); g.append(1 if new else 0)
    return g


def recall_at(ranked, evidence, k):
    if not evidence: return None
    g = gains(ranked[:k], evidence)
    return sum(g) / len(evidence)


def mrr_at(ranked, evidence, k=10):
    for r, x in enumerate(gains(ranked[:k], evidence), 1):
        if x: return 1 / r
    return 0.0


def ndcg_at(ranked, evidence, k=10):
    g = gains(ranked[:k], evidence)
    dcg = sum(x / math.log2(i + 2) for i, x in enumerate(g))
    idcg = sum(1 / math.log2(i + 2) for i in range(min(len(evidence), k)))
    return dcg / idcg if idcg else None


def all_metrics(ranked, evidence):
    return dict(r5=recall_at(ranked, evidence, 5), r10=recall_at(ranked, evidence, 10), mrr=mrr_at(ranked, evidence), ndcg=ndcg_at(ranked, evidence))


def cohen_kappa(a, b):
    n = len(a); po = sum(x == y for x, y in zip(a, b)) / n
    pa, pb = sum(a) / n, sum(b) / n; pe = pa * pb + (1 - pa) * (1 - pb)
    return (po - pe) / (1 - pe) if pe < 1 else 1.0
