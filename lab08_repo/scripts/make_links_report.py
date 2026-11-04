"""Формує docs/links_verification.md з data/links_decisions.csv та queries/results/results.json (q09)."""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
rows = list(csv.DictReader(open(ROOT / "data/links_decisions.csv", encoding="utf-8-sig")))
res = json.loads((ROOT / "queries/results/results.json").read_text(encoding="utf-8"))["q09_federated_wikidata.rq"]
acc = [r for r in rows if r["decision"] == "accepted"]; rej = [r for r in rows if r["decision"] == "rejected"]
L = ["# Результат 5. Зв'язки із зовнішніми джерелами (Wikidata)", "",
     "## 1. Метод і його межі", "",
     "Кандидатів знайдено пошуком по Wikidata (веб-пошук із фільтром домену wikidata.org, 2026-10-27). Сторінки сутностей **відкрити не вдалося** (інструмент читання сторінок повернув `url_not_found`), а прямого доступу до query.wikidata.org із середовища виконання немає. "
     "Тому єдине, що перевірено, — **заголовок (мітка) сутності у списку пошуку** і його збіг із нашою міткою. Не перевірено: опис, «instance of», зовнішні ідентифікатори, мовні версії. Це рівень **V1** (поверхнева перевірка), не V2+.", "",
     "Через це: (а) `owl:sameAs` і `skos:exactMatch` не використано взагалі — вони вимагають перевірки типу сутності; (б) усі прийняті зв'язки — `skos:closeMatch` (один — `skos:relatedMatch`); (в) впевненість не вища за medium-high.", "",
     f"## 2. Прийняті зв'язки ({len(acc)})", "", "| Наш термін | Wikidata | Мітка Wikidata | Властивість | Впевненість | Збіг мітки (V1) | Обґрунтування |", "|---|---|---|---|---|---|---|"]
for r in acc: L.append(f"| {r['our_iri']} | {r['wikidata']} | {r['wikidata_label']} | {r['property']} | {r['confidence']} | {'так' if r['label_match_V1']=='1' else 'ні (мітки відрізняються)'} | {r['rationale']} |")
L += ["", "Зв'язки та їхні анотації (впевненість, коментар, спосіб перевірки) — у `data/links.ttl`: сам зв'язок + вузол `rdf:Statement` із `dkh:matchConfidence`, `rdfs:comment`, `dkh:matchVerification`. Завантажено в іменований граф `urn:dkh:graph:links`.", "",
      f"## 3. Відхилені зв'язки ({len(rej)})", "", "| Наш термін | Кандидат | Мітка Wikidata | Причина відхилення |", "|---|---|---|---|"]
for r in rej: L.append(f"| {r['our_iri']} | {r['wikidata']} | {r['wikidata_label']} | {r['rationale']} |")
L += ["", "**Для захисту — яке посилання відхилено і чому:** найпоказовіше — `dkh:SNP` ↔ `wd:Q7391885` «SNP array»: мітка містить «SNP», але це мікрочип (технологія), а не тип варіанта; пошук за словом дав би хибний зв'язок. Другий — `dkh:PathogenicVariant` ↔ «BRCA mutation»: вужчий за наш клас.", "",
      "Кандидат `Q421651` для BRCA2 відхилено лише через неоднозначність (ген чи білок невідомо); обраний `Q17853272` має найнижчу впевненість (low-medium), бо вибір між двома кандидатами зроблено за порядком у списку пошуку, а не за змістом.", "",
      "## 4. Федеративний запит", "",
      "Запит `queries/q09_federated_wikidata.rq` бере наші зв'язки з графа `links` і через `SERVICE` дістає мітку Wikidata для кожного Q-id.", "",
      "**Важливо:** `SERVICE` тут звертається до **локального дзеркала** (`scripts/mock_wikidata.py`, `data/wikidata_mirror.ttl`), яке містить лише пари «Q-id → мітка», зняті зі списку пошуку. Це демонструє працездатність федерації (запит, HTTP-протокол SPARQL, об'єднання результатів), але **не є запитом до справжньої Wikidata**. "
      "Мітки в дзеркалі взято з тих самих даних, за якими «перевірялись» зв'язки, тож збіг міток у цьому запиті — коло, а не незалежне підтвердження. Щоб виконати на справжній Wikidata: `WIKIDATA_ENDPOINT=https://query.wikidata.org/sparql python3 scripts/run_queries.py` на машині з доступом до мережі.", "",
      "```sparql", (ROOT / "queries/q09_federated_wikidata.rq").read_text(encoding="utf-8").strip(), "```", "", f"Результат ({len(res['rows'])} рядків, {res['ms_median']} мс):", "",
      "| " + " | ".join(res["vars"]) + " |", "|" + "---|" * len(res["vars"])]
L += ["| " + " | ".join(r) + " |" for r in res["rows"]]
L += ["", "## 5. Що ще потрібно (за межами цього середовища)", "",
      "- Відкрити сторінки Q-id у Wikidata й перевірити «instance of» / опис (перевести V1 → V2).",
      "- Для зв'язків із DBpedia та CWE (вимога завдання допускає) кандидатів не шукано: зовнішні ресурси недоступні для перевірки.",
      "- Повторити q09 на живому ендпоїнті."]
(ROOT / "docs/links_verification.md").write_text("\n".join(L) + "\n", encoding="utf-8")
print("ok")
