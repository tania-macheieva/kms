"""Перевірка схеми models/rules.json та перелік винятків окремою таблицею.

Запуск: python scripts/validate_rules.py [rules.json]   (код виходу 1 — є порушення схеми)
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from models.frames import input_slots                      # noqa: E402

OPS = {"exists", "missing", "empty", "nonempty", "==", "!=", "<", "<=", ">", ">=", "in", "not_in", "contains"}
NO_VALUE = {"exists", "missing", "empty", "nonempty"}
STATUSES = {"verified", "draft"}


def check_cond(c, where, errs):
    if not isinstance(c, dict) or "fact" not in c or "op" not in c:
        errs.append(f"{where}: умова без fact/op"); return
    if c["op"] not in OPS:
        errs.append(f"{where}: невідома операція {c['op']}")
    if c["op"] not in NO_VALUE and "value" not in c:
        errs.append(f"{where}: немає value")
    if c["op"] in ("in", "not_in") and not isinstance(c.get("value"), list):
        errs.append(f"{where}: для in/not_in value має бути списком")


def validate(doc):
    errs, ids = [], set()
    for r in doc["rules"]:
        rid = r.get("id", "?")
        for key in ("id", "if", "then", "exception", "source_quote", "status"):
            if key not in r:
                errs.append(f"{rid}: немає поля {key}")
        if rid in ids:
            errs.append(f"{rid}: дубльований id")
        ids.add(rid)
        if not r.get("if"):
            errs.append(f"{rid}: порожній if")
        if not r.get("then"):
            errs.append(f"{rid}: порожній then")
        for i, c in enumerate(r.get("if", [])):
            check_cond(c, f"{rid}.if[{i}]", errs)
        for i, c in enumerate(r.get("exception", [])):
            check_cond(c, f"{rid}.exception[{i}]", errs)
        for i, e in enumerate(r.get("then", [])):
            if ("set" in e) == ("add" in e) or "value" not in e:
                errs.append(f"{rid}.then[{i}]: потрібно рівно одне з set/add і value")
        if r.get("status") not in STATUSES:
            errs.append(f"{rid}: статус має бути verified|draft")
        if r.get("status") == "verified" and not r.get("source_quote"):
            errs.append(f"{rid}: verified без цитати")
        if r.get("status") == "draft" and r.get("source_quote"):
            errs.append(f"{rid}: draft із цитатою (має бути verified)")
        if r.get("source_quote") and r.get("source") not in doc["sources"]:
            errs.append(f"{rid}: невідоме джерело {r.get('source')}")
    return errs


def main():
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "models" / "rules.json"
    doc = json.loads(path.read_text(encoding="utf-8"))
    errs = validate(doc)
    slots = input_slots()
    derived = {e.get("set") or e.get("add") for r in doc["rules"] for e in r["then"]}
    print(f"Схема {path.name}: правил {len(doc['rules'])}, порушень {len(errs)}")
    for e in errs:
        print("  ПОМИЛКА", e)
    unknown = sorted({c["fact"] for r in doc["rules"] for c in r["if"] + r["exception"]} - slots - derived)
    print(f"Факти в умовах, яких немає ні у слотах фреймів, ні серед виведених: {unknown or 'немає'}")
    print("\nПерелік винятків (окремо від правил):")
    print(f"{'id':5} {'виняток (правило НЕ спрацьовує, якщо всі умови істинні)':62} джерело/примітка")
    for r in doc["rules"]:
        if r["exception"]:
            from engine.engine import fmt_cond
            print(f"{r['id']:5} {' & '.join(fmt_cond(c) for c in r['exception']):62} {r.get('note', '')[:60]}")
    n = sum(1 for r in doc["rules"] if r["exception"])
    print(f"\nПравил із винятками: {n}")
    sys.exit(1 if errs or unknown else 0)


if __name__ == "__main__":
    main()
