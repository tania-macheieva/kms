# Результат 1. Графова схема під CQ

Схема: `docs/graph_schema.png` (джерело `graph_schema.dot`, SVG — `graph_schema.svg`). **14 міток** (Variant, Annotation, AnnotationType, Gene, GenePanel, Sample, Person, Diagnosis, Threshold, Procedure, DataFile, Instrument, Situation, Concept) і **19 типів зв'язків** (LOCATED_IN, FROM_SAMPLE, HAS_ANNOTATION, OF_TYPE, CHECKS, HAS_THRESHOLD, HAS_MEMBER, HAS_PARENT, HAS_SIBLING, CARRIES, HAS_DIAGNOSIS, APPLIES_TO, HAS_PROBAND, REQUIRES, DERIVED_FROM, GENERATED_BY, GUARD_CLASS, INSTANCE_OF, SUBCLASS_OF; 21 CSV-файл зі зв'язками, бо APPLIES_TO та INSTANCE_OF мають по два варіанти кінців). Дані — `data/*.csv` (370 вузлів, 757 зв'язків), побудовані з RDF-графа ЛР8 (`scripts/build_csv.py`).

## 1. Відображення CQ на шаблони шляхів

Джерело CQ — `docs/cq_lab4.md` (18 CQ ЛР4). Нижче 12 CQ; «Запит» — файл у `queries/`, де шаблон реалізовано і виконано (позначка «лише шаблон» — реалізація не робилась).

| CQ | Запитання | Шаблон шляху (Cypher) | Запит |
|---|---|---|---|
| CQ01 | За якого QD SNP отримує прапорець LowQD? | `(v:Variant {type:'SNP'})-[:HAS_ANNOTATION]->(a:Annotation {name:'QD'})` + `a.value < 2` | c01 |
| CQ02 | За якого FS SNP відкидають? | те саме з `name:'FS'`, `a.value > 60` | лише шаблон (покрито c02 через Threshold) |
| CQ03 | Який поріг FS для INDEL? | `(t:Threshold {annotation:'FS', variantType:'INDEL'})` → `t.value` | лише шаблон (є в c02: `FS_gt_200_indel`) |
| CQ05 | Чи достатньо одного прапорця? | `(t:Threshold)-[:CHECKS]->(:AnnotationType)<-[:OF_TYPE]-(a)<-[:HAS_ANNOTATION]-(v)` + `WITH v, collect(t)` | c02 |
| CQ07 | Варіант на кінці екзона лише з LowFS → перегляд | `(v:Variant {exonEnd:true})` + прапорці з c02 | лише шаблон |
| CQ08 | Який метод фільтрації для малої панелі? | `(v:Variant)-[:FROM_SAMPLE]->(s:Sample)` + `count(v)` | c03, c08 |
| CQ11 | Шанс успадкування для сиблінга | `(p:Person)-[:INSTANCE_OF]->(k:Concept {name:'FirstDegreeRelative'})` → `k.probability` | c07 |
| CQ12 | Шанс для тітки/бабусі | `(p)-[:INSTANCE_OF]->(:Concept {name:'SecondDegreeRelative'})` | c07 |
| CQ13 | Шанс для двоюрідних і далі; шлях до бабусі | `(o:Person)-[:HAS_PARENT\|HAS_SIBLING*1..4]-(r)`; `shortestPath((o)-[:HAS_PARENT*]->(g))` | c05, c06, c07 |
| CQ14 | З кого починати тестування | `(p)-[:CARRIES]->(v)-[:LOCATED_IN]->(g)<-[:HAS_MEMBER]-(panel)` + родичі з c05 | c04, c05, c11 |
| CQ15 | Чи можна тестувати 17-річного? | `(c:Procedure)-[:APPLIES_TO]->(p:Person)` + `p.ageYears >= c.minTestingAge` | c07 |
| CQ17 | Чи доречна панель з геном родини? | `(p:Person {proband:true})-[:CARRIES]->(v)-[:LOCATED_IN]->(g)<-[:HAS_MEMBER]-(:GenePanel)` | c04, c11 |

Додатково (поза переліком ЛР4, аналіз впливу): c09 — `(:Threshold)-[:CHECKS]->(:AnnotationType)<-[:OF_TYPE]-(:Annotation)<-[:HAS_ANNOTATION]-(:Variant)-[:LOCATED_IN]->(:Gene)` (5 кроків); c10 — `(:DataFile)<-[:DERIVED_FROM*1..3]-(:DataFile)<-[:APPLIES_TO]-(:Procedure)-[:HAS_THRESHOLD]->(:Threshold)`.

## 2. Властивості походження на зв'язках

На **кожному** зв'язку: `source` (рядок: `lab7-abox` — факти ЛР7, `synthetic-seed42` — синтетична когорта, `gatk` / `cdc` — правила з джерел ЛР4, `hermit` — виведено reasoner'ом), `confidence` (число 0.8–1.0: 1.0 — заявлено в джерелі/ЛР7, 0.95 — виведено HermiT, 0.8 — синтетичні дані) і `validFrom` (дата завантаження, 2026-10-26). Розподіл за джерелами можна отримати запитом `MATCH ()-[r]->() RETURN r.source, count(*)`. Значення `confidence` — моє призначення за категорією походження, а не статистична оцінка.

## 3. Порівняння зі схемою ЛР7 (онтологія)

| Елемент ЛР7 (OWL) | У графі (LPG) | Що змінилося / що втрачено |
|---|---|---|
| Клас `SNP`, `Indel` (підкласи `GeneticVariant`) | мітка `Variant` + властивість `type` + зв'язок `INSTANCE_OF` на вузол `Concept` | підклас став значенням властивості; ієрархія збережена вузлами `Concept` і `SUBCLASS_OF` |
| Класи `QualityByDepth`, `FisherStrandBias`, … | мітка `Annotation` + властивість `name` + вузол `AnnotationType` | чотири класи → одна мітка; відмінність — значення властивості |
| Індивід-ген (`BRCA1`…) | мітка `Gene` (вузол) | клас-в-онтології стає міткою; індивід — вузлом |
| Object property `hasParent`, `locatedIn` | типи зв'язків `HAS_PARENT`, `LOCATED_IN` | domain/range не перевіряються рушієм (контроль — лише обмеженнями на властивості) |
| Data property `hasAgeYears`, `hasNumericValue` | властивості вузлів `ageYears`, `value` | типи даних xsd → типи значень (int, float) |
| Означений клас `LowQDVariant`, `FlaggedVariant` (≡) | **немає класу**: обчислюється запитом c02 за порогами в графі | втрата автоматичної класифікації reasoner'ом; правило живе в запиті |
| Обмеження `owl:hasValue` (шанс успадкування) | властивість `probability` на вузлі `Concept` | логічна аксіома стала даними |
| Транзитивні властивості, ланцюги (`hasGrandparent`) | змінна довжина `*1..n` у запиті | виведення замінено обходом під час запиту |
| `AllDisjointClasses`, кардинальності | **не відтворюється**; частково — унікальні обмеження | втрата |
| `SituationTemplate` та метаонтологія (Event, State, Action) | мітка `Situation` (лише guard і назва) | частково: стани й дії не вузли |
| Походження фактів (немає в ЛР7) | `source`, `confidence`, `validFrom` на зв'язках | **нове** в LPG-моделі |
