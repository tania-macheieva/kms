# Перевірка шаблонів ситуацій запитами

Запити виконано до `models/onto.owl` + `models/onto_data.ttl` + виведених HermiT типів. Для кожного шаблона: guard-клас → індивіди, які йому відповідають, і дія/новий стан шаблона.

## S01 — Низький QD (основна перевірка)

Guard: QD < 2; клас: `dkh:LowQDVariant`.

```sparql
SELECT ?xl ?al ?nl WHERE {
  dkh:Situation_S01 dkh:guardClass ?c ; dkh:hasAction ?a ; dkh:hasNewState ?n .
  ?x rdf:type ?c ; rdfs:label ?xl . ?a rdfs:label ?al . ?n rdfs:label ?nl }
ORDER BY ?xl
```

Результат: індивіди ['VAR-002']; дія ['S01: ApplyFlagAction']; новий стан ['S01: FlaggedState']. Очікувалось ['VAR-002'] → **збіг**.

## S02 — Високий FS у SNP

Guard: FS > 60 і варіант є SNP; клас: `dkh:HighFSSnpVariant`.

```sparql
SELECT ?xl ?al ?nl WHERE {
  dkh:Situation_S02 dkh:guardClass ?c ; dkh:hasAction ?a ; dkh:hasNewState ?n .
  ?x rdf:type ?c ; rdfs:label ?xl . ?a rdfs:label ?al . ?n rdfs:label ?nl }
ORDER BY ?xl
```

Результат: індивіди ['VAR-004']; дія ['S02: ApplyFlagAction']; новий стан ['S02: FlaggedState']. Очікувалось ['VAR-004'] → **збіг**.

## S03 — Прапорець FS на кінці екзона

Guard: єдиний прапорець — FS, варіант у кінці екзона, SOR ≤ 3; клас: `dkh:ExonEndVariant`.

```sparql
SELECT ?xl ?al ?nl WHERE {
  dkh:Situation_S03 dkh:guardClass ?c ; dkh:hasAction ?a ; dkh:hasNewState ?n .
  ?x rdf:type ?c ; rdfs:label ?xl . ?a rdfs:label ?al . ?n rdfs:label ?nl }
ORDER BY ?xl
```

Результат: індивіди ['VAR-004']; дія ['S03: ReviewWithSORAction']; новий стан ['S03: UnfilteredState']. Очікувалось ['VAR-004'] → **збіг**.

## S04 — Вибір методу для малої панелі

Guard: панель мала: немає великого набору варіантів і підготовлених відомих ресурсів; клас: `dkh:GenePanel`.

```sparql
SELECT ?xl ?al ?nl WHERE {
  dkh:Situation_S04 dkh:guardClass ?c ; dkh:hasAction ?a ; dkh:hasNewState ?n .
  ?x rdf:type ?c ; rdfs:label ?xl . ?a rdfs:label ?al . ?n rdfs:label ?nl }
ORDER BY ?xl
```

Результат: індивіди ['HBOC-panel']; дія ['S04: SelectHardFilteringAction']; новий стан ['S04: UnfilteredState']. Очікувалось ['HBOC-panel'] → **збіг**.

## S05 — Пропозиція тестування дорослому родичу

Guard: родич повнолітній (вік ≥ 18); починати з родичів першого ступеня (50%); клас: `dkh:AdultRelative`.

```sparql
SELECT ?xl ?al ?nl WHERE {
  dkh:Situation_S05 dkh:guardClass ?c ; dkh:hasAction ?a ; dkh:hasNewState ?n .
  ?x rdf:type ?c ; rdfs:label ?xl . ?a rdfs:label ?al . ?n rdfs:label ?nl }
ORDER BY ?xl
```

Результат: індивіди ['Andrii', 'Halyna', 'Iryna', 'Marta', 'Petro']; дія ['S05: OfferCascadeTestingAction']; новий стан ['S05: TestingOfferedState']. Очікувалось ['Andrii', 'Halyna', 'Iryna', 'Marta', 'Petro'] → **збіг**.

## S06 — Відкладення тестування неповнолітнього (основна перевірка)

Guard: вік родича < 18; клас: `dkh:MinorRelative`.

```sparql
SELECT ?xl ?al ?nl WHERE {
  dkh:Situation_S06 dkh:guardClass ?c ; dkh:hasAction ?a ; dkh:hasNewState ?n .
  ?x rdf:type ?c ; rdfs:label ?xl . ?a rdfs:label ?al . ?n rdfs:label ?nl }
ORDER BY ?xl
```

Результат: індивіди ['Sofiia']; дія ['S06: DeferTestingAction']; новий стан ['S06: TestingDeferredState']. Очікувалось ['Sofiia'] → **збіг**.
