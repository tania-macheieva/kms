"""Шаблони ситуацій (джерело для models/situations.csv та індивідів у onto_data.ttl)."""
# id, назва, початковий стан(клас), подія(клас), guard-текст, guardClass, новий стан(клас), дія(клас), наслідок, сенсор/джерело, джерело
S = [
 ("S01", "Низький QD", "UnfilteredState", "AnnotationComputedEvent", "QD < 2", "LowQDVariant", "FlaggedState", "ApplyFlagAction",
  "Варіант отримує прапорець LowQD; будь-який прапорець → варіант буде відхилено (FILTERED)", "Sequencer", "gatk; CQ01, CQ05"),
 ("S02", "Високий FS у SNP", "UnfilteredState", "AnnotationComputedEvent", "FS > 60 і варіант є SNP", "HighFSSnpVariant", "FlaggedState", "ApplyFlagAction",
  "Варіант отримує прапорець HighFS (для INDEL поріг 200)", "Sequencer", "gatk; CQ02, CQ03"),
 ("S03", "Прапорець FS на кінці екзона", "FlaggedState", "AnnotationComputedEvent", "єдиний прапорець — FS, варіант у кінці екзона, SOR ≤ 3", "ExonEndVariant", "UnfilteredState", "ReviewWithSORAction",
  "Варіант не відкидають автоматично: додатково перевіряють SOR і передають на ручний перегляд (FS штрафує кінці екзонів)", "Sequencer", "gatk; CQ07"),
 ("S04", "Вибір методу для малої панелі", "UnfilteredState", "MethodChoiceEvent", "панель мала: немає великого набору варіантів і підготовлених відомих ресурсів", "GenePanel", "UnfilteredState", "SelectHardFilteringAction",
  "Обрано hard filtering, бо VQSR потребує великого набору й відомих ресурсів", "—", "gatk; CQ08"),
 ("S05", "Пропозиція тестування дорослому родичу", "UntestedState", "PathogenicVariantFoundEvent", "родич повнолітній (вік ≥ 18); починати з родичів першого ступеня (50%)", "AdultRelative", "TestingOfferedState", "OfferCascadeTestingAction",
  "Родичу пропонують тестування, першочергово — першого ступеня; консультування", "—", "cdc; CQ11, CQ14"),
 ("S06", "Відкладення тестування неповнолітнього", "UntestedState", "TestingRequestedEvent", "вік родича < 18", "MinorRelative", "TestingDeferredState", "DeferTestingAction",
  "Тестування відкладено до 18 років (виняток — ризики раку в дитинстві, рішення консультанта)", "—", "cdc; CQ15"),
]
