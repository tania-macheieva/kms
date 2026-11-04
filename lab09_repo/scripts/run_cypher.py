"""Виконує queries/c*.cypher (read-only), міряє час (медіана 5 після прогріву), зберігає queries/results/results.json
і формує docs/cypher_results.md за queries/meta.json та queries/results/manual_verification.json (якщо є)."""
import json
import statistics
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import graphdb as gdb  # noqa: E402

ROOT = gdb.ROOT


def cell(x):
    if isinstance(x, float): return f"{x:.6g}"
    if isinstance(x, list): return "[" + ", ".join(cell(i) for i in x) + "]"
    return "" if x is None else str(x)


def run_all():
    out = {}
    for f in sorted((ROOT / "queries").glob("c*.cypher")):
        q = f.read_text(encoding="utf-8"); gdb.ro(q)   # прогрів
        ts = []
        for _ in range(5):
            t = time.perf_counter(); r = gdb.ro(q); ts.append(time.perf_counter() - t)
        out[f.name] = {"vars": [h[1] if isinstance(h, (list, tuple)) else h for h in r.header], "rows": [[cell(x) for x in row] for row in r.result_set], "ms_median": round(statistics.median(ts) * 1000, 2)}
    (ROOT / "queries/results").mkdir(exist_ok=True)
    (ROOT / "queries/results/results.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    return out


def table(vs, rows, limit=15):
    s = "| " + " | ".join(vs) + " |\n|" + "---|" * len(vs) + "\n" + "".join("| " + " | ".join(c or "∅" for c in r) + " |\n" for r in rows[:limit])
    return s + (f"\n_(показано {limit} з {len(rows)} рядків)_\n" if len(rows) > limit else "")


def write_doc(out):
    meta = json.loads((ROOT / "queries/meta.json").read_text(encoding="utf-8"))
    mp = ROOT / "queries/results/manual_verification.json"; man = json.loads(mp.read_text(encoding="utf-8")) if mp.exists() else {}
    L = ["# Результат 3. Запити Cypher та їхні результати", "",
         "Рушій: FalkorDB (вбудований); запити виконуються лише через read-only виклик. Запити написано в діалекті, спільному з Neo4j 5, окрім двох відмінностей: `shortestPath` у FalkorDB дозволений лише в `RETURN`/`WITH` і лише спрямований. Час — медіана 5 запусків після прогріву (перший виклик запиту суттєво повільніший). Результати генерує `scripts/run_cypher.py`.", "",
         "| Запит | Конструкції | CQ | Рядків | мс |", "|---|---|---|---|---|"]
    L += [f"| {k.replace('.cypher','')} | {meta[k]['types']} | {meta[k]['cq']} | {len(v['rows'])} | {v['ms_median']} |" for k, v in out.items()] + [""]
    for i, (name, r) in enumerate(out.items(), 1):
        mt = meta[name]
        L += [f"## {i}. `{name}` — {mt['types']}", "", f"**CQ:** {mt['cq']} — {mt['cqtext']}", "", "```cypher", (ROOT / "queries" / name).read_text(encoding="utf-8").strip(), "```", "", "**Результат:**", "", table(r["vars"], r["rows"]), f"**Час:** {r['ms_median']} мс", "", f"**Інтерпретація:** {mt['interp']}", ""]
    L += ["## Ручна перевірка", "", "Результати шести запитів звірено з незалежним обчисленням звичайним Python-кодом по CSV-файлах (без Cypher і без бази) — `scripts/verify_manual.py`; для c05 і c06 додатково — ручний розбір малого підграфа (родина з 8 осіб, 8 зв'язків HAS_PARENT і 3 HAS_SIBLING).", "", "| Запит | Спосіб | Збіг |", "|---|---|---|"]
    L += [f"| {k} | {v['how']} | {'так' if v['match'] else 'НІ'} |" for k, v in man.items()]
    L += ["", "**Ручний розбір c05 (мала родина).** Рядки CSV: HAS_PARENT — Halyna→Maria, Andrii→Halyna, Iryna→Maria, Marta→Iryna, Marta→Petro, Olena→Iryna, Olena→Petro, Sofiia→Olena; HAS_SIBLING — Iryna→Halyna, Marta→Olena, Olena→Marta. Від Olena: Iryna, Petro (батьки), Marta (сестра), Sofiia (дочка) — 1 крок; Halyna (сестра Iryna) і Maria (мати Iryna) — 2 кроки; Andrii (дитина Halyna) — 3 кроки. Збігається з таблицею запиту c05.", "",
          "**Знахідка про рушій.** `toFloat()` у FalkorDB повертає значення з точністю float32 (`toFloat('1.1')` = 1.10000002384186, і тоді `a.value = 1.2` хибне). Тому в `import/*.cypher` значення округлено `round(toFloat(x)*1000)/1000`. Без цього порівняння на межі порога могли б давати хибний результат."]
    (ROOT / "docs/cypher_results.md").write_text("\n".join(L) + "\n", encoding="utf-8")


if __name__ == "__main__":
    o = run_all(); write_doc(o)
    for k, v in o.items(): print(k, len(v["rows"]), v["ms_median"])
