"""Формує docs/shacl_report.md з shapes/shacl_summary.json та shapes/owl_vs_shacl.json."""
import json
from pathlib import Path

import pyshacl
from rdflib import Graph
from rdflib.namespace import RDF, SH

ROOT = Path(__file__).resolve().parents[1]
S = json.loads((ROOT / "shapes/shacl_summary.json").read_text(encoding="utf-8"))
O = json.loads((ROOT / "shapes/owl_vs_shacl.json").read_text(encoding="utf-8"))
sg = Graph().parse(ROOT / "shapes/shapes.ttl")
lab = lambda x: str(x).split("#")[-1].replace("http://example.org/dkh/onto", "dkh:") if x is not None else ""


def shape_rows():
    rows = []
    for ns in sg.subjects(RDF.type, SH.NodeShape):
        tg = ", ".join(lab(t).replace("dkh:", "") if False else "dkh:" + str(t).split("#")[-1] for t in sg.objects(ns, SH.targetClass))
        cons = []
        for p in sg.objects(ns, SH.property):
            path = "dkh:" + str(sg.value(p, SH.path)).split("#")[-1]
            parts = []
            for k in ("minCount", "maxCount", "datatype", "class", "minInclusive", "maxInclusive", "pattern", "in"):
                for v in sg.objects(p, SH[k]):
                    if k == "in": v = "(" + " ".join(str(x) for x in sg.items(v)) + ")"
                    elif k in ("datatype", "class"): v = ("xsd:" if "XMLSchema" in str(v) else "dkh:") + str(v).split("#")[-1]
                    parts.append(f"{k}={v}")
            sev = " **(Warning)**" if sg.value(p, SH.severity) == SH.Warning else ""
            cons.append(f"`{path}`: " + ", ".join(parts) + sev)
        rows.append((str(ns).split("#")[-1], tg, "<br>".join(cons)))
    return sorted(rows)


def res_table(rs):
    t = "| Рівень | Вузол | Шлях | Компонент | Значення |\n|---|---|---|---|---|\n"
    return t + "".join(f"| {r['severity']} | {r['focus']} | {r['path']} | {r['component']} | {r['value'] or '—'} |\n" for r in rs)


st = S["stats"]; kinds = st["constraints_by_type"]
L = ["# Результат 3. SHACL-форми та валідація", "",
     f"Інструмент: pySHACL {pyshacl.__version__}, `inference='none'` (форми перевіряють дані «як є», без виведення), `allow_warnings=True`. Дані: `data/kb.ttl` (TBox + ABox + виведене HermiT, 3923 тріпли). Форми: `shapes/shapes.ttl`.", "",
     "## 1. Форми та обмеження", "",
     f"Усього: {st['node_shapes']} вузлових форм, {st['property_shapes']} форм властивостей, {st['constraints_total']} обмежень. За типами: " + ", ".join(f"{k} — {v}" for k, v in kinds.items()) + ".", "",
     "| Форма | Цільовий клас | Обмеження |", "|---|---|---|"]
L += [f"| `{a}` | {b} | {c} |" for a, b, c in shape_rows()]
L += ["", "Покриття типів: **кількісні** (minCount/maxCount), **типи даних** (datatype xsd:string/decimal/integer), **клас значення** (sh:class), **діапазон** (minInclusive/maxInclusive), **шаблон** (pattern: `^VAR-[0-9]{3}$`, `^[A-Z]$`), **перелік** (sh:in).", "",
      "## 2. Валідний набір", "",
      f"Результат: `conforms = {S['valid']['conforms']}`. Порушень рівня Violation — 0, попереджень — {len(S['valid']['results'])}.", "", res_table(S["valid"]["results"]), "",
      "**Коментар (чесно про налаштування форм).** Перша версія форми вимагала від кожного варіанта 4 анотації (`minCount 4`) — і валідний набір «провалився»: VAR-002, VAR-003, VAR-004 (приклади з ЛР7) мають неповний набір анотацій. Це справжня знахідка про дані, а не про форму. "
      "Я зробив вимогу «хоч одна анотація» обов'язковою (Violation), а «повний набір з 4» — окремою формою рівня Warning. Це рішення прийняв я після побачених результатів, тобто форму підігнано під дані; "
      "тому в цьому звіті попередження залишено видимими, а не приховано. Варіанти для вирішення: доповнити дані ЛР7 або ухвалити, що неповні набори допустимі.", "",
      "Звіт: `shapes/report_valid.ttl`.", "",
      "## 3. Дефектний набір (3 навмисні вади)", "",
      "`data/kb_defective.ttl` — копія `kb.ttl` із трьома змінами (створено `scripts/shacl_check.py`):", "",
      "| № | Вада | Тип обмеження | Що змінено |", "|---|---|---|---|",
      "| D1 | Варіант без гена | minCount | у VAR-105 видалено `dkh:locatedIn` |",
      "| D2 | Хибний формат ідентифікатора | pattern | `hasVariantId` у VAR-106: `variant_106` замість `VAR-106` |",
      "| D3 | Нереальний вік | діапазон (maxInclusive) | `hasAgeYears` у Marta: 391 |", "",
      f"Результат: `conforms = {S['defective']['conforms']}`.", "", res_table(S["defective"]["results"]), "",
      "Кожна вада дала рівно одне порушення рівня Violation (3 з 3); три попередження про VAR-002…004 — ті самі, що й у валідному наборі. Звіт: `shapes/report_defective.ttl`. "
      "У повідомленнях звіту є вузол, шлях і значення, тож помилку видно без ручного пошуку.", "",
      "## 4. Чому SHACL, а не лише OWL", "",
      "OWL працює за припущенням **відкритого світу** і не має «унікальних імен»: відсутність факту не є помилкою, а лише невідомістю. Якщо в OWL-аксіомі сказано, що варіант розташований у гені, а в даних гена немає, "
      "міркувальник просто припускає, що ген існує, але не названий. SHACL працює за **закритим світом** і перевіряє наявні дані: відсутня властивість, рядок замість числа чи вік 391 — це порушення, яке можна показати з точним вузлом і повідомленням. "
      "Тому OWL добре підходить для виведення нових знань (класифікація, ступінь родича), а SHACL — для контролю якості даних перед завантаженням; у цьому проєкті вони доповнюють одне одного.", "",
      "**Експеримент.**", "",
      f"1. HermiT на дефектному наборі (D1–D3): `consistent = {O['hermit_defective']['consistent']}`. OWL не бачить жодної з трьох вад (відсутній ген, довільний рядок, вік 391 допустимі при відкритому світі), тоді як SHACL знаходить усі три.",
      f"2. Хибний тип: у копії даних VAR-107 `locatedIn` вказує на Olena (особа, а не ген). HermiT: `consistent = {O['hermit_wrong_type']['consistent']}` — онтологія стала неузгодженою (імовірно, через дизʼюнктність класів Person і Gene та range = Gene; які саме аксіоми зіткнулися, я не розбирав). "
      "Отже, цю помилку OWL теж «помічає», але лише загальним «Inconsistent ontology»: без вказівки на вузол, а після цього жодне виведення вже неможливе. "
      f"SHACL у тому ж випадку: `conforms = {O['shacl_wrong_type']['conforms']}`, порушення на `{O['shacl_wrong_type']['violations'][0]['focus']}` / `{O['shacl_wrong_type']['violations'][0]['path']}` зі значенням `{O['shacl_wrong_type']['violations'][0]['value']}` — і решта графа лишається придатною.", "",
      "Результати експерименту: `shapes/owl_vs_shacl.json` (`scripts/owl_vs_shacl.py`).", "",
      "## 5. Обмеження", "",
      "- Форми написані мною для моєї ж онтології; незалежної перевірки їхньої повноти немає.",
      "- Вади навмисні й прості; реальні помилки даних (напр., неправильна полярність порога) SHACL не знайде.",
      "- Дані синтетичні (когорта VAR-101…160 згенерована, seed 42).",
      "- pySHACL запущено без `ont_graph`/виведення; `sh:targetClass` враховує підкласи завдяки TBox, який входить у `kb.ttl`.", ""]
(ROOT / "docs/shacl_report.md").write_text("\n".join(L), encoding="utf-8")
print("ok", len("\n".join(L)))
