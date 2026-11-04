# Результат 5. Порівняння зі SPARQL та text-to-Cypher

## 1. П'ять питань у SPARQL (ЛР8, pyoxigraph) і Cypher (FalkorDB)

Дані — ті самі (RDF-граф ЛР8 і LPG, побудований з нього). Результати порівнюються як множини рядків (числа — за значенням). Довжина — символи/слова запиту без коментарів і зайвих пробілів (без рядка PREFIX); час — медіана 5 запусків після прогріву на різних рушіях, тому порівнювати рушії за часом не слід (суб-мілісекунди, малі дані).

| № | Питання | Збіг результатів | SPARQL: довжина (симв./слів), мс | Cypher: довжина, мс |
|---|---|---|---|---|
| P1 | SNP-варіанти з QD < 2 | так | 165 / 27, 0.19 | 117 / 11, 0.57 |
| P2 | Кількість варіантів і середній QD по зразках (внутрішнє з'єднання з анотацією QD) | так | 222 / 36, 0.36 | 161 / 13, 0.72 |
| P3 | Предки Olena (транзитивно) | так | 75 / 13, 0.06 | 83 / 6, 0.21 |
| P4 | Кількість варіантів у кожному гені | так | 97 / 19, 0.15 | 76 / 6, 0.36 |
| P5 | Родичі зі ступенем, шансом успадкування, віком і можливістю тестування (≥ 18) | ні — пояснено нижче | 292 / 43, 0.21 | 224 / 25, 0.31 |

### P1. SNP-варіанти з QD < 2

```sparql
SELECT DISTINCT ?id WHERE { ?v a dkh:SNP ; dkh:hasVariantId ?id ; dkh:hasAnnotation ?a . ?a dkh:hasAnnotationName "QD" ; dkh:hasNumericValue ?x . FILTER (?x < 2.0) }
```

```cypher
MATCH (v:Variant {type:'SNP'})-[:HAS_ANNOTATION]->(a:Annotation {name:'QD'}) WHERE a.value < 2.0 RETURN DISTINCT v.id
```

Результат (однаковий): VAR-002; VAR-101; VAR-102; VAR-111; VAR-151.

### P2. Кількість варіантів і середній QD по зразках (внутрішнє з'єднання з анотацією QD)

```sparql
SELECT ?c (COUNT(DISTINCT ?v) AS ?n) (ROUND(AVG(?x) * 100) / 100 AS ?avg) WHERE { ?v dkh:fromSample ?s ; dkh:hasAnnotation ?a . ?s dkh:hasSampleCode ?c . ?a dkh:hasAnnotationName "QD" ; dkh:hasNumericValue ?x } GROUP BY ?c
```

```cypher
MATCH (v:Variant)-[:FROM_SAMPLE]->(s:Sample), (v)-[:HAS_ANNOTATION]->(a:Annotation {name:'QD'}) RETURN s.code, count(DISTINCT v), round(avg(a.value) * 100) / 100
```

Результат (однаковий): A, 22, 15.14; B, 20, 15.58; C, 20, 16.92.

### P3. Предки Olena (транзитивно)

```sparql
SELECT DISTINCT ?l WHERE { dkh:Olena dkh:hasParent+ ?p . ?p rdfs:label ?l }
```

```cypher
MATCH (:Person {name:'Olena'})-[:HAS_PARENT*1..]->(p:Person) RETURN DISTINCT p.name
```

Результат (однаковий): Iryna; Maria; Petro.

### P4. Кількість варіантів у кожному гені

```sparql
SELECT ?l (COUNT(DISTINCT ?v) AS ?n) WHERE { ?v dkh:locatedIn ?g . ?g rdfs:label ?l } GROUP BY ?l
```

```cypher
MATCH (v:Variant)-[:LOCATED_IN]->(g:Gene) RETURN g.symbol, count(DISTINCT v)
```

Результат (однаковий): BRCA1, 14; BRCA2, 20; PALB2, 14; TP53, 16.

### P5. Родичі зі ступенем, шансом успадкування, віком і можливістю тестування (≥ 18)

```sparql
SELECT DISTINCT ?name ?class ?prob ?age ?can WHERE { ?p dkh:hasAgeYears ?age ; rdfs:label ?name ; a ?class . ?class rdfs:subClassOf ?r . ?r owl:onProperty dkh:hasInheritanceProbability ; owl:hasValue ?prob . dkh:CT-01 dkh:hasMinTestingAge ?min . BIND (IF(?age >= ?min, "так", "ні") AS ?can) }
```

```cypher
MATCH (p:Person)-[:INSTANCE_OF]->(k:Concept) WHERE k.probability IS NOT NULL MATCH (c:Procedure {id:'CT-01'}) RETURN p.name, k.name, k.probability, p.ageYears, CASE WHEN p.ageYears >= c.minTestingAge THEN 'так' ELSE 'ні' END
```

SPARQL: Andrii, ThirdDegreeRelative, 0.125, 40, так; Halyna, SecondDegreeRelative, 0.25, 65, так; Iryna, FirstDegreeRelative, 0.5, 68, так; Marta, FirstDegreeRelative, 0.5, 39, так; Petro, FirstDegreeRelative, 0.5, 70, так; Sofiia, FirstDegreeRelative, 0.5, 17, ні.

Cypher: Andrii, ThirdDegreeRelative, 0.125, 40, так; Halyna, SecondDegreeRelative, 0.25, 65, так; Iryna, FirstDegreeRelative, 0.5, 68, так; Maria, SecondDegreeRelative, 0.25, , ні; Marta, FirstDegreeRelative, 0.5, 39, так; Petro, FirstDegreeRelative, 0.5, 70, так; Sofiia, FirstDegreeRelative, 0.5, 17, ні.

### Пояснення розбіжностей і додаткові перевірки

- **P2.** Збіг лише тоді, коли запит Cypher також вимагає наявність анотації QD (внутрішнє з'єднання, як у SPARQL): зразок A — 22 варіанти. Якщо замінити з'єднання на `OPTIONAL MATCH` (як у запиті c03 Результату 3), для зразка A виходить **24** варіантів: два варіанти ЛР7 (VAR-003, VAR-004) не мають анотації QD. Тобто різниця — у семантиці запиту, а не рушія.
- **P5.** Cypher-версія дає на один рядок більше: `Maria` (ступінь 2, шанс 0.25) з порожнім віком; у SPARQL її немає, бо шаблон `?p dkh:hasAgeYears ?age` вимагає наявності тріпла. Cypher не відкидає рядок із `null`, а вираз `null >= 18` дає «ні». Додавши `p.ageYears IS NOT NULL`, Cypher-результат збігається зі SPARQL (перевірено: збіг). Це приклад різного ставлення до відсутніх даних (шаблон проти значення null).

## 2. Таблиця порівняння

Оцінки «читабельність» і «зручність» — мої суб'єктивні судження за цими п'ятьма питаннями та Результатом 3; довжина й час — виміряні.

| Критерій | SPARQL (RDF) | Cypher (LPG) |
|---|---|---|
| Читабельність | Тріплетні шаблони з префіксами й явними змінними; шляхи читаються гірше | Шаблон «намальований» стрілками `(a)-[:R]->(b)`; для шляхів і зв'язків читається природніше |
| Довжина (сума по 5 запитах) | 851 симв. / 138 слів | 661 симв. / 61 слів |
| Час (медіана, сума по 5) | 0.97 мс (pyoxigraph) | 2.17 мс (FalkorDB) — різниця в межах накладних витрат викликів, висновку про рушії немає |
| Шляхи | `+`, `*`, `^`, `\|` — лаконічно, але без довжини й найкоротшого шляху | `*1..n`, `shortestPath`, повернення самого шляху `p`, `length(p)` |
| Виведення (reasoning) | Є: у сховищі лежать матеріалізовані типи HermiT; `rdfs:subClassOf` у даних | Немає: ієрархія — вузли `SUBCLASS_OF`, виведення замінюється обходом у запиті |
| Походження фактів | Окремий іменований граф або RDF-star / реіфікація (громіздко) | Властивості прямо на зв'язку (`source`, `confidence`, `validFrom`) |
| Цілісність даних | SHACL (ЛР8) — декларативні форми | Унікальні обмеження й індекси; складніші перевірки — запитами |
| Інтеграція | Глобальні IRI, федерація `SERVICE`, відкриті дані (Wikidata) | Ідентифікатори локальні; обмін через CSV/APOC, федерації немає |
| Обмеження, виявлені в цій роботі | Немає вбудованих PageRank/Louvain; середнє округлення залежить від рушія (ROUND) | Діалекти відрізняються: у FalkorDB `shortestPath` лише в `RETURN`/`WITH` і лише спрямований, `toFloat` повертає float32; у Neo4j це інакше |

## 3. Text-to-Cypher

Конвеєр (`scripts/t2c.py`): **промпт зі схемою графа** (мітки з типами властивостей, типи зв'язків з кінцями — генерується з CSV) → **LLM** → **парсер** (витяг із ```cypher) → **безпека (read-only)** → **перевірка схеми** (усі мітки, типи зв'язків і властивості мають бути в схемі) → **виконання з LIMIT 100 і таймаутом 3 с** → порівняння з еталоном.

**Read-only роль.** Два шари: (1) статичний фільтр відхиляє `CREATE, MERGE, DELETE, DETACH, SET, REMOVE, DROP, LOAD CSV, FOREACH, CALL`; (2) виконання лише через `GRAPH.RO_QUERY`, де сервер сам відхиляє запис. У Neo4j відповідник другого шару — окремий користувач із роллю `reader` (`GRANT ROLE reader TO llm_user`), у цій роботі не перевірявся, бо Neo4j тут недоступний.

| Випадок | Статичний фільтр | Перевірка схеми |
|---|---|---|
| запис через CREATE: `MATCH (n:Gene) CREATE (:Hack {x: 1}) RETURN n.symbol` | ВІДХИЛЕНО: заборонена конструкція: CREATE | — |
| видалення: `MATCH (n) DETACH DELETE n` | ВІДХИЛЕНО: заборонена конструкція: DETACH | — |
| SET властивості: `MATCH (v:Variant {id:'VAR-001'}) SET v.type = 'X' RETURN v` | ВІДХИЛЕНО: заборонена конструкція: SET | — |
| виклик процедури: `CALL db.constraints()` | ВІДХИЛЕНО: заборонена конструкція: CALL | — |
| вигадана мітка: `MATCH (x:Mutation) RETURN x` | пропущено | ВІДХИЛЕНО: мітка Mutation |
| вигадана властивість: `MATCH (v:Variant) RETURN v.qualityScore` | пропущено | ВІДХИЛЕНО: властивість qualityScore |
| вигаданий тип зв'язку: `MATCH (a)-[:KNOWS]->(b) RETURN a` | пропущено | ВІДХИЛЕНО: тип зв'язку KNOWS |

Другий шар: `CREATE (:Hack {x: 1})` через `RO_QUERY` → сервер відповів: `graph.RO_QUERY is to be executed only on read-only queries`; вузлів `Hack` після спроби — 0. LIMIT: до запитів без власного `LIMIT` дописується `LIMIT 100`.

### Набір питань і метрики

`tests/t2c.jsonl`: **27 питань**, поле `tier`. Спочатку складено 16 «простих» (t01–t16); на них вийшло лише 15/16 і 16/16 правильних, тому для змістовнішого аналізу помилок **після цього** додано 11 «складних» (t17–t27: OPTIONAL MATCH з нулями, `shortestPath`, `IS NULL`, дві анотації одного варіанта, властивості зв'язків, збережені результати аналізу графа). Це рішення прийнято після перших результатів — слід враховувати при інтерпретації. Еталонні запити й відповіді склала та сама система, що й генератор. Генератори — два незалежні сліпі прогони субагентів тієї самої моделі (r1, r2; температура/seed не контролювались).

| Метрика | r1 всі (27) | r2 всі (27) | r1 прості (16) | r2 прості (16) | r1 складні (11) | r2 складні (11) |
|---|---|---|---|---|---|---|
| Пройшов фільтр безпеки | 27/27 | 27/27 | 16/16 | 16/16 | 11/11 | 11/11 |
| Лише зі схеми | 27/27 | 27/27 | 16/16 | 16/16 | 11/11 | 11/11 |
| Виконався без помилки | 26/27 | 26/27 | 16/16 | 16/16 | 10/11 | 10/11 |
| Правильний результат | 25/27 (93%) | 26/27 (96%) | 15/16 (94%) | 16/16 (100%) | 10/11 (91%) | 10/11 (91%) |

**Частка коректних запитів:** 25/27 (93%) у r1 і 26/27 (96%) у r2; на 16 простих — 15/16 і 16/16; на 11 складних — 10/11 і 10/11. Вибірка мала, прогонів два, тож різниця між r1 і r2 (1 питання) — шум. Усі 27 відповідей пройшли фільтр безпеки й перевірку схеми, бо схема була в промпті.

### Аналіз трьох помилок

| Прогін | Питання | Етап | Клас | Деталь |
|---|---|---|---|---|
| r1 | t14 | result | E1 — зайвий стовпець | отримано [["BRCA2", "20"], ["TP53", "16"]]; очікувалось [["BRCA2"], ["TP53"]] |
| r1 | t20 | execution | E2 — діалектна несумісність | FalkorDB currently only supports shortestPaths in WITH or RETURN clauses |
| r2 | t20 | execution | E2 — діалектна несумісність | FalkorDB currently only supports shortestPaths in WITH or RETURN clauses |

**E1 — зайвий стовпець (r1, t14).** Питання «Які гени мають більше п'ятнадцяти варіантів?»; модель повернула `g.symbol, cnt` (ген і кількість), еталон — лише ген. Зміст відповіді правильний (BRCA2, TP53), але метрика порівнює таблиці суворо. Це слабкість метрики, а не знань моделі; м'яка метрика (еталонні стовпці — підмножина) зарахувала б 26/27. Вихід: у промпт додати «повертай лише запитані стовпці».

```cypher
MATCH (v:Variant)-[:LOCATED_IN]->(g:Gene)
WITH g, count(DISTINCT v) AS cnt
WHERE cnt > 15
RETURN g.symbol, cnt
```

**E2 — діалектна несумісність (r1 і r2, t20).** Питання «Скільки кроків має найкоротший шлях від Olena до Maria?». Обидва прогони написали `MATCH p = shortestPath((a)-[:HAS_PARENT*]->(b)) RETURN length(p)` — це коректний Cypher для Neo4j 5 (саме Neo4j був названий у промпті), але FalkorDB дозволяє `shortestPath` лише у `WITH`/`RETURN`, тому сервер повернув помилку: `FalkorDB currently only supports shortestPaths in WITH or RETURN clauses`. Отже, це помилка переносимості між рушіями, а не логіки моделі; на справжньому Neo4j запит, ймовірно, відпрацював би правильно (перевірити неможливо). Два з трьох «збоїв» — це один і той самий випадок, повторений у двох прогонах, тому незалежних класів помилок лише два. Вихід: назвати діалект у промпті (`shortestPath` лише у WITH/RETURN) — або запускати на Neo4j.

```cypher
MATCH (a:Person {name: 'Olena'}), (b:Person {name: 'Maria'})
MATCH p = shortestPath((a)-[:HAS_PARENT*]->(b))
RETURN length(p) AS steps
```

**Чого метрика не показує.** Запити, що дали правильний результат на цьому малому графі, можуть бути хибними на інших даних (наприклад, відсутність `DISTINCT`); їх не перевірено на варіаціях даних. Верифікація LLM-запитів тут — виконання й порівняння з еталоном (рівень V2); вимога V4 (незалежна експертна вибірка) не виконана.
