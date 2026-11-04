import sys, math
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src import metrics, chunking
from src.index import VectorStore
from src.hybrid import Retriever, make_pred, tok


def unit(n, d=16, seed=0):
    v = np.random.default_rng(seed).normal(size=(n, d)).astype(np.float32); return v / np.linalg.norm(v, axis=1, keepdims=True)


def meta(n, doc="d"):
    return [dict(chunk_id=f"{doc}#{i}", doc_id=doc, type="t", sensitivity="public", date="2026-01-01", lang="en") for i in range(n)]


def test_search_finds_itself_and_delete_tombstones():
    s = VectorStore(16, m=8, ef_construction=40, ef_search=32); v = unit(50); s.add(v, meta(50))
    assert s.search(v[7], 1)[0][0] == 7
    assert s.delete_doc("d") == 50 and s.search(v[7], 1) == []


def test_upsert_replaces_and_compact_drops_dead_rows():
    s = VectorStore(16, m=8, ef_construction=40, ef_search=32); a, b = unit(20, seed=1), unit(10, seed=2)
    s.add(a, meta(20, "a")); s.add(b, meta(10, "b"))
    old, new = s.upsert_doc("a", unit(5, seed=3), meta(5, "a")); assert (old, new) == (20, 5) and abs(s.dead_ratio() - 20 / 35) < 1e-9
    r = s.search(a[0], 5); assert all(s.meta[i]["doc_id"] != "a" or i >= 30 for i, _ in r)
    s.compact(); assert len(s.meta) == 15 and all(s.alive) and s.dead_ratio() == 0


def test_prefilter_applies_before_ranking():
    s = VectorStore(16, m=8, ef_construction=40, ef_search=32); v = unit(60); mt = meta(60)
    for i, m in enumerate(mt): m["sensitivity"] = "restricted" if i % 2 else "public"
    s.add(v, mt); r = s.search(v[1], 10, make_pred(sensitivity=["public"]))
    assert len(r) == 10 and all(mt[i]["sensitivity"] == "public" for i, _ in r)   # still k results, none restricted


def test_metrics_span_overlap_and_novel_coverage():
    ev = [dict(doc_id="d", start=100, end=200)]
    assert metrics.covers("d", 90, 400, ev[0]) and not metrics.covers("d", 190, 400, ev[0]) and not metrics.covers("x", 0, 999, ev[0])
    ranked = [("d", 0, 50), ("d", 80, 220), ("d", 90, 230)]            # second and third cover the same span
    assert metrics.gains(ranked, ev) == [0, 1, 0]
    assert metrics.mrr_at(ranked, ev) == 0.5 and metrics.recall_at(ranked, ev, 1) == 0 and metrics.recall_at(ranked, ev, 5) == 1
    assert math.isclose(metrics.ndcg_at(ranked, ev), 1 / math.log2(3))


def test_multi_evidence_recall_and_kappa():
    ev = [dict(doc_id="d", start=0, end=100), dict(doc_id="d", start=500, end=600)]
    assert metrics.recall_at([("d", 0, 120)], ev, 5) == 0.5
    assert metrics.cohen_kappa([1, 1, 0, 0], [1, 1, 0, 0]) == 1.0 and abs(metrics.cohen_kappa([1, 0, 1, 0], [1, 0, 0, 1])) < 1e-9


def test_chunkers_cover_and_respect_offsets():
    text = "# T\n\n## A\n" + ("alpha beta gamma. " * 40 + "\n\n") * 3 + "## B\n" + "delta epsilon. " * 30 + "\n"
    d = dict(doc_id="x", title="T", text=text)
    for name in ("fixed", "heading", "hierarchical"):
        ch = chunking.STRATEGIES[name](d); assert ch
        for c in ch: assert 0 <= c.start < c.end <= len(text) and c.text.strip()
    h = chunking.hierarchical(d); assert all(len(c.context) >= len(c.text) - 100 for c in h)


def test_fixed_chunker_handles_empty_input_and_invalid_sizes():
    d = dict(doc_id="x", title="T", text="")
    assert chunking.fixed(d) == []
    for size, overlap in ((0, 0), (10, -1), (10, 10)):
        try:
            chunking.fixed(d, size=size, overlap=overlap)
        except ValueError:
            pass
        else:
            raise AssertionError("invalid chunk dimensions must be rejected")


def test_rrf_and_tokenizer():
    f = Retriever.rrf([[(1, 0), (2, 0)], [(2, 0), (3, 0)]]); assert f[0][0] == 2 and abs(f[0][1] - (1 / 62 + 1 / 61)) < 1e-9
    assert tok("The QD of a SNP is 2.5") == ["qd", "snp", "2", "5"]
