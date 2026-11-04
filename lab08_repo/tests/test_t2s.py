import json
from pathlib import Path

import t2s
import pytest
from store import open_store

ROOT = Path(__file__).resolve().parents[1]
QS = [json.loads(l) for l in (ROOT / "tests/t2s.jsonl").read_text(encoding="utf-8").splitlines()]


def test_set_size_and_split():
    assert len(QS) >= 15 and {q["split"] for q in QS} == {"dev", "heldout"}
    assert all(q["gold_query"] and q["gold_answer"] is not None for q in QS)


def test_gold_reproducible():
    st = open_store()
    for q in QS:
        assert t2s.execute(st, q["gold_query"], limit=None)["canon"] == q["gold_answer"], q["id"]


def test_extract_from_fence():
    assert t2s.extract_sparql("текст\n```sparql\nASK { ?s ?p ?o }\n```\nще") == "ASK { ?s ?p ?o }"


def test_syntax_negative():
    assert not t2s.check_syntax("SELEC ?x WHERE { ?x ?y }")[0]
    assert t2s.check_syntax("ASK { ?s ?p ?o }")[0]


def test_schema_check_rejects_invented_iri():
    ok, pq, _ = t2s.check_syntax("SELECT ?v ?x WHERE { ?v dkh:hasQD ?x }")
    assert ok
    good, bad = t2s.check_schema(pq, t2s.vocabulary())
    assert not good and bad == ["dkh:hasQD"]
    ok, pq, _ = t2s.check_syntax("SELECT ?v WHERE { ?v dkh:locatedIn dkh:BRCA1 }")
    assert t2s.check_schema(pq, t2s.vocabulary())[0]


def test_limit_applied():
    st = open_store()
    r = t2s.execute(st, "SELECT ?s WHERE { ?s ?p ?o }", limit=7)
    assert r["ok"] and len(r["canon"]) == 7
    r = t2s.execute(st, "SELECT ?s WHERE { ?s ?p ?o };", limit=7)
    assert r["ok"] and len(r["canon"]) == 7


def test_execute_adds_limit_after_trailing_semicolon():
    class QueryBoolean:
        def __bool__(self):
            return True

    class Store:
        query_text = ""
        def query(self, text, **kwargs):
            self.query_text = text
            return QueryBoolean()

    st = Store()
    result = t2s.execute(st, "SELECT ?s WHERE { ?s ?p ?o };", limit=7)
    assert result["ok"] and st.query_text.rstrip().endswith("LIMIT 7")


def test_evaluate_uses_supplied_store(monkeypatch):
    st = object()
    monkeypatch.setattr(t2s, "open_store_cached", lambda: pytest.fail("unexpected store fallback"))
    seen = []
    monkeypatch.setattr(t2s, "execute", lambda store, query: seen.append(store) or {"ok": True, "canon": True, "error": ""})
    result = t2s.evaluate_one(st, set(), "ASK { ?s ?p ?o }", True)
    assert seen == [st]
    assert result["result_ok"]
