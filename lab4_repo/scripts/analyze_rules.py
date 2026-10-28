"""Статичний аналіз бази правил: надлишкові, суперечливі та недосяжні правила.

Метод. Для кожного факту береться скінченна множина «критичних» значень: усі пороги з правил, значення між ними,
значення за межами, усі згадані категорії, «інше» та «відсутнє» (None). Двох правил (або одного) достатньо перевірити
на всіх комбінаціях цих значень для фактів, що в них фігурують, — для порогових умов такий перебір повний.
Правило «активне» на наборі фактів, якщо всі його умови істинні й виняток не спрацьовує.

  • надлишкове:   правило A активне ⇒ активне й B, і обидва роблять той самий висновок (A зайве або повторює B);
  • суперечливе:  правила разом активні, але встановлюють (set) різні значення одному слоту;
                  фіксується, чи розв'язує це стратегія рушія (різний пріоритет/специфічність) чи ні (рівні ранги);
  • недосяжне:    умови (або виняток) ніколи не можуть бути істинними, або умова спирається на виведений факт/значення,
                  яке жодне правило не виробляє.

Обмеження: виведені факти розглядаються як вільні змінні (перебір надмірний), а час виконання (порядок спрацювання)
не моделюється — такі дефекти ловить лише динамічний тест (див. docs/rules_analysis.md, пастка 3).

Запуск: python scripts/analyze_rules.py [rules.json] [--draft]
"""
import itertools
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from engine.engine import eval_condition, fmt_cond, load_rules   # noqa: E402
from models.frames import input_slots                           # noqa: E402


def _is_num(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def candidates(rules):
    """fact → список критичних значень."""
    mentioned = {}
    for r in rules:
        for c in r.conds + r.exception:
            mentioned.setdefault(c["fact"], []).append(c)
        for e in r.thens:                                  # значення, які правила можуть виробляти, теж критичні
            op = "contains" if "add" in e else "=="
            mentioned.setdefault(e.get("set") or e.get("add"), []).append({"fact": "", "op": op, "value": e["value"], "_eff": True})
    cand = {}
    for fact, conds in mentioned.items():
        nums = sorted({c["value"] for c in conds if _is_num(c.get("value"))})
        conds = [c for c in conds]
        lists = [c["value"] for c in conds if isinstance(c.get("value"), list) and c["op"] in ("==", "!=")]
        listy = any(c["op"] in ("empty", "nonempty", "contains") for c in conds) or any(
            isinstance(c.get("value"), list) and c["op"] in ("==", "!=") for c in conds)
        vals = [None]
        if nums:
            vals += [nums[0] - 1, *nums, nums[-1] + 1] + [(a + b) / 2 for a, b in zip(nums, nums[1:])]
        if listy:
            items = {x for c in conds if c["op"] == "contains" for x in [c["value"]]}
            for l in lists:
                items.update(l)
            vals += [[]] + [list(l) for l in lists] + [[i] for i in sorted(items)] + ([sorted(items)] if len(items) > 1 else [])
        else:
            cats = []
            for c in conds:
                v = c.get("value")
                if c["op"] in ("in", "not_in"):
                    cats += list(v)
                elif v is not None and not _is_num(v):
                    cats.append(v)
            vals += list(dict.fromkeys(cats)) + ["__інше__"]
        if not nums and not listy and not any(isinstance(v, bool) for v in vals if v is not None) and not conds:
            vals += ["__інше__"]
        cand[fact] = vals
    return cand


def assignments(facts, cand):
    names = sorted(facts)
    for combo in itertools.product(*(cand[f] for f in names)):
        yield {n: v for n, v in zip(names, combo) if v is not None}


def active(rule, wm):
    return rule.matches(wm) and not rule.excepted(wm)


def rule_facts(*rules):
    return {c["fact"] for r in rules for c in r.conds + r.exception}


def effect_key(rule):
    return {(("set" if "set" in e else "add"), e.get("set") or e.get("add"), json.dumps(e["value"])) for e in rule.thens}


def analyze(rules, slots):
    cand = candidates(rules)
    out = {"redundant": [], "contradictory": [], "unreachable": []}
    # --- недосяжні
    produced = {}
    for r in rules:
        for e in r.thens:
            produced.setdefault(e.get("set") or e.get("add"), []).append(e)
    for r in rules:
        sat = any(r.matches(wm) for wm in assignments(rule_facts(r) & {c["fact"] for c in r.conds}, cand))
        if not sat:
            out["unreachable"].append((r.id, "умови ніколи не виконуються разом"))
        if r.exception and not any(all(eval_condition(c, wm) for c in r.exception)
                                   for wm in assignments({c["fact"] for c in r.exception}, cand)):
            out["unreachable"].append((r.id, "виняток ніколи не спрацьовує (зайвий виняток)"))
        for c in r.conds:
            f = c["fact"]
            if f in slots:
                continue
            effs = produced.get(f)
            if not effs:
                out["unreachable"].append((r.id, f"умова {fmt_cond(c)}: факт {f} не вхідний і ніким не виробляється"))
                continue
            if c["op"] in ("==", "in") and all("set" in e for e in effs):
                vals = [e["value"] for e in effs]
                if not any(eval_condition(c, {f: v}) for v in vals):
                    out["unreachable"].append((r.id, f"умова {fmt_cond(c)}: жодне правило не встановлює таке значення"))
    # --- пари
    for a, b in itertools.permutations(rules, 2):
        facts = {c["fact"] for c in a.conds + a.exception + b.conds + b.exception}
        if a.id < b.id or True:
            pass
        # надлишковість: A ⇒ B і однаковий висновок
        if effect_key(a) == effect_key(b):
            sat_a = [wm for wm in assignments(facts, cand) if active(a, wm)]
            if sat_a and all(active(b, wm) for wm in sat_a):
                same = all(active(a, wm) == active(b, wm) for wm in assignments(facts, cand))
                out["redundant"].append((a.id, b.id, "дублікати" if same else "A зайве: усі його випадки вже покриває B"))
    for a, b in itertools.combinations(rules, 2):
        facts = {c["fact"] for c in a.conds + a.exception + b.conds + b.exception}
        both = [wm for wm in assignments(facts, cand) if active(a, wm) and active(b, wm)]
        if not both:
            continue
        for ea in a.thens:
            for eb in b.thens:
                if "set" in ea and "set" in eb and ea["set"] == eb["set"] and ea["value"] != eb["value"]:
                    if a.priority != b.priority or a.specificity != b.specificity:
                        how = f"розв'язує стратегія: ранги {a.id}={a.rank}, {b.id}={b.rank}"
                        if a.priority == b.priority:
                            how += " (лише за специфічністю — неявно!)"
                        resolved = True
                    else:
                        how, resolved = f"НЕ розв'язано: рівні ранги {a.rank}", False
                    out["contradictory"].append((a.id, b.id, ea["set"], ea["value"], eb["value"], resolved, how))
    return out


def report(path, include_draft=False):
    rules = load_rules(path, include_draft)
    res = analyze(rules, input_slots())
    lines = [f"Аналіз: {Path(path).name} (правил: {len(rules)}{', разом із draft' if include_draft else ''})", ""]
    lines.append(f"[1] Надлишкові правила: {len(res['redundant'])}")
    for a, b, why in res["redundant"]:
        lines.append(f"    {a} ⊆ {b}: {why}")
    lines.append(f"[2] Суперечливі пари (різні set в один слот): {len(res['contradictory'])}")
    for a, b, slot, va, vb, resolved, how in res["contradictory"]:
        lines.append(f"    {a} / {b}: {slot} = {va!r} проти {vb!r} — {how}")
    lines.append(f"[3] Недосяжні правила / винятки: {len(res['unreachable'])}")
    for rid, why in res["unreachable"]:
        lines.append(f"    {rid}: {why}")
    total = len(res["redundant"]) + len(res["contradictory"]) + len(res["unreachable"])
    lines.append(f"\nУсього знахідок: {total}")
    return "\n".join(lines), res


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    path = args[0] if args else ROOT / "models" / "rules.json"
    text, _ = report(path, "--draft" in sys.argv)
    print(text)
