"""Рушій продукційних правил IF–THEN із прямим ланцюжкуванням.

Алгоритм (forward chaining):
  1. Робоча пам'ять = вхідні факти (`frame.slot` → значення).
  2. Порядок: на кожному циклі формується порядок застосовних правил — усі умови `if` істинні, жоден виняток
     (`exception`) не спрацьовує, правило ще не виконувалось.
  3. Стратегія розв'язання конфліктів: пріоритет (більший виграє), далі специфічність (більше умов — виграє),
     далі id (для детермінованості). Виконується одне найкраще правило, потім порядок перераховується.
  4. Висновки: `set` — присвоїти значення слоту; `add` — додати значення до списку. Якщо два правила присвоюють
     різні значення одному слоту, перемагає правило з вищим рангом (пріоритет, специфічність); рівні ранги —
     це нерозв'язаний конфлікт: лишається значення першого виконаного правила, конфлікт фіксується.
  5. Цикл триває, доки не з'являться нові застосовні правила (виведені факти можуть запускати інші правила).
  6. Для кожного висновку зберігається ланцюжок правил (explain).

Правила зі статусом draft (без цитати) за замовчуванням НЕ завантажуються: правило G08 спирається на відсутність
прапорців, а в монотонному прямому ланцюжку «відсутнє» ще не означає «не буде виведене» (див. пастку T3 в analysis).

Документований недолік: рушій монотонний, тому якщо вище за рангом правило перезаписує значення слота, правила,
що вже спиралися на старе значення, не відкочуються (див. docs/rules_analysis.md).
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_RULES = ROOT / "models" / "rules.json"


def _num(x: Any) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def eval_condition(cond: Dict[str, Any], facts: Dict[str, Any]) -> bool:
    """Істинність однієї умови. Відсутній факт робить умову хибною (крім exists/missing/empty)."""
    fact, op, val = cond["fact"], cond["op"], cond.get("value")
    present = fact in facts and facts[fact] is not None
    actual = facts.get(fact)
    if op == "exists":
        return present
    if op == "missing":
        return not present
    if op == "empty":
        return (not present) or actual == [] or actual == ""
    if op == "nonempty":
        return present and actual != [] and actual != ""
    if not present:
        return False
    if op in ("==", "!="):
        same = (isinstance(actual, bool) == isinstance(val, bool)) and actual == val
        return same if op == "==" else not same
    if op in ("<", "<=", ">", ">="):
        if not (_num(actual) and _num(val)):
            return False
        return {"<": actual < val, "<=": actual <= val, ">": actual > val, ">=": actual >= val}[op]
    if op == "in":
        return actual in val
    if op == "not_in":
        return actual not in val
    if op == "contains":
        return isinstance(actual, (list, tuple, set)) and val in actual
    raise ValueError(f"Невідома операція: {op}")


@dataclass
class Rule:
    id: str
    title: str
    group: str
    conds: List[Dict[str, Any]]
    thens: List[Dict[str, Any]]
    exception: List[Dict[str, Any]]
    priority: int
    status: str
    quote: str
    source: Optional[str]

    @property
    def specificity(self) -> int:
        return len(self.conds)

    @property
    def rank(self):
        return (self.priority, self.specificity)

    def matches(self, facts) -> bool:
        return all(eval_condition(c, facts) for c in self.conds)

    def excepted(self, facts) -> bool:
        return bool(self.exception) and all(eval_condition(c, facts) for c in self.exception)


def load_rules(path=DEFAULT_RULES, include_draft: bool = False) -> List[Rule]:
    doc = json.loads(Path(path).read_text(encoding="utf-8"))
    rules = []
    for r in doc["rules"]:
        if r["status"] == "draft" and not include_draft:
            continue
        rules.append(Rule(r["id"], r.get("title", ""), r.get("group", ""), r["if"], r["then"], r.get("exception", []),
                          r.get("priority", 5), r["status"], r.get("source_quote", ""), r.get("source")))
    return rules


def fmt_cond(c: Dict[str, Any]) -> str:
    v = c.get("value")
    return f"{c['fact']} {c['op']}" + ("" if c["op"] in ("exists", "missing", "empty", "nonempty") else f" {v!r}")


@dataclass
class Result:
    facts: Dict[str, Any]
    given: set
    trace: List[Dict[str, Any]] = field(default_factory=list)
    conflicts: List[Dict[str, Any]] = field(default_factory=list)

    @property
    def fired(self) -> List[str]:
        return [t["rule"] for t in self.trace]

    @property
    def derived(self) -> Dict[str, Any]:
        return {k: v for k, v in self.facts.items() if k not in self.given}

    @property
    def unresolved_conflicts(self):
        return [c for c in self.conflicts if not c["resolved"]]


class Engine:
    def __init__(self, rules: List[Rule]):
        self.rules = rules

    @classmethod
    def from_file(cls, path=DEFAULT_RULES, include_draft: bool = False) -> "Engine":
        return cls(load_rules(path, include_draft))

    # --------------------------------------------------------------- виведення
    def run(self, facts: Dict[str, Any]) -> Result:
        wm = {k: (list(v) if isinstance(v, list) else v) for k, v in facts.items()}
        res = Result(facts=wm, given=set(facts))
        owner: Dict[str, tuple] = {}                       # слот → (id правила, ранг) для розв'язання конфліктів
        done = set()
        for cycle in range(1, 1000):
            agenda = [r for r in self.rules if r.id not in done and r.matches(wm) and not r.excepted(wm)]
            if not agenda:
                break
            agenda.sort(key=lambda r: (-r.priority, -r.specificity, r.id))   # стратегія конфліктів
            rule = agenda[0]
            done.add(rule.id)
            entry = {"rule": rule.id, "title": rule.title, "cycle": cycle, "quote": rule.quote,
                     "competing": [r.id for r in agenda[1:]],
                     "matched": [{"cond": fmt_cond(c), "fact": c["fact"], "actual": wm.get(c["fact"])} for c in rule.conds],
                     "effects": []}
            for eff in rule.thens:
                entry["effects"].append(self._apply(rule, eff, wm, res, owner))
            res.trace.append(entry)
        return res

    def _apply(self, rule: Rule, eff: Dict[str, Any], wm, res: Result, owner) -> Dict[str, Any]:
        if "add" in eff:
            slot, value = eff["add"], eff["value"]
            lst = wm.setdefault(slot, [])
            applied = value not in lst
            if applied:
                lst.append(value)
            return {"op": "add", "fact": slot, "value": value, "applied": applied}
        slot, value = eff["set"], eff["value"]
        if slot in res.given:
            # вхідний факт не перезаписується, але розбіжність між входом і висновком правила потребує людини
            res.conflicts.append({"fact": slot, "rule": rule.id, "value": value, "given": wm.get(slot),
                                  "kind": "розбіжність: вхідний факт суперечить висновку правила", "resolved": False})
            return {"op": "set", "fact": slot, "value": value, "applied": False}
        if slot in owner and wm.get(slot) != value:
            old_rule, old_rank = owner[slot]
            if rule.rank > old_rank:                       # новіше правило сильніше → перезапис
                wm[slot] = value
                owner[slot] = (rule.id, rule.rank)
                res.conflicts.append({"fact": slot, "winner": rule.id, "loser": old_rule, "resolved": True,
                                      "kind": f"вищий ранг {rule.rank} проти {old_rank}"})
                return {"op": "set", "fact": slot, "value": value, "applied": True}
            tie = rule.rank == old_rank
            res.conflicts.append({"fact": slot, "winner": old_rule, "loser": rule.id, "resolved": not tie,
                                  "kind": "рівні ранги: лишається перше виконане правило" if tie
                                  else f"нижчий ранг {rule.rank} проти {old_rank}"})
            return {"op": "set", "fact": slot, "value": value, "applied": False}
        wm[slot] = value
        owner[slot] = (rule.id, rule.rank)
        return {"op": "set", "fact": slot, "value": value, "applied": True}

    # --------------------------------------------------------------- пояснення
    def explain(self, res: Result, fact: str, _depth: int = 0, _seen: Optional[set] = None) -> str:
        """Текстовий ланцюжок правил, що привів до значення факту (рекурсивно по виведених умовах)."""
        seen = _seen if _seen is not None else set()
        pad = "    " * _depth
        if fact not in res.facts:
            return f"{pad}{fact}: не виведено (жодне правило не спрацювало)"
        value = res.facts[fact]
        producers = [t for t in res.trace if any(e["fact"] == fact and e["applied"] for e in t["effects"])]
        if not producers:
            return f"{pad}{fact} = {value!r}  [вхідний факт]" if fact in res.given else f"{pad}{fact} = {value!r}"
        lines = [f"{pad}{fact} = {value!r}"]
        for t in producers:
            lines.append(f"{pad}  ← правило {t['rule']} «{t['title']}» (цикл {t['cycle']})")
            for m in t["matched"]:
                lines.append(f"{pad}      умова: {m['cond']}   [{m['fact']} = {m['actual']!r}]")
                if m["fact"] in res.facts and m["fact"] not in res.given and m["fact"] not in seen:
                    seen.add(m["fact"])
                    lines.append(self.explain(res, m["fact"], _depth + 2, seen))
            if t["quote"]:
                lines.append(f"{pad}      джерело: «{t['quote'][:110]}{'…' if len(t['quote']) > 110 else ''}»")
        return "\n".join(lines)


def run_demo() -> str:
    """Три приклади з поясненням ланцюжка (використовуються у звіті)."""
    cases = [
        ("1. SNP на екзонному кінці: тільки LowFS → не відкидати, а на перегляд",
         {"variant.variant_type": "SNP", "variant.QD": 18.0, "variant.FS": 72.5, "variant.SOR": 2.2, "variant.MQ": 58.0,
          "variant.at_exon_end": True}, ["variant.filter_status", "variant.filter_scope"], False),
        ("2. Рідний брат пробанда з BRCA1: від ризику до рекомендації",
         {"proband.variant_gene": "BRCA1", "proband.variant_known": True, "relative.relationship": "full_sibling",
          "relative.age": 52, "relative.available": True, "relative.wants_testing": True},
         ["relative.inheritance_chance", "relative.recommendation"], True),
        ("3. Мала панель із великим набором варіантів: конфлікт методів розв'язано пріоритетом",
         {"dataset.dataset_type": "small_gene_panel", "dataset.large_variant_set": True,
          "dataset.has_curated_known_variants": True}, ["dataset.filtering_method"], False),
    ]
    out = []
    for title, facts, targets, draft in cases:
        eng = Engine.from_file(include_draft=draft)       # чернетки (draft) за замовчуванням вимкнені
        res = eng.run(facts)
        out.append(f"=== {title}" + ("  [із чернетковими правилами]" if draft else ""))
        for t in targets:
            out.append(eng.explain(res, t))
        for c in res.conflicts:
            out.append(f"  [конфлікт] {c}")
        out.append("")
    return "\n".join(out)


if __name__ == "__main__":
    print(run_demo())
