# Журнал імпорту (Результат 2)

- Дата: 2026-10-28 21:18:57 (Europe/Kiev)
- Рушій: FalkorDB (вбудований, falkordblite 0.11.0) — не Neo4j; див. README.
- Імпорт: `import/01_nodes.cypher`, `import/02_rels.cypher` (LOAD CSV + MERGE), CSV — `data/*.csv`.

## Кількості (перший імпорт, 44 мс)

Вузлів: **370**, зв'язків: **757**.

| Мітка | Вузлів |
|---|---|
| Annotation | 248 |
| AnnotationType | 6 |
| Concept | 16 |
| DataFile | 2 |
| Diagnosis | 2 |
| Gene | 4 |
| GenePanel | 1 |
| Instrument | 1 |
| Person | 8 |
| Procedure | 2 |
| Sample | 3 |
| Situation | 6 |
| Threshold | 7 |
| Variant | 64 |

| Тип зв'язку | Кількість |
|---|---|
| APPLIES_TO | 5 |
| CARRIES | 1 |
| CHECKS | 7 |
| DERIVED_FROM | 1 |
| FROM_SAMPLE | 64 |
| GENERATED_BY | 2 |
| GUARD_CLASS | 6 |
| HAS_ANNOTATION | 248 |
| HAS_DIAGNOSIS | 2 |
| HAS_MEMBER | 4 |
| HAS_PARENT | 8 |
| HAS_PROBAND | 1 |
| HAS_SIBLING | 3 |
| HAS_THRESHOLD | 7 |
| INSTANCE_OF | 72 |
| LOCATED_IN | 64 |
| OF_TYPE | 248 |
| REQUIRES | 1 |
| SUBCLASS_OF | 13 |

## Ідемпотентність (повторний імпорт, 34 мс)

Після другого запуску: вузлів 370, зв'язків 757; розбивка за мітками й типами **збігається** з першою.

## Обмеження (`CALL db.constraints()`, аналог `SHOW CONSTRAINTS`)

| Тип | Мітка | Властивості | Об'єкт | Стан |
|---|---|---|---|---|
| UNIQUE | Threshold | id | NODE | OPERATIONAL |
| UNIQUE | Sample | code | NODE | OPERATIONAL |
| UNIQUE | Annotation | id | NODE | OPERATIONAL |
| UNIQUE | Person | name | NODE | OPERATIONAL |
| UNIQUE | Gene | symbol | NODE | OPERATIONAL |
| UNIQUE | Variant | id | NODE | OPERATIONAL |

## Індекси (`CALL db.indexes()`, аналог `SHOW INDEXES`)

| Мітка | Властивості | Тип | Стан |
|---|---|---|---|
| Threshold | id | ['RANGE'] | OPERATIONAL |
| Sample | code | ['RANGE'] | OPERATIONAL |
| Annotation | id, name, value | ['RANGE'] | OPERATIONAL |
| Person | name, ageYears | ['RANGE'] | OPERATIONAL |
| Gene | symbol | ['RANGE'] | OPERATIONAL |
| Variant | id, type | ['RANGE'] | OPERATIONAL |

## Порушення обмеження

`CREATE (:Variant {id: 'VAR-001', type: 'SNP'})`

Відповідь сервера: `unique constraint violation on node of type Variant`

`CREATE (:Gene {symbol: 'BRCA1'})`

Відповідь сервера: `unique constraint violation on node of type Gene`

Після спроб порушення граф не змінився: 370 вузлів, 757 зв'язків.
