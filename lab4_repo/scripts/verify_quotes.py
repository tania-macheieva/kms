"""Перевірка цитат: чи міститься source_quote кожного правила у тексті джерела.

Запуск:  python scripts/verify_quotes.py [шлях/до/rules.json]
Код виходу 0 — усе гаразд; 1 — є правило з непідтвердженою цитатою або правило без цитати зі статусом verified.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def normalize(text: str) -> str:
    """Нормалізація, що нівелює переноси рядків і типографські відмінності."""
    text = text.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    text = text.replace("–", "-").replace("—", "-")
    return re.sub(r"\s+", " ", text).strip()


def verify(rules_path: Path):
    doc = json.loads(rules_path.read_text(encoding="utf-8"))
    sources = {k: normalize((ROOT / v).read_text(encoding="utf-8")) for k, v in doc["sources"].items()}
    rows = []
    for r in doc["rules"]:
        quote = r.get("source_quote", "")
        if not quote:
            rows.append((r["id"], r["status"], "NO_QUOTE", "—", r["status"] == "draft"))
            continue
        found = normalize(quote) in sources.get(r.get("source"), "")
        rows.append((r["id"], r["status"], "FOUND" if found else "NOT_FOUND", r.get("source"),
                     found and r["status"] == "verified" or (not found and r["status"] == "draft")))
    return rows


def main():
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "models" / "rules.json"
    rows = verify(path)
    print(f"Перевірка цитат: {path.relative_to(ROOT) if path.is_absolute() and ROOT in path.parents else path}")
    print(f"{'id':5} {'status':9} {'quote':10} source  ok")
    for rid, status, q, src, ok in rows:
        print(f"{rid:5} {status:9} {q:10} {src:6}  {'OK' if ok else 'ПОМИЛКА'}")
    found = sum(1 for r in rows if r[2] == "FOUND")
    noq = sum(1 for r in rows if r[2] == "NO_QUOTE")
    bad = sum(1 for r in rows if not r[4])
    print(f"\nУсього правил: {len(rows)}; цитата знайдена: {found}; без цитати (draft): {noq}; невідповідностей: {bad}")
    print(f"Частка правил із підтвердженою цитатою: {found / len(rows):.0%}")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
