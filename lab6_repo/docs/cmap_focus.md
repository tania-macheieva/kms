# Результат 1. Фокусне питання, parking lot і каталог відношень

## 1. Фокусне питання

> **Як якість анотацій варіантів і родинний генетичний ризик перетворюються на рішення — які варіанти відкинути під час жорсткої фільтрації і яких родичів пробанда з BRCA1/BRCA2 тестувати в першу чергу?**

Питання відкрите (починається з «як», не має відповіді «так/ні»), змістовне й пов'язане з нашою проблемою — підтримкою рішень щодо якості геномних варіантів та каскадного тестування. Воно задає межі карти: два кластери (контроль якості варіантів, клінічне тестування) і зв'язки між ними через геномні поняття.

## 2. Parking lot (33 поняття + 6 екземплярів), від загальних до часткових

Усі поняття взято зі словника ЛР5 (таксономія). Рівень загальності: 1 — найзагальніші, 3 — конкретні, 4 — екземпляри (порогові значення, випадки). Порядок у межах рівня — алфавітний.

| № | Поняття | Рівень | Тип (ЛР5, рівень 1) | Кластер |
|---|---|---|---|---|
| 1 | gene | 1 | Biological entity | Геноміка й дані |
| 2 | genetic testing | 1 | Method and procedure | Клінічне тестування |
| 3 | genetic variant | 1 | Genetic variation | Геноміка й дані |
| 4 | hereditary cancer | 1 | Clinical concept | Клінічне тестування |
| 5 | risk assessment | 1 | Method and procedure | Клінічне тестування |
| 6 | variant filtering | 1 | Method and procedure | Контроль якості |
| 7 | BAM file | 2 | Data and artifact | Геноміка й дані |
| 8 | VCF file | 2 | Data and artifact | Геноміка й дані |
| 9 | breast cancer | 2 | Clinical concept | Клінічне тестування |
| 10 | cascade testing | 2 | Method and procedure | Клінічне тестування |
| 11 | family history | 2 | Data and artifact | Клінічне тестування |
| 12 | gene panel | 2 | Biological entity | Геноміка й дані |
| 13 | genetic counseling | 2 | Method and procedure | Клінічне тестування |
| 14 | germline variant | 2 | Genetic variation | Геноміка й дані |
| 15 | hard filtering | 2 | Method and procedure | Контроль якості |
| 16 | ovarian cancer | 2 | Clinical concept | Клінічне тестування |
| 17 | pathogenic variant | 2 | Genetic variation | Геноміка й дані |
| 18 | proband | 2 | Clinical concept | Клінічне тестування |
| 19 | relative | 2 | Clinical concept | Клінічне тестування |
| 20 | sequence alignment | 2 | Method and procedure | Геноміка й дані |
| 21 | variant calling | 2 | Method and procedure | Геноміка й дані |
| 22 | variant quality score recalibration | 2 | Method and procedure | Контроль якості |
| 23 | BRCA1 | 3 | Biological entity | Геноміка й дані |
| 24 | BRCA2 | 3 | Biological entity | Геноміка й дані |
| 25 | Fisher strand bias | 3 | Measure of quality | Контроль якості |
| 26 | exon | 3 | Biological entity | Контроль якості |
| 27 | insertion-deletion | 3 | Genetic variation | Геноміка й дані |
| 28 | mapping quality | 3 | Measure of quality | Контроль якості |
| 29 | quality by depth | 3 | Measure of quality | Контроль якості |
| 30 | rank sum test | 3 | Measure of quality | Контроль якості |
| 31 | read depth | 3 | Measure of quality | Контроль якості |
| 32 | single nucleotide polymorphism | 3 | Genetic variation | Геноміка й дані |
| 33 | strand odds ratio | 3 | Measure of quality | Контроль якості |
| 34 | QD < 2 | 4 | Measure of quality | Контроль якості |
| 35 | FS > 60 (SNP) | 4 | Measure of quality | Контроль якості |
| 36 | SOR > 3 | 4 | Measure of quality | Контроль якості |
| 37 | MQ < 40 | 4 | Measure of quality | Контроль якості |
| 38 | рідний брат/сестра: 50% | 4 | Clinical concept | Клінічне тестування |
| 39 | двоюрідний родич: до 12,5% | 4 | Clinical concept | Клінічне тестування |

Відкладено (не потрапило до карти, але лишається у ЛР5): `genome`, `exome`, `RNA sequencing`, `ontology` тощо — поза фокусним питанням.

## 3. Каталог відношень (12 типів)

| № | Відношення | У карті | Визначення | Domain → range (типи ЛР5) | Приклад |
|---|---|---|---|---|---|
| 1 | `is_a` | є різновидом | Вужче поняття є різновидом (підкласом) ширшого; для екземплярів — є прикладом класу. | той самий тип | hard filtering is_a variant filtering |
| 2 | `part_of` | є складовою | Об'єкт є частиною цілого (структурно чи функціонально). | будь-який → будь-який | gene part_of gene panel |
| 3 | `has_annotation` | має показник | Варіант, дані чи сутність характеризуються вимірюваним показником якості. | Genetic variation, Data and artifact, Biological entity → Measure of quality | genetic variant has_annotation quality by depth |
| 4 | `increases_risk_of` | підвищує ризик | Генетична сутність або властивість підвищує ймовірність захворювання. | Genetic variation, Biological entity, Biological property → Clinical concept | pathogenic variant increases_risk_of hereditary cancer |
| 5 | `is_kin_of` | є родичем | Особа перебуває у спорідненості з іншою особою (родич — пробанд). | Clinical concept → Clinical concept | relative is_kin_of proband |
| 6 | `uses_input` | використовує | Процедура чи показник використовує як вхід дані, показник або сутність. | Method and procedure, Measure of quality → Data and artifact, Measure of quality, Genetic variation, Biological entity, Knowledge and information technology | hard filtering uses_input Fisher strand bias |
| 7 | `produces` | створює | Процедура створює дані, варіанти чи показники як результат. | Method and procedure → Data and artifact, Genetic variation, Measure of quality | variant calling produces VCF file |
| 8 | `applies_to` | застосовується до | Процедура чи показник застосовується до об'єкта (дані, варіант, особа). | Method and procedure, Measure of quality → Genetic variation, Data and artifact, Biological entity, Clinical concept, Measure of quality | cascade testing applies_to relative |
| 9 | `requires` | потребує | Для виконання процедури необхідна передумова: дані, варіант, інша процедура. | Method and procedure → Data and artifact, Method and procedure, Genetic variation, Clinical concept, Biological entity, Knowledge and information technology | cascade testing requires pathogenic variant |
| 10 | `recommended_for` | рекомендований для | Джерело рекомендує процедуру або показник для певного випадку чи об'єкта. | Method and procedure, Measure of quality → Biological entity, Data and artifact, Clinical concept, Genetic variation | hard filtering recommended_for gene panel |
| 11 | `detects` | виявляє | Метод або процедура виявляє варіант, сутність чи стан. | Method and procedure → Genetic variation, Biological entity, Clinical concept | genetic testing detects pathogenic variant |
| 12 | `has_example` | має приклад | Поняття має конкретний приклад (екземпляр, порогове значення, випадок). | будь-який → будь-який | quality by depth has_example «QD < 2» |

Відношення «related-to» навмисно відсутнє: кожен зв'язок має бути одним із 12 типів із визначенням. Типи domain/range використовуються для автоматичної перевірки триплетів (результат 3).

## 4. Компетентнісні запитання ЛР4, які покриває карта

Запитання взято з `docs/cq_lab4.md` (18 CQ). Карта v1 повністю покриває 5, частково — 3.

| CQ | Запитання | Покриття | Пропозиції в карті |
|---|---|---|---|
| CQ01 | За якого QD SNP-варіант отримує прапорець LowQD? | повністю | P44 |
| CQ02 | За якого FS SNP відкидають? | повністю | P45 |
| CQ04 | Які значення SOR, MQ, MQRankSum призводять до прапорців? | частково (SOR, MQ; без MQRankSum) | P46, P47 |
| CQ07 | Чому варіант на кінці екзона з лише LowFS не слід просто відкидати? | частково (зв'язок SOR—екзон) | P26 |
| CQ08 | Який метод фільтрації обрати для малої панелі? | повністю | P27, P16 |
| CQ11 | Який шанс успадкування для рідного брата/сестри? | повністю | P48 |
| CQ13 | Який шанс для двоюрідних і далі? | повністю | P49 |
| CQ14 | З кого починати тестування і чому? | частково (каскад застосовується до родичів) | P37 |
| CQ17 | Чи буде користь від універсальної панелі без «родинного» варіанта? | ні (поза картою) | — |
| CQ15 | Чи можна тестувати 17-річного родича? | ні (вік поза картою) | — |

CQ17 і CQ15 лишаються поза картою свідомо (вік, склад панелі — деталі правил, а не понять); їх закриватимуть правила ЛР4.
