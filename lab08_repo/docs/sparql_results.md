# Результат 2. SPARQL-запити та їхні результати

Сховище: pyoxigraph (локальне, персистентне), іменовані графи tbox/abox/inferred/links; запити виконуються над об'єднанням графів. Час — медіана 5 запусків на локальній машині (малий набір, тому абсолютні числа мало що кажуть). Результати згенеровано `scripts/run_queries.py`.

## Покриття вимог

| Вимога | Запит |
|---|---|
| SELECT | q01, q08 |
| ASK | q02 |
| CONSTRUCT | q03 |
| агрегація | q04, q07 |
| OPTIONAL | q05, q07 |
| FILTER | q01, q03, q05, q08 |
| property path | q06, q07 |
| federated (SERVICE → Wikidata-дзеркало) | q09 |

## 1. `q01_select_filter_lowqd.rq` — SELECT, FILTER

**CQ:** CQ01 — За якого QD SNP-варіант отримує прапорець LowQD?

```sparql
# CQ01: За якого QD SNP-варіант отримує прапорець LowQD? -> які SNP у когорті мають QD < 2
# Типи: SELECT + FILTER
SELECT DISTINCT ?variant ?qd
WHERE {
  ?variant a dkh:SNP ; dkh:hasAnnotation ?a .
  ?a dkh:hasAnnotationName "QD" ; dkh:hasNumericValue ?qd .
  FILTER (?qd < 2.0)
}
ORDER BY ?qd ?variant
```

**Результат:**

| variant | qd |
|---|---|
| dkh:VAR-102 | 1.1 |
| dkh:VAR-101 | 1.2 |
| dkh:VAR-151 | 1.2 |
| dkh:VAR-002 | 1.5 |
| dkh:VAR-111 | 1.5 |

**Час:** 0.7 мс

**Інтерпретація:** Запит повертає 5 SNP-варіантів із QD < 2 (1.1–1.5): VAR-102, VAR-101, VAR-151, VAR-002, VAR-111. Усі вони за правилом G01 отримують прапорець LowQD. Варіант із QD = 2.0 у вибірку не потрапляє (строге «<»), що узгоджено з CQ01.

## 2. `q02_ask_pathogenic.rq` — ASK

**CQ:** CQ14, CQ17 — З кого починати каскадне тестування / чи має сенс панель, що включає ген родини?

```sparql
# CQ14/CQ17: чи є в наборі патогенний варіант у гені з панелі HBOC (підстава запропонувати каскадне тестування)?
# Тип: ASK
ASK {
  dkh:HBOC-panel dkh:hasMember ?gene .
  ?v dkh:locatedIn ?gene ; dkh:hasClinicalSignificance dkh:Pathogenic .
}
```

**Результат:** `true`

**Час:** 0.24 мс

**Інтерпретація:** Відповідь true: у наборі є варіанти, що лежать у генах панелі HBOC і мають значущість Pathogenic (VAR-001 у BRCA1 та VAR-103 у PALB2). Це умова, за якої система пропонує каскадне тестування; ASK достатньо, коли потрібне лише так/ні.

## 3. `q03_construct_flagged.rq` — CONSTRUCT, FILTER, BIND

**CQ:** CQ05 — Чи достатньо одного прапорця, щоб відхилити варіант?

```sparql
# CQ05: Чи достатньо одного прапорця? -> побудувати граф рішень: кожному варіанту, що порушує хоча б один поріг SNP, призначити статус FILTERED
# Тип: CONSTRUCT (нові тріпли з пороговими анотаціями, не зберігаються у сховищі)
CONSTRUCT {
  ?v dkh:decision "FILTERED" ; dkh:reason ?why .
}
WHERE {
  ?v a dkh:SNP ; dkh:hasAnnotation ?a .
  ?a dkh:hasAnnotationName ?n ; dkh:hasNumericValue ?x .
  FILTER ((?n = "QD" && ?x < 2.0) || (?n = "FS" && ?x > 60.0) || (?n = "SOR" && ?x > 3.0) || (?n = "MQ" && ?x < 40.0))
  BIND (CONCAT(?n, "=", STR(?x)) AS ?why)
}
```

**Результат:** 56 тріплів (перші 6):

```
dkh:VAR-002 dkh:decision FILTERED
dkh:VAR-002 dkh:reason QD=1.5
dkh:VAR-004 dkh:decision FILTERED
dkh:VAR-004 dkh:reason FS=62
dkh:VAR-101 dkh:decision FILTERED
dkh:VAR-101 dkh:reason QD=1.2
```

**Час:** 5.84 мс

**Інтерпретація:** CONSTRUCT будує новий малий граф «рішень»: тріпл dkh:decision "FILTERED" і dkh:reason (яка анотація порушила поріг). Один порушений поріг достатній (диз'юнкція у FILTER), тому для VAR-002 із QD=1.5 достатньо єдиної причини. Тріпли не записуються у сховище — це результат запиту.

## 4. `q04_aggregate_per_sample.rq` — агрегація (COUNT, AVG, MIN, MAX, GROUP BY, HAVING)

**CQ:** CQ08 — Який метод фільтрації обрати для малої панелі?

```sparql
# CQ08: який обсяг даних і яка якість по зразках? -> кількість варіантів, середні QD/FS по кожному зразку
# Тип: агрегація (GROUP BY, COUNT, AVG, MIN, MAX) + HAVING
SELECT ?sample (COUNT(DISTINCT ?v) AS ?variants) (ROUND(AVG(?qd)*100)/100 AS ?avgQD) (MIN(?qd) AS ?minQD) (MAX(?qd) AS ?maxQD)
WHERE {
  ?v dkh:fromSample ?s ; dkh:hasAnnotation ?a .
  ?s dkh:hasSampleCode ?sample .
  ?a dkh:hasAnnotationName "QD" ; dkh:hasNumericValue ?qd .
}
GROUP BY ?sample
HAVING (COUNT(DISTINCT ?v) >= 1)
ORDER BY ?sample
```

**Результат:**

| sample | variants | avgQD | minQD | maxQD |
|---|---|---|---|---|
| A | 22 | 15.14 | 1.1 | 34.9 |
| B | 20 | 15.58 | 1.5 | 34.5 |
| C | 20 | 16.92 | 1.2 | 30.3 |

**Час:** 2.35 мс

**Інтерпретація:** По кожному із трьох зразків — 20–22 варіанти, це дуже мало: GATK радить VQSR для великих наборів, а для малих — hard-filtering (джерело ЛР4); отже вибірка підтримує відповідь на CQ08, хоча сам поріг «великий/малий» у джерелі не кількісний. Середній QD ≈ 15–17, мінімум 1.1–1.5 (є кандидати на LowQD).

## 5. `q05_optional_clinical.rq` — OPTIONAL, FILTER

**CQ:** CQ14 — З кого починати тестування і чому? (потрібна клінічна значущість варіанта)

```sparql
# CQ05/CQ17: варіанти зразка A у генах панелі з необов'язковою клінічною значущістю
# Тип: OPTIONAL (варіанти без значущості не зникають з відповіді)
SELECT DISTINCT ?id ?geneLabel ?significance
WHERE {
  ?v dkh:fromSample dkh:SAMPLE-A ; dkh:hasVariantId ?id ; dkh:locatedIn ?g .
  ?g rdfs:label ?geneLabel .
  OPTIONAL { ?v dkh:hasClinicalSignificance ?significance }
  FILTER (?id <= "VAR-110")
}
ORDER BY ?id
```

**Результат:**

| id | geneLabel | significance |
|---|---|---|
| VAR-001 | BRCA1 | dkh:Pathogenic |
| VAR-002 | BRCA2 | dkh:Benign |
| VAR-003 | BRCA2 | ∅ |
| VAR-004 | BRCA2 | ∅ |
| VAR-101 | BRCA1 | ∅ |
| VAR-102 | TP53 | ∅ |
| VAR-103 | PALB2 | dkh:Pathogenic |
| VAR-104 | TP53 | ∅ |
| VAR-105 | PALB2 | ∅ |
| VAR-106 | PALB2 | ∅ |
| VAR-107 | BRCA2 | ∅ |
| VAR-108 | PALB2 | ∅ |
| VAR-109 | TP53 | ∅ |
| VAR-110 | BRCA2 | ∅ |

**Час:** 0.7 мс

**Інтерпретація:** Варіанти зразка A до VAR-110 виводяться всі (14 рядків); значущість показана лише там, де вона відома (VAR-001, VAR-002, VAR-103), в решті — порожньо. Без OPTIONAL ці 11 варіантів зникли б із відповіді, що спотворило б обсяг даних.

## 6. `q06_property_path_relatives.rq` — property path (|, ^, +)

**CQ:** CQ14, CQ16 — З кого починати тестування; що, якщо найближчий родич недоступний?

```sparql
# CQ11-CQ13: хто є родичем пробанда Olena через ланцюжок «батьки/діти/сиблінги» (скільки кроків угору)?
# Тип: property path  ( ^ інверсія, + один чи більше кроків, | альтернатива, / послідовність )
SELECT DISTINCT ?name
WHERE {
  dkh:Olena (dkh:hasParent|dkh:hasChild|dkh:hasSibling|^dkh:hasParent|^dkh:hasChild)+ ?r .
  ?r rdfs:label ?name .
  FILTER (?r != dkh:Olena)
}
ORDER BY ?name
```

**Результат:**

| name |
|---|
| Andrii |
| Halyna |
| Iryna |
| Maria |
| Marta |
| Petro |
| Sofiia |

**Час:** 157.03 мс

**Інтерпретація:** Шлях (hasParent|hasChild|hasSibling|^hasParent|^hasChild)+ обходить родовід транзитивно: від пробанда Olena досяжні 7 осіб (Andrii, Halyna, Iryna, Maria, Marta, Petro, Sofiia). Один запит замінює вручну перелічені рівні зв'язків; зайняв найбільше часу (~100+ мс) через обчислення замикання.

## 7. `q07_ancestors_path.rq` — property path (+), агрегація, OPTIONAL

**CQ:** CQ13 — Який шанс для двоюрідних і далі? (глибина родоводу)

```sparql
# Предки пробанда (транзитивний hasParent+) - ступінь «глибини» у родоводі
# Тип: property path + агрегація
SELECT ?ancestorName (COUNT(DISTINCT ?mid) AS ?intermediateGenerations)
WHERE {
  dkh:Olena dkh:hasParent+ ?anc .
  ?anc rdfs:label ?ancestorName .
  OPTIONAL { dkh:Olena dkh:hasParent+ ?mid . ?mid dkh:hasParent+ ?anc }
}
GROUP BY ?ancestorName
ORDER BY ?ancestorName
```

**Результат:**

| ancestorName | intermediateGenerations |
|---|---|
| Iryna | 0 |
| Maria | 1 |
| Petro | 0 |

**Час:** 0.37 мс

**Інтерпретація:** hasParent+ дає трьох предків пробанда; лічильник проміжних поколінь показує, що Maria (бабуся) — через одну проміжну особу, а Iryna та Petro — прямі батьки (0). Глибина — вхід для оцінки віддаленості родича.

## 8. `q08_relatives_probability_age.rq` — SELECT, JOIN TBox+ABox, FILTER/BIND

**CQ:** CQ11–CQ15 — Шанс успадкування для сиблінга/тітки/двоюрідних; чи можна тестувати 17-річного?

```sparql
# CQ11-CQ15: для кожного родича з відомим ступенем - шанс успадкування (з обмежень OWL у TBox), вік, чи можна тестувати (>= мін. віку)
# Тип: SELECT + JOIN TBox/ABox + FILTER + BIND
SELECT DISTINCT ?name ?class ?prob ?age ?canTest
WHERE {
  ?p dkh:hasAgeYears ?age ; rdfs:label ?name ; a ?class .
  ?class rdfs:subClassOf ?r .
  ?r owl:onProperty dkh:hasInheritanceProbability ; owl:hasValue ?prob .
  dkh:CT-01 dkh:hasMinTestingAge ?min .
  BIND (IF(?age >= ?min, "так", "ні") AS ?canTest)
}
ORDER BY DESC(?prob) ?name
```

**Результат:**

| name | class | prob | age | canTest |
|---|---|---|---|---|
| Iryna | dkh:FirstDegreeRelative | 0.5 | 68 | так |
| Marta | dkh:FirstDegreeRelative | 0.5 | 39 | так |
| Petro | dkh:FirstDegreeRelative | 0.5 | 70 | так |
| Sofiia | dkh:FirstDegreeRelative | 0.5 | 17 | ні |
| Halyna | dkh:SecondDegreeRelative | 0.25 | 65 | так |
| Andrii | dkh:ThirdDegreeRelative | 0.125 | 40 | так |

**Час:** 0.57 мс

**Інтерпретація:** З обмежень OWL у TBox (hasValue) береться шанс 0.5 / 0.25 / 0.125, з ABox — вік. Sofiia (17 років) має шанс 0.5, але тестування «ні» (мінімальний вік 18, CQ15); Halyna — 0.25, Andrii — 0.125 (верхня межа, CQ13). Maria не виведена, бо в ABox немає її віку.

## 9. `q09_federated_wikidata.rq` — federated (SERVICE)

**CQ:** CQ19 (додано у ЛР8) — Які терміни онтології мають зовнішні відповідники і з якою міткою в Wikidata?

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

**Результат:**

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

**Час:** 1.5 мс

**Інтерпретація:** Наші зв'язки (graph links) з'єднуються з мітками, одержаними через SERVICE. Тут SERVICE звернений до ЛОКАЛЬНОГО дзеркала міток (див. R5): реальний query.wikidata.org недоступний із середовища виконання. Результат — 9 пар «наш термін — мітка Wikidata»; на живому ендпоїнті запит треба повторити (змінна WIKIDATA_ENDPOINT).

## Оптимізація повільного запиту: вимірювання часу

Синтетичний набір (seed 42): 50000 варіантів × 4 анотації = 900000 тріплів. Задача: порахувати варіанти з QD < 2. Обидва запити дають однакову відповідь (2764).

| Запит | Медіана, мс | Усі 5 запусків, мс |
|---|---|---|
| `queries/bench/slow.rq` (змінні предикати, `STR()`, фільтри за IRI) | 472.4 | [524.2, 472.4, 457.8, 459.7, 473.3] |
| `queries/bench/fast.rq` (фіксовані предикати, літерал в шаблоні) | 99.7 | [99.3, 99.7, 101.9, 104.4, 99.1] |

Прискорення ≈ 4.7×. Що змінено: (1) змінні предиката `?p ?q ?r` із `FILTER(?p = …)` замінено на сталі IRI — тоді рушій бере індекс за предикатом; (2) `STR(?nm) = "QD"` замінено літералом «QD» прямо у шаблоні — це вибірка за індексом, а не перевірка після повного з'єднання; (3) шаблон починається з найселективнішої частини. Висновок обмежений: це один рушій (pyoxigraph), один набір, одна машина; на Fuseki/GraphDB співвідношення може бути іншим.

## Ручна перевірка (≥3 запитів)

Результати чотирьох запитів звірено з незалежним обчисленням звичайним Python-кодом по тріплах `abox.ttl` (без SPARQL): `scripts/verify_manual.py` → `queries/results/manual_verification.json`. Це перевірка рівня V2 (повторне обчислення іншим способом), а не експертна V3.

| Запит | Збіг |
|---|---|
| q01 | так |
| q04 | так |
| q06 | так |
| q08 | так |

Знахідка під час перевірки: перша версія звірки для q04 показала «розбіжність» середнього QD зразка C (16.91 проти 16.92). Причина — не помилка запиту: точне середнє дорівнює 16.915, SPARQL `ROUND` округлює половину вгору, а `round()` у Python на float дав 16.91. Звірку виправлено (Decimal, ROUND_HALF_UP); запит не змінювався.

Також руками (за текстом `abox.ttl`) перевірено: у `Sofiia` `hasAgeYears 17`, `hasParent Olena` → вона в q08 має шанс 0.5 і тестування «ні»; VAR-102 має QD 1.1.
