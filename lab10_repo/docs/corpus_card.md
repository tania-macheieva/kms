# Картка корпусу (Domain Knowledge Hub, ЛР10)

Корпус: **33 документів → 688 фрагментів** (стратегія за заголовками, ≤250 слів; медіана 141 слів, мін 33, макс 287). Файл: `data/corpus.jsonl` (метадані: chunk_id, doc_id, title, section, type, date, sensitivity, source_url, lang, start, end, n_words, text).

## 1. Джерела та ліцензії

| Джерело | Версія (commit) | Ліцензія | Документів | Фрагментів | Мова |
|---|---|---|---|---|---|
| nf-core/sarek | 6e9b164daa | MIT | 8 | 215 | en |
| nf-core/raredisease | b504e038ba | MIT | 4 | 96 | en |
| samtools/bcftools | b62c1bda5b | MIT/Expat (dual with GPL) | 2 | 148 | en |
| broadinstitute/gatk | 0cde69eed3 | Apache-2.0 | 10 | 157 | en |
| own project (ЛР4–ЛР9) | локальні файли | власна робота автора (включено до репозиторію; дані синтетичні) | 9 | 72 | uk |

Документи — відкрита документація (README, посібники, довідники) інструментів аналізу геномних варіантів, тобто тієї ж предметної області, що й проєкт (біомедичні дані: VCF, анотація, фільтрація). Сирі копії файлів лежать у `data/raw/` (для зовнішніх джерел — з їхньою ліцензією MIT/Apache-2.0, яка дозволяє копіювання з збереженням повідомлення про авторські права), очищені — у `data/docs_clean/`.
Свідомо **не** включено: специфікації GA4GH hts-specs (у репозиторії немає файла ліцензії), Wikipedia, NCBI/PubMed та HuggingFace (недоступні з середовища виконання), CHANGELOG-файли (шум, низька інформативність).

## 2. Правила очищення (шум, навігація, колонтитули)

Реалізація — `scripts/build_corpus.py` (`md_clean`, `adoc_clean`); правила застосовуються в такому порядку:

| № | Правило | Навіщо |
|---|---|---|
| R1 | Видалення YAML front matter | службові метадані |
| R2 | Видалення HTML-коментарів | службові нотатки |
| R3 | Видалення блоків ```mermaid | діаграми без тексту |
| R4 | Видалення бейджів `[![…](…)](…)` | навігація/статус CI |
| R5 | Видалення зображень `![…](…)` | немає тексту |
| R6 | Видалення HTML-тегів (img, p, picture, details…) із збереженням тексту | розмітка |
| R7 | Посилання `[текст](url)` → `текст` | URL не несуть змісту для пошуку |
| R8 | Callout-блоки `> [!NOTE]` → `NOTE:` | зберегти попередження |
| R9 | Видалення розділювачів таблиць `|---|` | розмітка |
| R10 | Видалення розділів «Table of contents» | навігація |
| R11 | Видалення пунктів списку, що є лише якорями `[…](#…)` | навігація |
| R12 | AsciiDoc (bcftools): видалення `//` коментарів | службові |
| R13 | AsciiDoc: підкреслені заголовки та `=== X` → Markdown `#`; прибрати `+`/`--` | зберегти структуру |
| R14 | AsciiDoc: прибрати `*…*`, `'…'` маркери, `{date}`/`{version}`, екранування `\<` | розмітка |
| R15 | Нормалізація пробілів, ≤1 порожній рядок підряд | чистота |
| R16 | Видалення порожніх заголовків | порожні розділи |

Обсяг: сирі файли містили 827 524 символів, після очищення — 673 869. Колонтитулів у Markdown-документації немає; їхній аналог (CI-бейджі, меню, TOC) знято правилами R4, R10, R11.

## 3. Чутливість (sensitivity) і доступ

Кожен фрагмент має поле `sensitivity`: **public** — відкрита документація; **internal** — внутрішні звіти проєкту без персональних записів; **restricted** — внутрішні звіти, що містять записи родоводу (імена вигаданих/синтетичних осіб: Olena, Iryna, …) — вони позначені обмеженими, бо за призначенням проєкту такі дані мають потрапляти лише до уповноважених користувачів. Правило призначення: `restricted`, якщо в сирому документі є ім'я з родоводу ЛР7–ЛР9; інакше `internal`; усе з зовнішніх репозиторіїв — `public`.

| sensitivity | Документів | Фрагментів |
|---|---|---|
| public | 24 | 616 |
| internal | 3 | 18 |
| restricted | 6 | 54 |

Pre-filter за `sensitivity` перевірено в `docs/hybrid_report.md`; жодні дані не передавалися зовнішнім сервісам (усі моделі працюють локально).

## 4. Типи документів

| type | Документів | Фрагментів |
|---|---|---|
| internal-report | 9 | 72 |
| pipeline-readme | 6 | 46 |
| tutorial | 5 | 74 |
| readme | 4 | 57 |
| usage-guide | 2 | 133 |
| output-reference | 2 | 119 |
| citations | 2 | 16 |
| reference | 2 | 27 |
| manual | 1 | 144 |

## 5. Документи

| doc_id | Назва | type | date | sensitivity | Фрагментів |
|---|---|---|---|---|---|
| sarek_readme | sarek_readme | readme | 2026-10-26 | public | 9 |
| sarek_usage | Introduction | usage-guide | 2026-10-26 | public | 91 |
| sarek_output | sarek_output | output-reference | 2026-10-26 | public | 77 |
| sarek_vc_intro | Variant Calling Tutorial | tutorial | 2026-10-26 | public | 3 |
| sarek_vc_theory | Calling Variants on Sequencing Data | tutorial | 2026-10-26 | public | 10 |
| sarek_vc_sarek | Using Sarek for Variant Calling | tutorial | 2026-10-26 | public | 9 |
| sarek_vc_interp | Interpretation | tutorial | 2026-10-26 | public | 6 |
| sarek_citations | sarek_citations | citations | 2026-10-26 | public | 10 |
| rare_readme | rare_readme | readme | 2026-10-07 | public | 6 |
| rare_usage | nf-core/raredisease: Usage | usage-guide | 2026-10-07 | public | 42 |
| rare_output | rare_output | output-reference | 2026-10-07 | public | 42 |
| rare_citations | rare_citations | citations | 2026-10-07 | public | 6 |
| bcftools_readme | bcftools_readme | readme | 2026-10-27 | public | 4 |
| bcftools_manual | Convert 23andme results into VCF | manual | 2026-10-27 | public | 144 |
| gatk_readme | gatk_readme | readme | 2026-08-17 | public | 38 |
| gatk_mutect2_wdl | gatk_mutect2_wdl | pipeline-readme | 2026-08-17 | public | 16 |
| gatk_cnv_germline | gatk_cnv_germline | pipeline-readme | 2026-08-17 | public | 6 |
| gatk_cnv_somatic | gatk_cnv_somatic | pipeline-readme | 2026-08-17 | public | 3 |
| gatk_funcotator_wdl | gatk_funcotator_wdl | pipeline-readme | 2026-08-17 | public | 5 |
| gatk_pathseq_wdl | gatk_pathseq_wdl | pipeline-readme | 2026-08-17 | public | 4 |
| gatk_docker | REPLACE VALUE OF GITHUB_TAG WITH DESIRED VERSION | pipeline-readme | 2026-08-17 | public | 12 |
| gatk_funco_tutorial | Required and defaults to false. | tutorial | 2026-08-17 | public | 46 |
| gatk_funco_spec | gatk_funco_spec | reference | 2026-08-17 | public | 16 |
| gatk_funco_refdiff | gatk_funco_refdiff | reference | 2026-08-17 | public | 11 |
| int_cq_scope | int_cq_scope | internal-report | 2026-10-21 | internal | 7 |
| int_rules | Результат 5. Аналіз бази правил | internal-report | 2026-10-21 | internal | 6 |
| int_reasoner | Журнал reasoner (HermiT) | internal-report | 2026-10-26 | restricted | 6 |
| int_onto_eval | Порівняння з чернеткою LLM, OntoClean і CQ-тести (результат  | internal-report | 2026-10-26 | restricted | 12 |
| int_situations | Перевірка шаблонів ситуацій запитами | internal-report | 2026-10-25 | restricted | 6 |
| int_sparql | Результат 2. SPARQL-запити та їхні результати | internal-report | 2026-10-27 | restricted | 12 |
| int_shacl | Результат 3. SHACL-форми та валідація | internal-report | 2026-10-27 | restricted | 5 |
| int_cq_map | Результат 1. Графова схема під CQ | internal-report | 2026-10-28 | internal | 5 |
| int_cypher | Результат 3. Запити Cypher та їхні результати | internal-report | 2026-10-28 | restricted | 13 |

`date` — дата останнього коміту файла в репозиторії-джерелі (для власних документів — дата зміни файла).

## 6. Відомі прогалини та ризики

- **Мова.** 24 з 33 документів англійською, 9 — українською (власні звіти). Доступні в середовищі моделі embeddings — англомовні (multilingual-e5 недоступна, HuggingFace заблоковано), тому для українських запитів якість очікувано нижча; це виміряно окремо в `docs/embeddings_cmp.md`.
- **Дублювання.** Документація sarek і raredisease частково повторює одні й ті самі настанови (nf-core boilerplate) — схожі фрагменти ускладнюють розмітку релевантності.
- **Охоплення.** Немає клінічних настанов (ACMG, ClinVar), немає статей; корпус — технічна документація, а не біомедична література. Запити без відповіді (no_answer) використовують цю прогалину.
- **Таблиці й код.** Таблиці та командні рядки перетворено на текст; частина таблиць після очищення втрачає структуру стовпців.
- **Версії.** Знімки репозиторіїв зафіксовано commit-ами (див. source_url); пізніші зміни документації не відображені.
- **Власні документи** — українською, написані в межах ЛР, містять синтетичні дані; не є джерелом істини щодо медицини.
