"""Запускає queries/q*.rq на локальному сховищі (store/), вимірює час, зберігає результати в queries/results/results.json
і формує docs/sparql_results.md за описами з queries/meta.json. Додатково: бенчмарк «повільний vs оптимізований» (scripts/bench.py)."""
import json
import os
import statistics
import sys
import time
from pathlib import Path

os.environ["NO_PROXY"] = "127.0.0.1,localhost"; os.environ["no_proxy"] = "127.0.0.1,localhost"
sys.path.insert(0, str(Path(__file__).parent))
import mock_wikidata  # noqa: E402
import pyoxigraph as ox  # noqa: E402
from store import ROOT, open_store, query  # noqa: E402

ENDPOINT = os.environ.get("WIKIDATA_ENDPOINT", "http://127.0.0.1:8765/sparql")
SHORT = lambda t: ("<" + t.value + ">") if isinstance(t, ox.NamedNode) else (t.value if t is not None else "")


def short(t):
    if t is None: return ""
    s = str(t.value)
    return s.replace("http://example.org/dkh/onto#", "dkh:").replace("http://www.wikidata.org/entity/", "wd:").replace("http://www.w3.org/2004/02/skos/core#", "skos:")


def run(store, text, reps=5):
    times, res = [], None
    for _ in range(reps):
        t = time.perf_counter(); r = query(store, text)
        if r.__class__.__name__ == "QueryBoolean": res = {"kind": "ASK", "answer": bool(r)}
        elif r.__class__.__name__ == "QueryTriples":
            tr = sorted((short(x.subject), short(x.predicate), short(x.object)) for x in r); res = {"kind": "CONSTRUCT", "triples": tr}
        else:
            vs = [v.value for v in r.variables]; rows = [[short(s[v]) for v in vs] for s in r]; res = {"kind": "SELECT", "vars": vs, "rows": rows}
        times.append(time.perf_counter() - t)
    res["ms_median"] = round(statistics.median(times) * 1000, 2)
    return res


def main():
    srv = mock_wikidata.start(int(ENDPOINT.rsplit(":", 1)[1].split("/")[0])) if "127.0.0.1" in ENDPOINT else None
    store = open_store()
    meta = json.loads((ROOT / "queries/meta.json").read_text(encoding="utf-8"))
    out = {}
    for f in sorted((ROOT / "queries").glob("q*.rq")):
        text = f.read_text(encoding="utf-8").replace("{ENDPOINT}", ENDPOINT)
        out[f.name] = run(store, text)
        print(f.name, out[f.name]["kind"], out[f.name].get("answer", len(out[f.name].get("rows", out[f.name].get("triples", [])))), out[f.name]["ms_median"], "ms")
    (ROOT / "queries/results").mkdir(exist_ok=True)
    (ROOT / "queries/results/results.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    return out, meta


def md_table(vars_, rows, limit=15):
    s = "| " + " | ".join(vars_) + " |\n|" + "---|" * len(vars_) + "\n"
    for r in rows[:limit]: s += "| " + " | ".join(x if x != "" else "∅" for x in r) + " |\n"
    if len(rows) > limit: s += f"\n_(показано {limit} з {len(rows)} рядків)_\n"
    return s


def write_doc(out, meta):
    bench = json.loads((ROOT / "queries/results/bench.json").read_text(encoding="utf-8"))
    man = json.loads((ROOT / "queries/results/manual_verification.json").read_text(encoding="utf-8"))
    L = ["# Результат 2. SPARQL-запити та їхні результати", "",
         "Сховище: pyoxigraph (локальне, персистентне), іменовані графи tbox/abox/inferred/links; запити виконуються над об'єднанням графів. "
         "Час — медіана 5 запусків на локальній машині (малий набір, тому абсолютні числа мало що кажуть). Результати згенеровано `scripts/run_queries.py`.", "",
         "## Покриття вимог", "", "| Вимога | Запит |", "|---|---|"]
    cover = {"SELECT": "q01, q08", "ASK": "q02", "CONSTRUCT": "q03", "агрегація": "q04, q07", "OPTIONAL": "q05, q07", "FILTER": "q01, q03, q05, q08", "property path": "q06, q07", "federated (SERVICE → Wikidata-дзеркало)": "q09"}
    L += [f"| {k} | {v} |" for k, v in cover.items()] + [""]
    for i, (name, r) in enumerate(out.items(), 1):
        mt = meta[name]; text = (ROOT / "queries" / name).read_text(encoding="utf-8").strip()
        L += [f"## {i}. `{name}` — {mt['types']}", "", f"**CQ:** {mt['cq']} — {mt['cqtext']}", "", "```sparql", text, "```", ""]
        if r["kind"] == "ASK": L += [f"**Результат:** `{str(r['answer']).lower()}`", ""]
        elif r["kind"] == "CONSTRUCT":
            tr = r["triples"]; L += [f"**Результат:** {len(tr)} тріплів (перші 6):", "", "```", *(" ".join(t) for t in tr[:6]), "```", ""]
        else: L += ["**Результат:**", "", md_table(r["vars"], r["rows"])]
        L += [f"**Час:** {r['ms_median']} мс", "", f"**Інтерпретація:** {mt['interp']}", ""]
    L += ["## Оптимізація повільного запиту: вимірювання часу", "",
          f"Синтетичний набір (seed 42): {bench['variants']} варіантів × 4 анотації = {bench['triples']} тріплів. Задача: порахувати варіанти з QD < 2. Обидва запити дають однакову відповідь ({bench['slow']['answer']}).", "",
          "| Запит | Медіана, мс | Усі 5 запусків, мс |", "|---|---|---|",
          f"| `queries/bench/slow.rq` (змінні предикати, `STR()`, фільтри за IRI) | {bench['slow']['ms_median']} | {bench['slow']['ms_all']} |",
          f"| `queries/bench/fast.rq` (фіксовані предикати, літерал в шаблоні) | {bench['fast']['ms_median']} | {bench['fast']['ms_all']} |", "",
          f"Прискорення ≈ {bench['speedup']}×. Що змінено: (1) змінні предиката `?p ?q ?r` із `FILTER(?p = …)` замінено на сталі IRI — тоді рушій бере індекс за предикатом; (2) `STR(?nm) = \"QD\"` замінено літералом «QD» прямо у шаблоні — це вибірка за індексом, а не перевірка після повного з'єднання; "
          "(3) шаблон починається з найселективнішої частини. Висновок обмежений: це один рушій (pyoxigraph), один набір, одна машина; на Fuseki/GraphDB співвідношення може бути іншим.", "",
          "## Ручна перевірка (≥3 запитів)", "",
          "Результати чотирьох запитів звірено з незалежним обчисленням звичайним Python-кодом по тріплах `abox.ttl` (без SPARQL): `scripts/verify_manual.py` → `queries/results/manual_verification.json`. "
          "Це перевірка рівня V2 (повторне обчислення іншим способом), а не експертна V3.", "", "| Запит | Збіг |", "|---|---|"]
    for k, v in man.items(): L.append(f"| {k} | {'так' if v['match'] else 'ні'} |")
    L += ["", "Знахідка під час перевірки: перша версія звірки для q04 показала «розбіжність» середнього QD зразка C (16.91 проти 16.92). Причина — не помилка запиту: точне середнє дорівнює 16.915, SPARQL `ROUND` округлює половину вгору, а `round()` у Python на float дав 16.91. Звірку виправлено (Decimal, ROUND_HALF_UP); запит не змінювався.", "",
          "Також руками (за текстом `abox.ttl`) перевірено: у `Sofiia` `hasAgeYears 17`, `hasParent Olena` → вона в q08 має шанс 0.5 і тестування «ні»; VAR-102 має QD 1.1."]
    (ROOT / "docs/sparql_results.md").write_text("\n".join(L) + "\n", encoding="utf-8")


if __name__ == "__main__":
    o, m = main(); write_doc(o, m)
