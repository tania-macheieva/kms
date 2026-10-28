"""Золотий набір: кожен випадок — вхідні факти й еталонний результат (за текстами джерел)."""
from engine.engine import Engine


def _same(actual, expected):
    if isinstance(expected, list):
        return isinstance(actual, list) and sorted(actual) == sorted(expected)
    return actual == expected


def test_gold_case(case, rules_path):
    eng = Engine.from_file(rules_path, include_draft=case.get("include_draft", False))
    res = eng.run(case["facts"])
    for fact, exp in case.get("expect", {}).items():
        assert fact in res.facts, f"{case['id']}: факт {fact} не виведено; спрацювали {res.fired}"
        assert _same(res.facts[fact], exp), f"{case['id']}: {fact} = {res.facts[fact]!r}, очікувалось {exp!r}; спрацювали {res.fired}"
    for fact, items in case.get("expect_contains", {}).items():
        got = res.facts.get(fact, [])
        assert all(i in got for i in items), f"{case['id']}: {fact} = {got!r}, очікувалось містить {items!r}"
    for fact in case.get("absent", []):
        assert fact not in res.facts, f"{case['id']}: {fact} = {res.facts.get(fact)!r}, але мав бути не виведений; спрацювали {res.fired}"
    for rid in case.get("fired_excludes", []):
        assert rid not in res.fired, f"{case['id']}: правило {rid} не мало спрацювати"
    for rid in case.get("fired_includes", []):
        assert rid in res.fired, f"{case['id']}: правило {rid} мало спрацювати"
    if case.get("no_rules_fire"):
        assert res.fired == [], f"{case['id']}: жодне правило не мало спрацювати, а спрацювали {res.fired}"
    if case.get("no_unresolved_conflicts"):
        assert not res.unresolved_conflicts, f"{case['id']}: нерозв'язані конфлікти {res.unresolved_conflicts}"
