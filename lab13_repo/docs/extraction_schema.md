# Схема видобування знань (ЛР13, результат R1)

Домен: документація інструментів аналізу геномних варіантів (Sarek, RareLink/rare, bcftools, GATK/Funcotator) — корпус із ЛР10
(24 зовнішні документи; власні звіти `int_*` виключено, щоб не оцінювати текст, який породжено тим самим процесом).
Схема узгоджена з онтологією ЛР7 (властивості `usesInput`, `produces`, `hasThreshold` …): див. таблицю в `docs/normalization.md`.

## 1. Типи сутностей (6) і відношень (7)

| Сутність | Визначення | Приклад (✔) | Контрприклад (✘) |
|---|---|---|---|
| **Tool** | програма, workflow/конвеєр, плагін, команда чи підкоманда | `bcftools annotate`, `HaplotypeCaller`, `nf-core/sarek`, плагін `Condel` | «Nextflow-based» як прикметник без назви; люди й організації («Broad Institute») |
| **Procedure** | крок аналізу, названий у тексті | `variant calling`, `annotation`, `filtering` | загальні слова «analysis», «run», «process» |
| **FileFormat** | формат даних/файлу | `VCF`, `BAM`, `CRAM`, `BED` | назва файлу-прикладу `sample1.vcf.gz` (це файл, не формат) |
| **Metric** | показник/анотація якості, бал | `QD`, `FS`, `mapping quality`, `Consensus Deleteriousness score` | перелік полів у змісті, де не сказано, що їх обчислює інструмент |
| **Option** | параметр/прапорець командного рядка або workflow | `--merge-logic`, `--vep_condel` | значення параметра (`GRCh38` у `--genome GRCh38`) |
| **Resource** | іменована база/збірка/референс | `dbSNP`, `GRCh38`, `Gencode` | загальне «any species with a reference genome» |

| Відношення | Тип (суб'єкт → об'єкт) | Приклад ✔ | Контрприклад ✘ |
|---|---|---|---|
| ACCEPTS | Tool → FileFormat | «bcftools merge takes VCF files» | «VCF is described in the spec» (інструмент не згадано) |
| PRODUCES | Tool → FileFormat | «outputs a BCF file» | «the file can be indexed» |
| PERFORMS | Tool → Procedure | «sarek is a workflow designed to detect variants» | «can be customised for variant calling» (тема, не твердження) |
| HAS_OPTION | Tool → Option | «`--condel_config` specifies the path to the config» | прапорець як приклад значення іншого параметра |
| COMPUTES_METRIC | Tool → Metric | «The plugin calculates the Consensus Deleteriousness score» | метрика тільки в заголовку таблиці |
| USES_RESOURCE | Tool → Resource | «uses dbSNP to annotate» | «dbSNP is a database» |
| INVOKES | Tool → Tool | «runs `bcftools view` to filter» | «built using Nextflow», «runs in Docker» (залежність/контейнер) |

## 2. Інструкція анотатору (v2, `llm_log/prompts/annotate_v2.txt`)

1. Лише те, що явно сказано в уривку; без зовнішніх знань. Згадка в заголовку/змісті/переліку назв — не твердження (сутність можна позначити).
2. `evidence` — дослівний відрізок з уривка (розмітка збережена), до 2 суміжних речень, **містить предикат**.
3. Суб'єкт/об'єкт — поверхнева форма **без markdown-розмітки**; займенник чи «the plugin» розв'язується до названої сутності того ж уривка.
4. Одне твердження на трійку (суб'єкт, відношення, об'єкт) в уривку; аліаси (`nf-core/sarek`, `Sarek`) — одна сутність (перша форма).
5. Обмеження типів обов'язкові; «містить/збудований на/працює в контейнері» ≠ INVOKES.
6. PERFORMS/COMPUTES_METRIC тощо потребують явного твердження «цей інструмент це робить».
7. Не анотувати людей, установи, фінансування, ліцензії, цитування.

Граничні випадки: заперечення («does not support») не анотуються; параметри підкоманди належать підкоманді; параметр, згаданий як значення іншого параметра, не є HAS_OPTION; WDL-входи належать «Funcotator WDL», а не «Funcotator» (рішення адʼюдикації D053–D060); короткі прапорці `-R` = аліас довгої форми `--regions` (одне твердження).

## 3. Вихідна JSON-схема та нормалізація

Схема: `schema/extraction_output.schema.json` (закритий словник типів та відношень, `additionalProperties:false`). Метод B валідує нею кожну відповідь.
Кожен запис видобування додатково несе **провенанс**: `document`, `passage_id`, `start`/`end` (зсув доказу в уривку), `doc_start` (у чистому документі), `model`, `prompt_version`, `method`.

Нормалізація (функція `norm` у `src/common.py`, використовується в оцінці): N1 прибрати markdown (`` ` * _ [ ] ``); N2 нижній регістр; N3 префікс `nf-core/` відкинути; N4 обрізати кінцеву пунктуацію/пробіли; для опцій `--` зберігаються. Зведення до канонічних сутностей графа (аліаси, посилання на класи онтології ЛР7) — у `docs/normalization.md` (R5).

## 4. Пілотна анотація (5 уривків) і уточнення

Пілот: `llm_log/prompts/annotate_v1.txt` → `llm_log/raw/pilot_out.json` (P001, P008, P023, P046, P065; різні документи й типи тексту). Анотатор повернув 5 відношень і 13 спірних місць. Внесені **уточнення v1 → v2**:

| № | Знахідка в пілоті | Уточнення |
|---|---|---|
| U1 | P008: підмет «The plugin calculates…» → у evidence немає імені `Condel`, правило «суб'єкт у evidence» суперечить правилу 3 | суб'єкт розв'язується до названої сутності; evidence мусить містити лише предикат (правило 2–3) |
| U2 | P008: у evidence є зворотні лапки, у сутностях — ні | сутності без розмітки, evidence дослівно з розміткою (правило 3, N1) |
| U3 | P001/P046: «built using Nextflow», «contains vcf* commands» — немає відношення | явно виключені залежність/контейнер/вмістимість з INVOKES (правило 5) |
| U4 | P023: «can be customised for variant calling» — слабка PERFORMS | потрібне явне твердження (правило 6) |
| U5 | P001/P023: `nf-core/sarek` та `Sarek` — дублі; workflow — Tool? | аліаси = одна сутність (правило 4); workflow/плагін = Tool (визначення Tool) |
| U6 | P065: перелік полів у змісті, Gencode лише в заголовку | згадка в змісті/заголовку не є твердженням (правило 1) |

Вплив: після v2 міжанотаторне узгодження склало κ = 0,71 (див. `docs/gold_card.md`).
