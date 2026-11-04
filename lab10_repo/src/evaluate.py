"""Run a retriever on the gold set and aggregate metrics."""
import json, time, random
import numpy as np
from pathlib import Path
from . import metrics
ROOT = Path(__file__).resolve().parents[1]


def load_gold():
    return [json.loads(l) for l in open(ROOT / "eval/gold.jsonl", encoding="utf-8")]


def run(ret, gold, mode, k=10, pred=None):
    """-> per-query dicts (metrics, latency ms, ranked rows)."""
    out = []
    for g in gold:
        t0 = time.perf_counter(); r = ret.search(g["query"], mode, k, pred); ms = (time.perf_counter() - t0) * 1000
        m = metrics.all_metrics(ret.spans(r), g["evidence"]) if g["answerable"] else {}
        out.append(dict(qid=g["qid"], type=g["type"], lang=g["lang"], ms=ms, rows=[x[0] for x in r], scores=[x[1] for x in r], ctx=ret.ctx_words(r), **m))
    return out


def agg(res, keys=("r5", "r10", "mrr", "ndcg"), seed=42, boot=1000):
    a = [x for x in res if x.get("r5") is not None]; d = {"n": len(a)}
    rnd = np.random.default_rng(seed)
    for k in keys:
        v = np.array([x[k] for x in a]); d[k] = float(v.mean())
        bs = [v[rnd.integers(0, len(v), len(v))].mean() for _ in range(boot)]; d[k + "_ci"] = (float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5)))
    d["ms"] = float(np.median([x["ms"] for x in res])); d["ctx"] = float(np.mean([x["ctx"] for x in a]))
    return d
