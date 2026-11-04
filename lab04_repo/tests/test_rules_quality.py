import json
import subprocess
import sys

import pytest

from engine.engine import ROOT, Engine, load_rules
from scripts.analyze_rules import analyze
from scripts.validate_rules import validate
from scripts.verify_quotes import verify
from models.frames import input_slots
from engine.engine import Rule


def test_rules_schema_valid(rules_path):
    doc = json.loads(open(rules_path, encoding="utf-8").read())
    assert validate(doc) == []
    assert len(doc["rules"]) >= 20


def test_at_least_ten_quotes_found_in_sources(rules_path):
    rows = verify(__import__("pathlib").Path(rules_path))
    found = [r for r in rows if r[2] == "FOUND"]
    assert len(found) >= 10 and all(r[4] for r in rows)         # знайдені цитати та правильні статуси


def test_rules_without_quote_are_draft(rules_path):
    doc = json.loads(open(rules_path, encoding="utf-8").read())
    assert all(r["status"] == "draft" for r in doc["rules"] if not r["source_quote"])


def test_at_least_three_rules_with_exceptions(rules_path):
    assert sum(1 for r in load_rules(rules_path) if r.exception) >= 3


def test_analyzer_detects_synthetic_defects():
    def R(id, conds, thens, exc=(), prio=5):
        return Rule(id, "", "", conds, thens, list(exc), prio, "verified", "", None)
    c = lambda f, op, v=None: {"fact": f, "op": op, "value": v}
    rules = [
        R("A", [c("x.n", ">", 10)], [{"add": "x.flag", "value": "hi"}]),
        R("B", [c("x.n", ">", 5)], [{"add": "x.flag", "value": "hi"}]),                         # A зайве
        R("C", [c("x.n", ">", 1)], [{"set": "x.s", "value": "a"}]),
        R("D", [c("x.n", ">", 2)], [{"set": "x.s", "value": "b"}]),                             # те саме, інше значення
        R("E", [c("x.n", ">", 5), c("x.n", "<", 3)], [{"set": "x.t", "value": 1}]),              # недосяжне
        R("F", [c("x.derived", "==", 7)], [{"set": "x.u", "value": 1}]),                         # ніхто не виробляє
    ]
    out = analyze(rules, {"x.n"})
    assert ("A", "B", "A зайве: усі його випадки вже покриває B") in out["redundant"]
    assert any({a, b} == {"C", "D"} and not resolved for a, b, *_, resolved, _ in out["contradictory"])
    ids = {r for r, _ in out["unreachable"]}
    assert {"E", "F"} <= ids


def test_final_rules_have_no_unresolved_static_conflicts():
    rules = load_rules(ROOT / "models" / "rules.json")
    out = analyze(rules, input_slots())
    assert not out["redundant"] and not out["unreachable"]
    assert all(resolved for *_, resolved, _ in out["contradictory"])
