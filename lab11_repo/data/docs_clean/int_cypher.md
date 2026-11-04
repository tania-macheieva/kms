# Результат 3. Запити Cypher та їхні результати

Рушій: FalkorDB (вбудований); запити виконуються лише через read-only виклик. Запити написано в діалекті, спільному з Neo4j 5, окрім двох відмінностей: `shortestPath` у FalkorDB дозволений лише в `RETURN`/`WITH` і лише спрямований. Час — медіана 5 запусків після прогріву (перший виклик запиту суттєво повільніший). Результати генерує `scripts/run_cypher.py`.

| Запит | Конструкції | CQ | Рядків | мс |

| c01_snp_low_qd | MATCH, WHERE, ORDER BY | CQ01 | 5 | 0.43 |
| c02_flags_per_variant | шлях з 4 зв'язків, WITH, collect/size, CASE-логіка у WHERE | CQ05 | 10 | 1.91 |
| c03_per_sample_stats | OPTIONAL MATCH, агрегації count/avg/min/max | CQ08 | 3 | 2.7 |
| c04_genes_optional_pathogenic | OPTIONAL MATCH, WITH, count/collect | CQ14, CQ17 | 4 | 0.57 |
| c05_relatives_varlen | шлях змінної довжини *1..4, min(length) | CQ11–CQ14 | 7 | 0.55 |
| c06_shortest_path | shortestPath, список вузлів шляху | CQ13 | 1 | 0.27 |
| c07_relative_eligibility | JOIN через 3 мітки, CASE | CQ11–CQ15 | 4 | 0.31 |
| c08_concept_hierarchy | змінна довжина *0..4 за ієрархією класів | CQ08 (класифікація) | 3 | 0.36 |
| c09_impact_threshold | аналіз впливу, шлях 5 кроків | Аналіз впливу 1 | 4 | 0.56 |
| c10_impact_bam | аналіз впливу, змінна довжина *1..3 + 2 кроки | Аналіз впливу 2 | 1 | 0.32 |
| c11_proband_panel_path | шлях з 3 зв'язків | CQ17 | 1 | 0.34 |

## 1. `c01_snp_low_qd.cypher` — MATCH, WHERE, ORDER BY

**CQ:** CQ01 — За якого QD SNP-варіант отримує прапорець LowQD?

```cypher
// CQ01: За якого QD SNP-варіант отримує прапорець LowQD? -> SNP із QD < 2.
// Конструкції: MATCH з міткою та властивістю, фільтр WHERE, сортування.
MATCH (v:Variant {type: 'SNP'})-[:HAS_ANNOTATION]->(a:Annotation {name: 'QD'})
WHERE a.value < 2.0
RETURN v.id AS variant, a.value AS qd
ORDER BY qd, variant
```

**Результат:**

| variant | qd |

| VAR-102 | 1.1 |
| VAR-101 | 1.2 |
| VAR-151 | 1.2 |
| VAR-002 | 1.5 |
| VAR-111 | 1.5 |

**Час:** 0.43 мс

**Інтерпретація:** 5 SNP-варіантів мають QD < 2 (1.1–1.5): VAR-102, VAR-101, VAR-151, VAR-002, VAR-111 — ті самі, що дав SPARQL-запит ЛР8 (q01). Варіант із QD = 2.0 не потрапляє (строге «<»).

## 2. `c02_flags_per_variant.cypher` — шлях з 4 зв'язків, WITH, collect/size, CASE-логіка у WHERE

**CQ:** CQ05 — Чи достатньо одного прапорця, щоб відхилити варіант?

```cypher
// CQ05: Чи достатньо одного прапорця, щоб відхилити варіант? -> пороги беруться з ГРАФА (вузли Threshold), а не з тексту запиту.
// Конструкції: шлях з 4 зв'язків, WITH + агрегація collect/count, фільтр після агрегації, CASE.
MATCH (t:Threshold)-[:CHECKS]->(:AnnotationType)<-[:OF_TYPE]-(a:Annotation)<-[:HAS_ANNOTATION]-(v:Variant)
WHERE (t.variantType = 'all' OR t.variantType = toUpper(v.type))
 AND ((t.op = '<' AND a.value < t.value) OR (t.op = '>' AND a.value > t.value))
WITH v, collect(t.id) AS flags
WHERE size(flags) >= 1
RETURN v.id AS variant, size(flags) AS nFlags, flags
ORDER BY nFlags DESC, variant
LIMIT 10
```

**Результат:**

| variant | nFlags | flags |

| VAR-122 | 3 | [FS_gt_60_snp, MQ_lt_40, SOR_gt_3] |
| VAR-101 | 2 | [QD_lt_2, SOR_gt_3] |
| VAR-102 | 2 | [QD_lt_2, SOR_gt_3] |
| VAR-108 | 2 | [FS_gt_200_indel, MQ_lt_40] |
| VAR-111 | 2 | [QD_lt_2, SOR_gt_3] |
| VAR-121 | 2 | [MQ_lt_40, QD_lt_2] |
| VAR-148 | 2 | [MQ_lt_40, SOR_gt_3] |
| VAR-151 | 2 | [MQ_lt_40, QD_lt_2] |
| VAR-158 | 2 | [FS_gt_60_snp, MQ_lt_40] |
| VAR-002 | 1 | [QD_lt_2] |

**Час:** 1.91 мс

**Інтерпретація:** Пороги читаються з вузлів Threshold, тому зміна порога в графі змінює відповідь без правки запиту. Варіант із ≥ 1 прапорцем вважається FILTERED; у топі — варіанти з кількома прапорцями одночасно (напр., VAR-122: FS, MQ і SOR).

## 3. `c03_per_sample_stats.cypher` — OPTIONAL MATCH, агрегації count/avg/min/max

**CQ:** CQ08 — Який метод фільтрації обрати для малої панелі?

```cypher
// CQ08: Який обсяг даних і яка якість по зразках (чи малий набір для VQSR)?
// Конструкції: агрегації count/avg/min/max з групуванням за зразком.
MATCH (v:Variant)-[:FROM_SAMPLE]->(s:Sample)
OPTIONAL MATCH (v)-[:HAS_ANNOTATION]->(a:Annotation {name: 'QD'})
RETURN s.code AS sample, count(DISTINCT v) AS variants, round(avg(a.value) * 100) / 100 AS avgQD, min(a.value) AS minQD, max(a.value) AS maxQD
ORDER BY sample
```

**Результат:**

| sample | variants | avgQD | minQD | maxQD |

| A | 24 | 15.14 | 1.1 | 34.9 |
| B | 20 | 15.58 | 1.5 | 34.5 |
| C | 20 | 16.92 | 1.2 | 30.3 |

**Час:** 2.7 мс

**Інтерпретація:** У кожному зразку 20–24 варіанти; для такого малого набору GATK радить hard-filtering замість VQSR (ЛР4). Середній QD ≈ 15–17, мінімум 1.1–1.5 — є кандидати на LowQD.

## 4. `c04_genes_optional_pathogenic.cypher` — OPTIONAL MATCH, WITH, count/collect

**CQ:** CQ14, CQ17 — З кого починати тестування; чи варто тестувати панель, що включає ген родини?

```cypher
// CQ14/CQ17: Які гени панелі мають патогенні варіанти (і які — жодного)?
// Конструкції: OPTIONAL MATCH (гени без патогенних варіантів не зникають), WITH, умовний підрахунок.
MATCH (:GenePanel {name: 'HBOC-panel'})-[:HAS_MEMBER]->(g:Gene)
OPTIONAL MATCH (g)<-[:LOCATED_IN]-(v:Variant)
WHERE v.clinicalSignificance = 'Pathogenic'
WITH g, count(v) AS pathogenic, collect(v.id) AS ids
RETURN g.symbol AS gene, pathogenic, ids
ORDER BY pathogenic DESC, gene
```

**Результат:**

| gene | pathogenic | ids |

| PALB2 | 2 | [VAR-103, VAR-131] |
| BRCA1 | 1 | [VAR-001] |
| TP53 | 1 | [VAR-152] |
| BRCA2 | 0 | [] |

**Час:** 0.57 мс

**Інтерпретація:** У панелі HBOC патогенні варіанти є в PALB2 (VAR-103, VAR-131), BRCA1 (VAR-001) і TP53 (VAR-152); BRCA2 залишається у відповіді з нулем завдяки OPTIONAL MATCH.

## 5. `c05_relatives_varlen.cypher` — шлях змінної довжини *1..4, min(length)

**CQ:** CQ11–CQ14 — Хто з родичів пробанда і наскільки далеко?

```cypher
// CQ11-CQ13/CQ14: Хто є родичем пробанда Olena і через скільки родинних кроків?
// Конструкції: шлях змінної довжини *1..4 за кількома типами зв'язків без напрямку, DISTINCT, агрегація min(length).
MATCH p = (o:Person {name: 'Olena'})-[:HAS_PARENT|HAS_SIBLING*1..4]-(r:Person)
WHERE r <> o
RETURN r.name AS relative, min(length(p)) AS steps
ORDER BY steps, relative
```

**Результат:**

| relative | steps |

| Iryna | 1 |
| Marta | 1 |
| Petro | 1 |
| Sofiia | 1 |
| Halyna | 2 |
| Maria | 2 |
| Andrii | 3 |

**Час:** 0.55 мс

**Інтерпретація:** Від Olena досяжні 7 осіб: 1 крок — Iryna, Petro, Marta, Sofiia; 2 кроки — Halyna, Maria; 3 кроки — Andrii. Кількість кроків — груба міра віддаленості (дочка Sofiia теж 1 крок, бо шлях не має напрямку).

## 6. `c06_shortest_path.cypher` — shortestPath, список вузлів шляху

**CQ:** CQ13 — Який шлях до більш віддаленого родича (бабусі)?

```cypher
// CQ13: Яка найкоротша родинна лінія від пробанда до Maria?
// Конструкції: shortestPath (у FalkorDB — лише в RETURN/WITH і лише спрямований).
MATCH (a:Person {name: 'Olena'}), (b:Person {name: 'Maria'})
WITH shortestPath((a)-[:HAS_PARENT*]->(b)) AS p
RETURN length(p) AS hops, [n IN nodes(p) | n.name] AS line
```

**Результат:**

| hops | line |

| 2 | [Olena, Iryna, Maria] |

**Час:** 0.27 мс

**Інтерпретація:** Найкоротша лінія від Olena до Maria — 2 кроки: Olena → Iryna → Maria (мати — бабуся пробанда).

## 7. `c07_relative_eligibility.cypher` — JOIN через 3 мітки, CASE

**CQ:** CQ11–CQ15 — Шанс успадкування і чи можна тестувати родича (вік ≥ 18)?

```cypher
// CQ11-CQ15: шанс успадкування (з вузла Concept), вік і чи можна тестувати відповідно до процедури CT-01.
// Конструкції: JOIN через три мітки, WHERE, обчислюваний стовпець, ORDER BY.
MATCH (c:Procedure {id: 'CT-01'})-[:APPLIES_TO]->(p:Person)-[:INSTANCE_OF]->(k:Concept)
WHERE k.probability IS NOT NULL
RETURN p.name AS person, k.name AS degree, k.probability AS probability, p.ageYears AS age,
 CASE WHEN p.ageYears >= c.minTestingAge THEN 'так' ELSE 'ні' END AS canTest
ORDER BY probability DESC, person
```

**Результат:**

| person | degree | probability | age | canTest |

| Marta | FirstDegreeRelative | 0.5 | 39 | так |
| Sofiia | FirstDegreeRelative | 0.5 | 17 | ні |
| Halyna | SecondDegreeRelative | 0.25 | 65 | так |
| Andrii | ThirdDegreeRelative | 0.125 | 40 | так |

**Час:** 0.31 мс

**Інтерпретація:** Шанс береться з Concept-вузла ступеня (0.5 / 0.25), вік — з Person. Sofiia (17 років) має шанс 0.5, але тестування «ні» (мін. вік 18, CQ15). Процедура CT-01 застосовується лише до 4 осіб: Marta, Sofiia, Halyna, Andrii (Andrii: ступінь 3, шанс 0.125 — див. таблицю).

## 8. `c08_concept_hierarchy.cypher` — змінна довжина *0..4 за ієрархією класів

**CQ:** CQ08 (класифікація) — Скільки варіантів належить кожному класу з урахуванням підкласів?

```cypher
// Скільки варіантів належить кожному предку в ієрархії класів (INSTANCE_OF + SUBCLASS_OF*)?
// Конструкції: змінна довжина *0..4 (0 = сам клас), агрегація за предком.
MATCH (v:Variant)-[:INSTANCE_OF]->(:Concept)-[:SUBCLASS_OF*0..4]->(anc:Concept)
RETURN anc.name AS concept, count(DISTINCT v) AS variants
ORDER BY variants DESC, concept
```

**Результат:**

| concept | variants |

| GeneticVariant | 64 |
| SNP | 46 |
| Indel | 18 |

**Час:** 0.36 мс

**Інтерпретація:** SNP — 46, Indel — 18, разом GeneticVariant — 64: замикання SUBCLASS_OF* дає ту саму підсумкову класифікацію, що в OWL, але без reasoner — шлях обчислюється під час запиту.

## 9. `c09_impact_threshold.cypher` — аналіз впливу, шлях 5 кроків

**CQ:** Аналіз впливу 1 — Якщо змінити поріг QD, на які варіанти й гени це вплине?

```cypher
// АНАЛІЗ ВПЛИВУ 1: Якщо змінити поріг QD_lt_2 — на які варіанти та гени це вплине? (залежності на 5 кроків)
// Threshold -CHECKS-> AnnotationType <-OF_TYPE- Annotation <-HAS_ANNOTATION- Variant -LOCATED_IN-> Gene
MATCH (t:Threshold {id: 'QD_lt_2'})-[:CHECKS]->(:AnnotationType)<-[:OF_TYPE]-(:Annotation)<-[:HAS_ANNOTATION]-(v:Variant)-[:LOCATED_IN]->(g:Gene)
RETURN g.symbol AS gene, count(DISTINCT v) AS variantsAffected
ORDER BY variantsAffected DESC, gene
```

**Результат:**

| gene | variantsAffected |

| BRCA2 | 18 |
| TP53 | 16 |
| BRCA1 | 14 |
| PALB2 | 14 |

**Час:** 0.56 мс

**Інтерпретація:** Зміна QD_lt_2 торкнеться всіх варіантів, що мають анотацію QD, у 4 генах: BRCA2 — 18, TP53 — 16, BRCA1 — 14, PALB2 — 14 варіантів. Це оцінка «радіуса ураження» зміни правила.

## 10. `c10_impact_bam.cypher` — аналіз впливу, змінна довжина *1..3 + 2 кроки

**CQ:** Аналіз впливу 2 — Якщо sample1.bam буде перероблено, які залежні файли, процедури й пороги треба перевірити?

```cypher
// АНАЛІЗ ВПЛИВУ 2: Якщо sample1.bam буде перероблено — що залежить від нього (глибина до 4)?
// BAM <-DERIVED_FROM*- файли; процедури, що застосовуються до цих файлів; пороги цих процедур.
MATCH (f:DataFile {id: 'sample1_bam'})<-[:DERIVED_FROM*1..3]-(d:DataFile)<-[:APPLIES_TO]-(proc:Procedure)-[:HAS_THRESHOLD]->(t:Threshold)
RETURN d.id AS derivedFile, proc.id AS procedure, count(t) AS thresholdsToRecheck, collect(t.id) AS thresholds
```

**Результат:**

| derivedFile | procedure | thresholdsToRecheck | thresholds |

| sample1_vcf | HF-01 | 7 | [FS_gt_200_indel, FS_gt_60_snp, MQRankSum_lt_-12.5, MQ_lt_40, QD_lt_2, ReadPosRankSum_lt_-8, SOR_gt_3] |

**Час:** 0.32 мс

**Інтерпретація:** Від sample1.bam залежить sample1.vcf (DERIVED_FROM), до нього застосовується HF-01, що має 7 порогів: усі 7 потрібно перевірити (глибина залежності 3 кроки + порогів).

## 11. `c11_proband_panel_path.cypher` — шлях з 3 зв'язків

**CQ:** CQ17 — Чи потрапляє варіант пробанда в ген панелі?

```cypher
// CQ17: Чи потрапляє варіант пробанда в ген панелі, для якої доречне каскадне тестування? (шлях з 3 зв'язків)
MATCH (p:Person {proband: true})-[:CARRIES]->(v:Variant)-[:LOCATED_IN]->(g:Gene)<-[:HAS_MEMBER]-(panel:GenePanel)
RETURN p.name AS proband, v.id AS variant, v.clinicalSignificance AS significance, g.symbol AS gene, panel.name AS panel
```

**Результат:**

| proband | variant | significance | gene | panel |

| Olena | VAR-001 | Pathogenic | BRCA1 | HBOC-panel |

**Час:** 0.34 мс

**Інтерпретація:** Olena носить VAR-001 (Pathogenic) у BRCA1, що входить до HBOC-panel: це умова для пропозиції каскадного тестування родичів.

## Ручна перевірка

Результати шести запитів звірено з незалежним обчисленням звичайним Python-кодом по CSV-файлах (без Cypher і без бази) — `scripts/verify_manual.py`; для c05 і c06 додатково — ручний розбір малого підграфа (родина з 8 осіб, 8 зв'язків HAS_PARENT і 3 HAS_SIBLING).

| Запит | Спосіб | Збіг |

| c01 | Python-цикл по Variant/Annotation CSV | так |
| c02 | перерахунок порогів у Python; перевірено 10 найбільших (за кількістю прапорців) і загальну кількість варіантів із прапорцями | так |
| c03 | групування в Python (Decimal, ROUND_HALF_UP для середнього) | так |
| c04 | підрахунок патогенних варіантів у генах панелі | так |
| c05 | BFS у Python по HAS_PARENT/HAS_SIBLING (без напрямку) + ручний розбір | так |
| c09 | підрахунок варіантів із анотацією QD по генах | так |

**Ручний розбір c05 (мала родина).** Рядки CSV: HAS_PARENT — Halyna→Maria, Andrii→Halyna, Iryna→Maria, Marta→Iryna, Marta→Petro, Olena→Iryna, Olena→Petro, Sofiia→Olena; HAS_SIBLING — Iryna→Halyna, Marta→Olena, Olena→Marta. Від Olena: Iryna, Petro (батьки), Marta (сестра), Sofiia (дочка) — 1 крок; Halyna (сестра Iryna) і Maria (мати Iryna) — 2 кроки; Andrii (дитина Halyna) — 3 кроки. Збігається з таблицею запиту c05.

**Знахідка про рушій.** `toFloat()` у FalkorDB повертає значення з точністю float32 (`toFloat('1.1')` = 1.10000002384186, і тоді `a.value = 1.2` хибне). Тому в `import/*.cypher` значення округлено `round(toFloat(x)*1000)/1000`. Без цього порівняння на межі порога могли б давати хибний результат.
