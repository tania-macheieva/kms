import json
from pathlib import Path

import pytest

import graphdb as gdb
import t2c

ROOT = Path(__file__).resolve().parents[1]
QS = [json.loads(l) for l in (ROOT / "tests/t2c.jsonl").read_text(encoding="utf-8").splitlines()]


def test_set():
    assert len(QS) >= 10 and all(q["gold_answer"] is not None for q in QS)


def test_gold_reproducible():
    for q in QS: assert t2c.execute(q["gold_query"], limit=False)["canon"] == q["gold_answer"], q["id"]


@pytest.mark.parametrize("q", ["CREATE (:X)", "MATCH (n) DETACH DELETE n", "MATCH (n) SET n.a = 1 RETURN n", "CALL db.labels()"])
def test_static_filter_blocks_writes(q):
    assert not t2c.check_safe(q)[0]


def test_ro_query_rejects_write_server_side():
    with pytest.raises(Exception):
        gdb.graph().ro_query("CREATE (:Hack)")
    assert gdb.graph().ro_query("MATCH (n:Hack) RETURN count(n)").result_set[0][0] == 0


def test_schema_check():
    assert t2c.check_schema("MATCH (v:Variant) RETURN v.id")[0]
    ok, bad = t2c.check_schema("MATCH (v:Mutation) RETURN v.qualityScore")
    assert not ok and len(bad) == 2


def test_with_limit_handles_trailing_semicolons():
    assert t2c.with_limit("MATCH (n) RETURN n.name;").endswith("LIMIT 100")
    assert t2c.with_limit("MATCH (n) RETURN n.name LIMIT 5;").endswith("LIMIT 5;")


def test_limit():
    assert t2c.with_limit("MATCH (n) RETURN n.name").endswith("LIMIT 100")
    assert t2c.with_limit("MATCH (n) RETURN n.name LIMIT 5").endswith("LIMIT 5")
    assert len(t2c.execute("MATCH (n) RETURN n.name", True)["canon"]) == 100


def test_eval_files():
    for r in ("r1", "r2"):
        rows = json.loads((ROOT / f"llm_log/eval_t2c_{r}.json").read_text(encoding="utf-8"))
        assert len(rows) == len(QS) and sum(not x["result_ok"] for x in rows) >= 1
