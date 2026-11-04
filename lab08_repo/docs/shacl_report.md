# Результат 3. SHACL-форми та валідація

Інструмент: pySHACL 0.40.1, `inference='none'` (форми перевіряють дані «як є», без виведення), `allow_warnings=True`. Дані: `data/kb.ttl` (TBox + ABox + виведене HermiT, 3923 тріпли). Форми: `shapes/shapes.ttl`.

## 1. Форми та обмеження

Усього: 9 вузлових форм, 18 форм властивостей, 43 обмежень. За типами: minCount — 15, maxCount — 7, datatype — 5, pattern — 2, class — 7, minInclusive — 3, in — 3, maxInclusive — 1.

| Форма | Цільовий клас | Обмеження |
|---|---|---|
| `AnnotationShape` | dkh:QualityAnnotation | `dkh:hasNumericValue`: minCount=1, maxCount=1, datatype=xsd:decimal<br>`dkh:hasAnnotationName`: minCount=1, in=(QD FS SOR MQ MQRankSum ReadPosRankSum)<br>`dkh:isAnnotationOf`: minCount=1, class=dkh:GeneticVariant |
| `CascadeTestingShape` | dkh:CascadeTesting | `dkh:hasProband`: minCount=1, maxCount=1, class=dkh:Proband<br>`dkh:hasMinTestingAge`: minCount=1, datatype=xsd:integer, minInclusive=0<br>`dkh:appliesTo`: minCount=1, class=dkh:Person |
| `FullAnnotationSetWarning` | dkh:GeneticVariant | `dkh:hasAnnotation`: minCount=4 **(Warning)** |
| `GenePanelShape` | dkh:GenePanel | `dkh:hasMember`: minCount=1, class=dkh:Gene |
| `NonNegativeAnnotationShape` | dkh:QualityByDepth, dkh:FisherStrandBias, dkh:StrandOddsRatio | `dkh:hasNumericValue`: minInclusive=0 |
| `PersonShape` | dkh:Person | `dkh:hasAgeYears`: maxCount=1, datatype=xsd:integer, minInclusive=0, maxInclusive=120<br>`dkh:hasParent`: maxCount=2, class=dkh:Person |
| `SampleShape` | dkh:Sample | `dkh:hasSampleCode`: minCount=1, maxCount=1, pattern=^[A-Z]$ |
| `ThresholdShape` | dkh:FilterThreshold | `dkh:hasThresholdValue`: minCount=1, maxCount=1, datatype=xsd:decimal<br>`dkh:hasComparisonOperator`: minCount=1, in=(< >)<br>`dkh:onAnnotationName`: minCount=1, in=(QD FS SOR MQ MQRankSum ReadPosRankSum) |
| `VariantShape` | dkh:GeneticVariant | `dkh:hasVariantId`: minCount=1, maxCount=1, datatype=xsd:string, pattern=^VAR-[0-9]{3}$<br>`dkh:locatedIn`: minCount=1, class=dkh:Gene<br>`dkh:hasAnnotation`: minCount=1, class=dkh:QualityAnnotation |

Покриття типів: **кількісні** (minCount/maxCount), **типи даних** (datatype xsd:string/decimal/integer), **клас значення** (sh:class), **діапазон** (minInclusive/maxInclusive), **шаблон** (pattern: `^VAR-[0-9]{3}$`, `^[A-Z]$`), **перелік** (sh:in).

## 2. Валідний набір

Результат: `conforms = True`. Порушень рівня Violation — 0, попереджень — 3.

| Рівень | Вузол | Шлях | Компонент | Значення |
|---|---|---|---|---|
| Warning | dkh:VAR-002 | dkh:hasAnnotation | MinCount | — |
| Warning | dkh:VAR-003 | dkh:hasAnnotation | MinCount | — |
| Warning | dkh:VAR-004 | dkh:hasAnnotation | MinCount | — |


**Коментар (чесно про налаштування форм).** Перша версія форми вимагала від кожного варіанта 4 анотації (`minCount 4`) — і валідний набір «провалився»: VAR-002, VAR-003, VAR-004 (приклади з ЛР7) мають неповний набір анотацій. Це справжня знахідка про дані, а не про форму. Я зробив вимогу «хоч одна анотація» обов'язковою (Violation), а «повний набір з 4» — окремою формою рівня Warning. Це рішення прийняв я після побачених результатів, тобто форму підігнано під дані; тому в цьому звіті попередження залишено видимими, а не приховано. Варіанти для вирішення: доповнити дані ЛР7 або ухвалити, що неповні набори допустимі.

Звіт: `shapes/report_valid.ttl`.

## 3. Дефектний набір (3 навмисні вади)

`data/kb_defective.ttl` — копія `kb.ttl` із трьома змінами (створено `scripts/shacl_check.py`):

| № | Вада | Тип обмеження | Що змінено |
|---|---|---|---|
| D1 | Варіант без гена | minCount | у VAR-105 видалено `dkh:locatedIn` |
| D2 | Хибний формат ідентифікатора | pattern | `hasVariantId` у VAR-106: `variant_106` замість `VAR-106` |
| D3 | Нереальний вік | діапазон (maxInclusive) | `hasAgeYears` у Marta: 391 |

Результат: `conforms = False`.

| Рівень | Вузол | Шлях | Компонент | Значення |
|---|---|---|---|---|
| Violation | dkh:Marta | dkh:hasAgeYears | MaxInclusive | 391 |
| Violation | dkh:VAR-105 | dkh:locatedIn | MinCount | — |
| Violation | dkh:VAR-106 | dkh:hasVariantId | Pattern | variant_106 |
| Warning | dkh:VAR-002 | dkh:hasAnnotation | MinCount | — |
| Warning | dkh:VAR-003 | dkh:hasAnnotation | MinCount | — |
| Warning | dkh:VAR-004 | dkh:hasAnnotation | MinCount | — |


Кожна вада дала рівно одне порушення рівня Violation (3 з 3); три попередження про VAR-002…004 — ті самі, що й у валідному наборі. Звіт: `shapes/report_defective.ttl`. У повідомленнях звіту є вузол, шлях і значення, тож помилку видно без ручного пошуку.

## 4. Чому SHACL, а не лише OWL

OWL працює за припущенням **відкритого світу** і не має «унікальних імен»: відсутність факту не є помилкою, а лише невідомістю. Якщо в OWL-аксіомі сказано, що варіант розташований у гені, а в даних гена немає, міркувальник просто припускає, що ген існує, але не названий. SHACL працює за **закритим світом** і перевіряє наявні дані: відсутня властивість, рядок замість числа чи вік 391 — це порушення, яке можна показати з точним вузлом і повідомленням. Тому OWL добре підходить для виведення нових знань (класифікація, ступінь родича), а SHACL — для контролю якості даних перед завантаженням; у цьому проєкті вони доповнюють одне одного.

**Експеримент.**

1. HermiT на дефектному наборі (D1–D3): `consistent = True`. OWL не бачить жодної з трьох вад (відсутній ген, довільний рядок, вік 391 допустимі при відкритому світі), тоді як SHACL знаходить усі три.
2. Хибний тип: у копії даних VAR-107 `locatedIn` вказує на Olena (особа, а не ген). HermiT: `consistent = False` — онтологія стала неузгодженою (імовірно, через дизʼюнктність класів Person і Gene та range = Gene; які саме аксіоми зіткнулися, я не розбирав). Отже, цю помилку OWL теж «помічає», але лише загальним «Inconsistent ontology»: без вказівки на вузол, а після цього жодне виведення вже неможливе. SHACL у тому ж випадку: `conforms = False`, порушення на `dkh:VAR-107` / `dkh:locatedIn` зі значенням `dkh:Olena` — і решта графа лишається придатною.

Результати експерименту: `shapes/owl_vs_shacl.json` (`scripts/owl_vs_shacl.py`).

## 5. Обмеження

- Форми написані мною для моєї ж онтології; незалежної перевірки їхньої повноти немає.
- Вади навмисні й прості; реальні помилки даних (напр., неправильна полярність порога) SHACL не знайде.
- Дані синтетичні (когорта VAR-101…160 згенерована, seed 42).
- pySHACL запущено без `ont_graph`/виведення; `sh:targetClass` враховує підкласи завдяки TBox, який входить у `kb.ttl`.
