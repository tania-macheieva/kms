"""Перевірка триплетів LLM: схема, цитати (V1), типи domain/range (V2), словник.

Запуск: python scripts/check_triples.py [вхід.jsonl] [--write]
Вихід: таблиця помилок за класами; з --write — models/triples_llm.jsonl (вхід + поле checks) і docs/evidence/triples_check.txt.
Класи помилок: E1 цитата не знайдена в тексті; E2 порушення domain; E3 порушення range; E4 is_a між різними типами;
E5 об'єкт — літерал, а не поняття словника; E6 s/o не зі словника; E0 помилка схеми.
"""
import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from map_tools import REL, ROOT                                    # noqa: E402

SRC = {"gatk": ROOT / "sources/gatk_hard_filtering.txt", "cdc": ROOT / "sources/cdc_cascade_testing.txt"}
TYPES = {c["label"]: c["type"] for c in json.loads((ROOT / "data/concept_types.json").read_text(encoding="utf-8"))}
REQUIRED = {"id": str, "s": str, "p": str, "o": str, "evidence": str, "source": str}


def norm(t):
    t = t.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"').replace("–", "-").replace("—", "-")
    return re.sub(r"\s+", " ", t).strip().casefold()


TEXT = {k: norm(v.read_text(encoding="utf-8")) for k, v in SRC.items()}


def check(t):
    errs = []
    for k, ty in REQUIRED.items():
        if not isinstance(t.get(k), ty) or not t.get(k):
            errs.append(("E0", f"поле {k} відсутнє або порожнє"))
    if errs:
        return errs
    if t["p"] not in REL:
        errs.append(("E0", f"відношення {t['p']} не з каталогу"))
    if t["source"] not in TEXT:
        errs.append(("E0", f"невідоме джерело {t['source']}"))
        return errs
    if norm(t["evidence"]) not in TEXT[t["source"]]:
        errs.append(("E1", "evidence не знайдено в тексті джерела"))
    s_ok, o_ok = t["s"] in TYPES, t["o"] in TYPES
    if not s_ok:
        errs.append(("E6", f"суб'єкт «{t['s']}» не зі словника"))
    if not o_ok:
        errs.append(("E5" if t["p"] == "has_example" else "E6", f"об'єкт «{t['o']}» — {'літерал' if t['p']=='has_example' else 'не зі словника'}"))
    if t["p"] in REL and s_ok and o_ok:
        r = REL[t["p"]]
        st, ot = TYPES[t["s"]], TYPES[t["o"]]
        if r.get("same_type"):
            if st != ot:
                errs.append(("E4", f"is_a між різними типами: {st} → {ot}"))
        else:
            if r["domain"] != ["*"] and st not in r["domain"]:
                errs.append(("E2", f"domain {t['p']}: {st} не дозволено"))
            if r["range"] != ["*"] and ot not in r["range"]:
                errs.append(("E3", f"range {t['p']}: {ot} не дозволено"))
    return errs


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    path = Path(args[0]) if args else ROOT / "llm_log/raw/step3_triples_llm_raw_output.jsonl"
    triples = [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]
    out, lines = [], []
    cls = Counter()
    for t in triples:
        e = check(t)
        t2 = dict(t, s_type=TYPES.get(t["s"]), o_type=TYPES.get(t["o"]), checks=[{"class": c, "message": m} for c, m in e])
        out.append(t2)
        for c, _ in e:
            cls[c] += 1
    n = len(triples)
    q_ok = sum(1 for t in out if not any(c["class"] == "E1" for c in t["checks"]))
    type_ok = sum(1 for t in out if not any(c["class"] in ("E2", "E3", "E4") for c in t["checks"]))
    clean = sum(1 for t in out if not t["checks"])
    lines.append(f"Файл: {path.name}; триплетів: {n}; за джерелами: {dict(Counter(t['source'] for t in triples))}")
    lines.append(f"Цитати знайдено в тексті: {q_ok}/{n} = {q_ok / n:.0%}")
    lines.append(f"Типи domain/range коректні: {type_ok}/{n} = {type_ok / n:.0%}")
    lines.append(f"Без жодної помилки: {clean}/{n} = {clean / n:.0%}")
    lines.append(f"Помилки за класами: {dict(sorted(cls.items()))}")
    lines.append("\nТриплети з помилками:")
    for t in out:
        for c in t["checks"]:
            lines.append(f"  {t['id']} [{c['class']}] ({t['s']}) -{t['p']}-> ({t['o']}): {c['message']}")
    rep = "\n".join(lines)
    print(rep)
    if "--write" in sys.argv:
        (ROOT / "models/triples_llm.jsonl").write_text("\n".join(json.dumps(t, ensure_ascii=False) for t in out) + "\n", encoding="utf-8")
        (ROOT / "docs/evidence").mkdir(exist_ok=True)
        (ROOT / "docs/evidence/triples_check.txt").write_text(rep + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
