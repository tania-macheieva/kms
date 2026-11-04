# Результат 4. Аналіз графа та продуктивність

**Рушій і заміна GDS.** Neo4j GDS тут недоступний. PageRank виконано нативною процедурою FalkorDB `CALL algo.pageRank(null, null)` (весь граф: 370 вузлів, 757 зв'язків); Louvain у FalkorDB немає, тому спільноти обчислено `networkx.louvain_communities` (seed 42, resolution 1.0) на вигрузці графа без напрямку. Це не Neo4j GDS: назви процедур, параметри проєкції і числа можуть відрізнятися. Скрипт: `scripts/gds.py`; сирі результати: `docs/evidence/gds.json`.

## 1. PageRank: топ-10

| № | Вузол | Оцінка (FalkorDB) | Топ networkx |
|---|---|---|---|
| 1 | AnnotationType:FS | 0.08673 | AnnotationType:FS (0.08687) |
| 2 | AnnotationType:QD | 0.08407 | AnnotationType:QD (0.08421) |
| 3 | AnnotationType:SOR | 0.08402 | AnnotationType:SOR (0.08416) |
| 4 | AnnotationType:MQ | 0.08266 | AnnotationType:MQ (0.08279) |
| 5 | Concept:GeneticVariant | 0.01928 | Concept:GeneticVariant (0.01931) |
| 6 | Concept:Person | 0.01627 | Concept:Person (0.01629) |
| 7 | Concept:Relative | 0.01577 | Concept:Relative (0.01579) |
| 8 | Concept:SNP | 0.01148 | Concept:SNP (0.01149) |
| 9 | Sample:A | 0.00577 | Sample:A (0.00578) |
| 10 | Gene:BRCA2 | 0.00532 | Gene:BRCA2 (0.00533) |

Перевірка: незалежний `networkx.pagerank` (alpha 0.85) на тому самому графі дає той самий склад топ-10 (перетин 10/10); сума оцінок нативного PageRank = 0.9986. Порядок окремих позицій може відрізнятися через різну обробку вузлів без вихідних зв'язків.

PageRank серед осіб (`MATCH (p:Person) RETURN p.name, p.pagerank`): Maria — 0.0030; Halyna — 0.0027; Olena — 0.0026; Iryna — 0.0022; Petro — 0.0022; Marta — 0.0019; Andrii — 0.0016; Sofiia — 0.0016.

## 2. Louvain: 17 спільнот, модулярність 0.4319

| Спільнота | Вузлів | Склад за мітками | Ключові вузли |
|---|---|---|---|
| 0 | 49 | Annotation 36, Variant 9, Sample 1, Situation 1, Concept 2 | Concept:HighFSSnpVariant, Concept:SNP, Sample:C |
| 1 | 47 | Variant 9, Annotation 35, AnnotationType 1, Gene 1, Threshold 1 | AnnotationType:SOR, Gene:PALB2, Threshold:SOR_gt_3 |
| 2 | 45 | Variant 8, Annotation 34, AnnotationType 1, Gene 1, Threshold 1 | AnnotationType:MQ, Gene:TP53, Threshold:MQ_lt_40 |
| 3 | 42 | Annotation 31, Variant 8, AnnotationType 1, Sample 1, Threshold 1 | AnnotationType:QD, Sample:B, Threshold:QD_lt_2 |
| 4 | 38 | Variant 7, Annotation 25, Situation 2, Concept 4 | Concept:ExonEndVariant, Concept:GeneticVariant, Concept:Indel, Concept:LowQDVariant |
| 5 | 32 | Annotation 23, Variant 7, Gene 1, Sample 1 | Gene:BRCA2, Sample:A |
| 6 | 32 | Annotation 24, Variant 6, Gene 1, GenePanel 1 | Gene:BRCA1, GenePanel:HBOC-panel |
| 7 | 26 | Variant 1, Person 8, Diagnosis 2, Procedure 1, Situation 2, Concept 8, Annotation 4 | Concept:AdultRelative, Concept:FirstDegreeRelative, Concept:MinorRelative, Concept:Person, Concept:Proband |
| 8 | 21 | Variant 2, Threshold 4, Annotation 8, Procedure 1, DataFile 2, Instrument 1, AnnotationType 3 | AnnotationType:FS, AnnotationType:MQRankSum, AnnotationType:ReadPosRankSum, Procedure:HF-01, Threshold:FS_gt_200_indel |
| 9–15 | по 5 | Variant 1 + Annotation 4 | (окремі «зірки» варіантів) |
| 16 | 3 | Concept 2, Situation 1 | DataArtifact, GenePanel |

## 3. Інтерпретація для предметної області

1. Найвищий PageRank мають чотири вузли `AnnotationType` (FS, QD, SOR, MQ — по ≈ 0.08), тобто саме типи анотацій є головними вузлами збору знань: на кожен із них вказує понад шістдесят вузлів-анотацій, і всі правила жорсткої фільтрації (`Threshold`) підключаються через них. Для змісту це означає: зміна визначення або порога для цих показників зачіпає найбільшу частину графа — це підтверджує й запит аналізу впливу c09.
2. Далі йдуть вузли класів `GeneticVariant`, `Person`, `Relative`, `SNP`: ієрархія класів працює як «шини», через які сходяться всі екземпляри; це корисно для запитів із замиканням `SUBCLASS_OF*`, але є артефактом моделі (кожен варіант прив'язаний до класу), а не біологічною важливістю.
3. Серед генів найвищий PageRank у BRCA2 (0.0053): у цьому наборі він має найбільше варіантів (20). Це відображає розмір вибірки в синтетичній когорті, а не клінічну значущість гена; на реальних даних такий висновок був би хибним без нормування.
4. Louvain розбив граф на 17 спільнот; сім найбільших (32–49 вузлів) сформовані навколо хабів — типів анотацій (SOR, MQ, QD), генів (PALB2, TP53, BRCA2, BRCA1), зразків і класів; інакше кажучи, алгоритм здебільшого відтворює «зірки» навколо хабів, а не нові біологічні групи. Модулярність 0.43 помірна.
5. Єдина спільнота з явним доменним змістом — №7 (26 вузлів): усі 8 осіб родини, 2 діагнози, процедура CT-01, ступені споріднення й класи `Relative`/`Proband`. Вона показує, що родинний підграф — окрема когерентна частина бази знань, слабко пов'язана з підграфом якості варіантів (єдиний місток — варіант VAR-001, який носить пробанд). Це пряма підстава зберігати їх як різні модулі й обмінюватись між ними лише через `CARRIES`.
6. Спільнота №8 (21 вузол) об'єднує процедуру HF-01, файли sample1.vcf/.bam, прилад і чотири пороги (FS, MQRankSum, ReadPosRankSum) — «ланцюг походження даних і правил», що узгоджується з аналізом впливу c10.
7. Обмеження: граф малий і синтетичний, тому структура спільнот значною мірою визначається схемою даних (кожна анотація належить рівно одному варіанту та одному типу); Louvain недетермінований без seed, тут seed = 42. Висновки про «значущість» вузлів слід вважати ілюстрацією методу, а не знанням про біологію.

## 4. Збереження результатів у графі

`SET n.pagerank, n.community` виконано для всіх вузлів: з `pagerank` — 370, зі `community` — 370. Перевірка `MATCH (n) RETURN n.community, count(n) ORDER BY count(n) DESC LIMIT 5`: спільнота 0 — 49, спільнота 1 — 47, спільнота 2 — 45, спільнота 3 — 42, спільнота 4 — 38.

## 5. PROFILE

### Запит 1 — c01 (SNP із QD < 2) на графі dkh

```
Results   [записів: 5, 0.001 мс]
  Sort   [записів: 5, 0.002 мс]
    Project   [записів: 5, 0.003 мс]
      Filter   [записів: 5, 0.004 мс]
        Conditional Traverse (v)->(v)   [записів: 6, 0.143 мс]
          Node By Index Scan (a:Annotation)   [записів: 6, 0.036 мс]
```
Час: 0.28 мс.

### Запит 2 — c09 (аналіз впливу порога QD, 5 кроків) на графі dkh

```
Results   [записів: 4, 0.001 мс]
  Sort   [записів: 4, 0.001 мс]
    Aggregate   [записів: 4, 0.077 мс]
      Conditional Traverse (v)->(g:Gene)   [записів: 62, 0.149 мс]
        Conditional Traverse (t)->(v:Variant)   [записів: 62, 0.137 мс]
          Node By Index Scan (t:Threshold)   [записів: 1, 0.007 мс]
```
Час: 0.6 мс.

На малому графі (370 вузлів) обидва запити виконуються за частки мілісекунди й оптимізувати нічого, тому оптимізацію показано на синтетичному графі.

## 6. Оптимізація (синтетичний граф: 20000 варіантів, 100000 вузлів, 80000 зв'язків)

Запит: кількість SNP-варіантів із QD < 2 (відповідь однакова в усіх варіантах: 915; збіг перевірено: True). Значення в синтетичних анотаціях детерміновані (формула від номера варіанта), випадковості немає.

```cypher
// до (Q_BEFORE)
MATCH (v:Variant)-[:HAS_ANNOTATION]->(a:Annotation)
WHERE v.type = 'SNP' AND a.name = 'QD' AND a.value < 2.0
RETURN count(v)
```

PROFILE до оптимізації (без індексу):

```
Results   [записів: 1, 0.001 мс]
  Aggregate   [записів: 1, 0.114 мс]
    Filter   [записів: 915, 0.401 мс]
      Conditional Traverse (v)->(v)   [записів: 1145, 15.302 мс]
        Filter   [записів: 1145, 23.479 мс]
          Node By Label Scan (a:Annotation)   [записів: 80000, 4.92 мс]
```

Крок 1 — переписування шаблону (початок з `Annotation {name:'QD'}`): без індексу план практично той самий (оптимізатор уже починає зі сканування `Annotation`), час не покращився.

```
Results   [записів: 1, 0.001 мс]
  Aggregate   [записів: 1, 0.131 мс]
    Filter   [записів: 915, 0.467 мс]
      Conditional Traverse (v)->(v)   [записів: 1145, 2.03 мс]
        Filter   [записів: 1145, 12.424 мс]
          Node By Label Scan (a:Annotation)   [записів: 80000, 5.27 мс]
```

Крок 2 — індекс: `bg.create_node_range_index('Annotation', 'name', 'value')` (у Neo4j — `CREATE INDEX FOR (a:Annotation) ON (a.name, a.value)`).

PROFILE після (запит Q_BEFORE з індексом):

```
Results   [записів: 1, 0.001 мс]
  Aggregate   [записів: 1, 0.105 мс]
    Filter   [записів: 915, 0.242 мс]
      Conditional Traverse (v)->(v)   [записів: 1145, 1.763 мс]
        Node By Index Scan (a:Annotation)   [записів: 1145, 1.034 мс]
```

| Варіант | Медіана 5 запусків, мс | Сканування Annotation |
|---|---|---|
| до (без індексу) | 13.41 | Node By Label Scan — 80 000 записів |
| переписування, без індексу | 13.27 | Node By Label Scan — 80 000 |
| після (індекс) | 3.31 | Node By Index Scan — 1145 записів |
| переписування + індекс | 4.18 | Node By Index Scan — 1145 |

Висновок: індекс замінив сканування 80 000 вузлів на вибірку 1145, час впав з 13.41 до 3.31 мс (≈ 4.1×); саме по собі переписування запиту нічого не дало. Вимірювання на одному рушії та одній машині; різниця переписування vs. база (15 vs 19 мс) — у межах шуму.
