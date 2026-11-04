# Результат 5. Зв'язки із зовнішніми джерелами (Wikidata)

## 1. Метод і його межі

Кандидатів знайдено пошуком по Wikidata (веб-пошук із фільтром домену wikidata.org, 2026-10-27). Сторінки сутностей **відкрити не вдалося** (інструмент читання сторінок повернув `url_not_found`), а прямого доступу до query.wikidata.org із середовища виконання немає. Тому єдине, що перевірено, — **заголовок (мітка) сутності у списку пошуку** і його збіг із нашою міткою. Не перевірено: опис, «instance of», зовнішні ідентифікатори, мовні версії. Це рівень **V1** (поверхнева перевірка), не V2+.

Через це: (а) `owl:sameAs` і `skos:exactMatch` не використано взагалі — вони вимагають перевірки типу сутності; (б) усі прийняті зв'язки — `skos:closeMatch` (один — `skos:relatedMatch`); (в) впевненість не вища за medium-high.

## 2. Прийняті зв'язки (9)

| Наш термін | Wikidata | Мітка Wikidata | Властивість | Впевненість | Збіг мітки (V1) | Обґрунтування |
|---|---|---|---|---|---|---|
| dkh:Gene | wd:Q7187 | gene | skos:closeMatch | medium-high | так | мітки збігаються; тип/опис сторінки не перевірено, тому closeMatch, а не exactMatch |
| dkh:BreastCancer | wd:Q128581 | breast cancer | skos:closeMatch | medium-high | так | мітки збігаються; ми також маємо MeSH Breast Neoplasms (ЛР5) — узгоджується |
| dkh:OvarianCancer | wd:Q172341 | ovarian cancer | skos:closeMatch | medium-high | так | мітки збігаються; MeSH Ovarian Neoplasms (ЛР5) |
| dkh:SNP | wd:Q501128 | single-nucleotide polymorphism | skos:closeMatch | medium-high | так | мітки збігаються з точністю до дефіса |
| dkh:GeneticCounseling | wd:Q1124169 | genetic counseling | skos:closeMatch | medium-high | так | мітки збігаються; MeSH Genetic Counseling (ЛР5) |
| dkh:Exon | wd:Q373027 | exon | skos:closeMatch | medium | так | мітки збігаються; у пошуку є омоніми (прізвища, ExxonMobil) — вибрано запис саме з міткою «exon», тип не перевірено |
| dkh:BRCA1 | wd:Q227339 | BRCA1 | skos:closeMatch | medium | так | мітка збігається; у Wikidata ген і білок — окремі елементи, не з'ясовано, який саме Q227339; тому closeMatch, не sameAs |
| dkh:BRCA2 | wd:Q17853272 | BRCA2 | skos:closeMatch | low-medium | так | мітка збігається, але є другий кандидат Q421651 «BRCA2 DNA repair associated»; який із двох — ген, не перевірено |
| dkh:VCFFile | wd:Q7915770 | Variant Call Format | skos:relatedMatch | low | ні (мітки відрізняються) | наш клас — файл у форматі, Wikidata — формат: не еквівалент, лише пов'язане поняття |

Зв'язки та їхні анотації (впевненість, коментар, спосіб перевірки) — у `data/links.ttl`: сам зв'язок + вузол `rdf:Statement` із `dkh:matchConfidence`, `rdfs:comment`, `dkh:matchVerification`. Завантажено в іменований граф `urn:dkh:graph:links`.

## 3. Відхилені зв'язки (4)

| Наш термін | Кандидат | Мітка Wikidata | Причина відхилення |
|---|---|---|---|
| dkh:SNP | wd:Q7391885 | SNP array | «SNP array» — технологія (мікрочип) для виявлення SNP, не тип варіанта: мітка іншого поняття |
| dkh:PathogenicVariant | wd:Q4836333 | BRCA mutation | «BRCA mutation» вужче (лише BRCA), а наш клас — будь-який патогенний варіант; зв'язок хибний за обсягом |
| dkh:(ЛР6, не клас ЛР7) | wd:Q19000660 | hereditary breast ovarian cancer | це конкретний синдром (HBOC), вужчий за «спадковий рак» |
| dkh:BRCA2 | wd:Q421651 | BRCA2 DNA repair associated | другий елемент для того ж гена: неоднозначність; без відкритої сторінки (ген чи білок) обрати не можна — залишено перший збіг за точною міткою |

**Для захисту — яке посилання відхилено і чому:** найпоказовіше — `dkh:SNP` ↔ `wd:Q7391885` «SNP array»: мітка містить «SNP», але це мікрочип (технологія), а не тип варіанта; пошук за словом дав би хибний зв'язок. Другий — `dkh:PathogenicVariant` ↔ «BRCA mutation»: вужчий за наш клас.

Кандидат `Q421651` для BRCA2 відхилено лише через неоднозначність (ген чи білок невідомо); обраний `Q17853272` має найнижчу впевненість (low-medium), бо вибір між двома кандидатами зроблено за порядком у списку пошуку, а не за змістом.

## 4. Федеративний запит

Запит `queries/q09_federated_wikidata.rq` бере наші зв'язки з графа `links` і через `SERVICE` дістає мітку Wikidata для кожного Q-id.

**Важливо:** `SERVICE` тут звертається до **локального дзеркала** (`scripts/mock_wikidata.py`, `data/wikidata_mirror.ttl`), яке містить лише пари «Q-id → мітка», зняті зі списку пошуку. Це демонструє працездатність федерації (запит, HTTP-протокол SPARQL, об'єднання результатів), але **не є запитом до справжньої Wikidata**. Мітки в дзеркалі взято з тих самих даних, за якими «перевірялись» зв'язки, тож збіг міток у цьому запиті — коло, а не незалежне підтвердження. Щоб виконати на справжній Wikidata: `WIKIDATA_ENDPOINT=https://query.wikidata.org/sparql python3 scripts/run_queries.py` на машині з доступом до мережі.

```sparql
# Федеративний запит: наші зв'язки (graph links) + мітки з Wikidata через SERVICE
# Тип: federated query. Адреса ендпоїнта підставляється скриптом: {ENDPOINT} = реальний https://query.wikidata.org/sparql або локальне дзеркало
SELECT ?term ?wd ?wdLabel ?prop
WHERE {
  ?term ?prop ?wd .
  FILTER (?prop IN (skos:closeMatch, skos:relatedMatch) && STRSTARTS(STR(?wd), "http://www.wikidata.org/entity/"))
  SERVICE <{ENDPOINT}> {
    ?wd rdfs:label ?wdLabel .
    FILTER (LANG(?wdLabel) = "en")
  }
}
ORDER BY ?term
```

Результат (9 рядків, 1.5 мс):

| term | wd | wdLabel | prop |
|---|---|---|---|
| dkh:BRCA1 | wd:Q227339 | BRCA1 | skos:closeMatch |
| dkh:BRCA2 | wd:Q17853272 | BRCA2 | skos:closeMatch |
| dkh:BreastCancer | wd:Q128581 | breast cancer | skos:closeMatch |
| dkh:Exon | wd:Q373027 | exon | skos:closeMatch |
| dkh:Gene | wd:Q7187 | gene | skos:closeMatch |
| dkh:GeneticCounseling | wd:Q1124169 | genetic counseling | skos:closeMatch |
| dkh:OvarianCancer | wd:Q172341 | ovarian cancer | skos:closeMatch |
| dkh:SNP | wd:Q501128 | single-nucleotide polymorphism | skos:closeMatch |
| dkh:VCFFile | wd:Q7915770 | Variant Call Format | skos:relatedMatch |

## 5. Що ще потрібно (за межами цього середовища)

- Відкрити сторінки Q-id у Wikidata й перевірити «instance of» / опис (перевести V1 → V2).
- Для зв'язків із DBpedia та CWE (вимога завдання допускає) кандидатів не шукано: зовнішні ресурси недоступні для перевірки.
- Повторити q09 на живому ендпоїнті.
