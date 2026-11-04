"""Імпорт у граф: схема (обмеження+індекси) → LOAD CSV/MERGE → підрахунок → повторний імпорт (ідемпотентність) → порушення обмеження.
Результат: docs/import_log.md, docs/evidence/import.json."""
import json
import re
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import graphdb as gdb  # noqa: E402

ROOT = gdb.ROOT
UNI = [("Variant", "id"), ("Gene", "symbol"), ("Person", "name"), ("Annotation", "id"), ("Sample", "code"), ("Threshold", "id")]
IDX = [("Annotation", "name"), ("Annotation", "value"), ("Variant", "type"), ("Person", "ageYears")]


def statements(path):
    txt = "\n".join(l for l in Path(path).read_text(encoding="utf-8").splitlines() if not l.strip().startswith("//"))
    return [s.strip() for s in txt.split(";") if s.strip()]


def counts():
    g = gdb.graph()
    c = {"nodes": g.ro_query("MATCH (n) RETURN count(n)").result_set[0][0], "rels": g.ro_query("MATCH ()-[r]->() RETURN count(r)").result_set[0][0]}
    c["by_label"] = {r[0]: r[1] for r in g.ro_query("MATCH (n) RETURN labels(n)[0], count(n) ORDER BY labels(n)[0]").result_set}
    c["by_type"] = {r[0]: r[1] for r in g.ro_query("MATCH ()-[r]->() RETURN type(r), count(r) ORDER BY type(r)").result_set}
    return c


def schema():
    g = gdb.graph()
    for l, p in UNI: g.create_node_range_index(l, p)
    for l, p in IDX: g.create_node_range_index(l, p)
    for l, p in UNI: g.create_node_unique_constraint(l, p)
    for _ in range(50):
        cs = g.ro_query("CALL db.constraints()").result_set
        if len(cs) == len(UNI) and all(r[4] == "OPERATIONAL" for r in cs): break
        time.sleep(0.2)
    return cs, g.ro_query("CALL db.indexes()").result_set


def load():
    t = time.perf_counter()
    for f in ("01_nodes.cypher", "02_rels.cypher"):
        for s in statements(ROOT / "import" / f): gdb.run(s)
    return round((time.perf_counter() - t) * 1000)


def main():
    gdb.reset(); gdb.stage_csv()
    cs, ix = schema()
    ms1 = load(); c1 = counts()
    ms2 = load(); c2 = counts()
    # порушення обмежень
    viol = {}
    for name, q in (("Variant.id", "CREATE (:Variant {id: 'VAR-001', type: 'SNP'})"), ("Gene.symbol", "CREATE (:Gene {symbol: 'BRCA1'})")):
        try: gdb.run(q); viol[name] = {"query": q, "error": "(помилки немає — обмеження не спрацювало!)"}
        except Exception as e: viol[name] = {"query": q, "error": str(e)}
    c3 = counts()
    ev = {"loaded": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "first": c1, "second": c2, "ms_first": ms1, "ms_second": ms2, "identical": c1 == c2, "after_violation": {"nodes": c3["nodes"], "rels": c3["rels"]},
          "constraints": [[r[0], r[1], r[2], r[3], r[4]] for r in cs], "indexes": [[r[0], list(r[1]), list(r[2].values())[0] if isinstance(r[2], dict) else r[2], r[6], r[7]] for r in ix], "violation": viol}
    (ROOT / "docs/evidence").mkdir(parents=True, exist_ok=True)
    (ROOT / "docs/evidence/import.json").write_text(json.dumps(ev, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    L = ["# Журнал імпорту (Результат 2)", "", f"- Дата: {ev['loaded']} (UTC)", "- Рушій: FalkorDB (вбудований, falkordblite 0.11.0) — не Neo4j; див. README.", "- Імпорт: `import/01_nodes.cypher`, `import/02_rels.cypher` (LOAD CSV + MERGE), CSV — `data/*.csv`.", "",
         f"## Кількості (перший імпорт, {ms1} мс)", "", f"Вузлів: **{c1['nodes']}**, зв'язків: **{c1['rels']}**.", "", "| Мітка | Вузлів |", "|---|---|"] + [f"| {k} | {v} |" for k, v in c1["by_label"].items()] + ["", "| Тип зв'язку | Кількість |", "|---|---|"] + [f"| {k} | {v} |" for k, v in c1["by_type"].items()]
    L += ["", f"## Ідемпотентність (повторний імпорт, {ms2} мс)", "", f"Після другого запуску: вузлів {c2['nodes']}, зв'язків {c2['rels']}; розбивка за мітками й типами **{'збігається' if ev['identical'] else 'НЕ збігається'}** з першою.", "",
          "## Обмеження (`CALL db.constraints()`, аналог `SHOW CONSTRAINTS`)", "", "| Тип | Мітка | Властивості | Об'єкт | Стан |", "|---|---|---|---|---|"] + [f"| {r[0]} | {r[1]} | {', '.join(r[2])} | {r[3]} | {r[4]} |" for r in cs]
    L += ["", "## Індекси (`CALL db.indexes()`, аналог `SHOW INDEXES`)", "", "| Мітка | Властивості | Тип | Стан |", "|---|---|---|---|"] + [f"| {r[0]} | {', '.join(r[1])} | {r[2]} | {r[4]} |" for r in ev["indexes"]]
    L += ["", "## Порушення обмеження", ""]
    for k, v in viol.items(): L += [f"`{v['query']}`", "", f"Відповідь сервера: `{v['error']}`", ""]
    L += [f"Після спроб порушення граф не змінився: {c3['nodes']} вузлів, {c3['rels']} зв'язків."]
    (ROOT / "docs/import_log.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print(json.dumps({"c1": [c1["nodes"], c1["rels"]], "c2": [c2["nodes"], c2["rels"]], "identical": ev["identical"], "constraints": len(cs), "indexes": len(ix), "viol": {k: v["error"][:100] for k, v in viol.items()}, "ms": [ms1, ms2]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
