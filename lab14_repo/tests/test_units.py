"""Unit tests for dedup, conflict detection and the gold set (run in CI before the quality gate)."""
import sys, csv, json, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent; sys.path.insert(0, str(ROOT))
from quality import dedup as D, conflicts as C
from quality.common import chunks, STORE

def test_normalise_ignores_title_line_and_markdown():
    a = "doc_a — Intro\n## Intro\n\nUse `-r 3.3.2` **always** now"; b = "doc_b — Other\n### Other\n\nuse -r 3.3.2 always now"
    assert D.normalise(a) == D.normalise(b)
def test_merge_unmerge_roundtrip():
    ch = chunks(STORE)[:30]; pairs = [(ch[0]["chunk_id"], ch[1]["chunk_id"]), (ch[1]["chunk_id"], ch[2]["chunk_id"])]
    merged, log = D.merge(ch, pairs); assert len(merged) == 28 and len(log) == 1 and len(log[0]["absorbed"]) == 2
    back = D.unmerge(merged, log[0]["canonical"]); assert sorted(c["chunk_id"] for c in back) == sorted(c["chunk_id"] for c in ch)
    by = {c["chunk_id"]: c for c in ch}; assert all(c == by[c["chunk_id"]] for c in back)
def test_canonical_prefers_public_then_longest():
    g = [dict(chunk_id="b", sensitivity="internal", text="x" * 99), dict(chunk_id="a", sensitivity="public", text="x" * 10), dict(chunk_id="c", sensitivity="public", text="x" * 50)]
    assert D.canonical_choice(g)["chunk_id"] == "c"
def test_never_merge_across_sensitivity():
    f = dict(same_sens=False, tfidf=1, emb=1, fuzz=1, ratio=1, len_ratio=1); assert not D.decide(f, 0.9)
def test_blocking_reduces_comparisons_and_keeps_gold_duplicates():
    S = D.Store(); P = set(D.blocking(S)); n = len(S.c); assert len(P) < 0.01 * n * (n - 1) / 2
    for r in csv.DictReader(open(ROOT / "quality/pairs_gold.csv")):
        if r["dup"] == "1": a, b = sorted((S.idx[r["a"]], S.idx[r["b"]])); assert (a, b) in P, r["pair_id"]
def test_gold_set_shape():
    rows = list(csv.DictReader(open(ROOT / "quality/pairs_gold.csv"))); main = [r for r in rows if r["split"] != "probe"]
    assert len(main) >= 100 and sum(r["split"] == "dev" for r in rows) >= 50 and sum(r["split"] == "test" for r in rows) >= 50
    assert {r["label"] for r in rows} <= {"DUP", "RELATED", "DISTINCT"} and sum(r["dup"] == "1" for r in main) >= 10
    assert not ({(r["a"], r["b"]) for r in rows if r["split"] == "dev"} & {(r["a"], r["b"]) for r in rows if r["split"] == "test"})
def test_conflicts_detected_four_types():
    cf = C.detect(STORE); assert len(cf) >= 5 and {c["type"] for c in cf} == {"value", "temporal", "terminological", "logical"}
    assert all(len(c["items"]) >= 2 and all("source" in i for i in c["items"]) for c in cf)
def test_clean_store_has_no_logical_conflict():
    assert not [c for c in C.detect(ROOT / "store_clean") if c["type"] == "logical"]
def test_decision_log_complete():
    dec = list(csv.DictReader(open(ROOT / "quality/decisions.csv", encoding="utf-8"))); ids = {c["id"] for c in C.detect(STORE)}
    assert ids <= {d["conflict_id"] for d in dec} and all(d["decided_by"] and d["decided_at"] and d["rationale"] for d in dec)
