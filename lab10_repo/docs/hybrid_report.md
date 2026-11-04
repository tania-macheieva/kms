# Гібридний пошук і reranking (Результат 4)

Код: `src/hybrid.py` (клас `Retriever`), експеримент `scripts/exp_hybrid.py`, сирі дані `docs/evidence/hybrid.json`.

## 1. Компоненти

- **BM25** (`rank_bm25.BM25Okapi`) над токенами `\w+` у нижньому регістрі без англійських стоп-слів.
- **Dense**: bge-small-en-v1.5 + FAISS HNSW (M=32, efSearch=64).
- **RRF (k=60)**: `score(d) = Σ 1/(60 + rank_i(d))` по двох списках top-50 (BM25 та dense); результат — top-N за сумою.
- **Reranker (top-30 → top-5).** **Відхилення від завдання:** cross-encoder з вагами в доступних реєстрах знайти не вдалося (HuggingFace заблоковано). Замість нього реалізовано **late-interaction reranker (MaxSim, як у ColBERT)** на токенних векторах тієї ж моделі bge: оцінка = середнє за токенами запиту від максимальної косинусної схожості з токенами фрагмента. Це **не cross-encoder**: модель не навчалася для такого скорингу, тож очікувати якості справжнього reranker не слід. `Retriever.r_rerank` можна замінити на cross-encoder (sentence-transformers `CrossEncoder`) без зміни решти коду — цю заміну не перевірено.
- **Pre-filter за метаданими** (`make_pred`: type, sensitivity, date, lang) застосовується **до** ранжування: BM25 — маскою оцінок, HNSW — `IDSelectorBatch` над дозволеними рядками.

## 2. Rerank змінює top-5

З 55 запитів із відповіддю top-5 після reranking відрізняється від top-5 гібриду у 55 (склад змінився у 47); перша релевантна позиція покращилася у 8 запитів і погіршилася у 9. Медіанна затримка: гібрид 15 мс, з reranking 670 мс.

Приклад зміни порядку за незмінного складу (запит Q04: «Where do I put the target regions and GC files when building ASCAT resources for exome data?»):

| # | До (RRF) | Після (MaxSim) |
|---|---|---|
| 1 | sarek_usage#h040 · Core Nextflow arguments > How to run ASCAT with whole-exome  | sarek_usage#h040 · Core Nextflow arguments > How to run ASCAT with whole-exome  |
| 2 | sarek_usage#h042 · Core Nextflow arguments > How to run ASCAT with whole-exome  | sarek_usage#h042 · Core Nextflow arguments > How to run ASCAT with whole-exome  |
| 3 | sarek_usage#h038 · Core Nextflow arguments > How to run ASCAT with whole-exome  | sarek_usage#h041 · Core Nextflow arguments > How to run ASCAT with whole-exome  |
| 4 | sarek_usage#h041 · Core Nextflow arguments > How to run ASCAT with whole-exome  | sarek_usage#h043 · Core Nextflow arguments > How to run ASCAT with whole-exome  |
| 5 | sarek_usage#h043 · Core Nextflow arguments > How to run ASCAT with whole-exome  | sarek_usage#h038 · Core Nextflow arguments > How to run ASCAT with whole-exome  |

Приклад, де reranking змінив позицію першої релевантної відповіді: Q02 («Which tool predicts what effect a variant has, and what does it record in the VCF header?») — 3 → 2.

## 3. Pre-filter за метаданими (перевірка)

| Фільтр | Запит | Без фільтра | З фільтром | Результат |
|---|---|---|---|---|
| sensitivity = public | Яке сховище використовується для SPARQL-запитів? | public: 0, internal: 0, restricted: 10 | public: 10, internal: 0, restricted: 0 | пройдено |
| type = manual | how to filter variants by expression | tutorial: 1, output-reference: 1, manual: 8 | manual: 10 | пройдено |
| date ≥ 2026-10-25 | how do I run the pipeline | найстарший: 2026-10-07 | найстарший: 2026-10-26 | пройдено |
| type∈{manual,readme} ∧ public ∧ date≥2026-01-01 + rerank | how to call variants with bcftools mpileup | — | 5 результатів, усі відповідають фільтру | пройдено |

Українське запитання про SPARQL без фільтра повертає 10 з 10 фрагментів із **restricted**-документів (родовід); з фільтром `public` — жодного обмеженого, і все одно 10 результатів. Окрема перевірка pre- проти post-фільтрації: фільтр, якому відповідають 77 фрагментів, при pre-фільтрації віддає 10 результатів, а фільтрація top-10 після пошуку — лише 2. Це перевірка механізму; доступ реальних користувачів потрібно додатково забезпечувати на рівні сховища (ролі).

## 4. Приклади: гібрид виграє (3) та програє (1)

Узагальнення за 55 запитами (позиція першої релевантної відповіді в top-10): гібрид краще за dense у 14 запитах і гірше у 8; краще за BM25 у 19 і гірше у 6. Краще **за обидва** окремі пошуки — лише у 3 запитах; гірше за кращий з двох — у 14; однаково — у 38. Тобто RRF не завжди перевершує найкращий окремий пошук: його сила — у стабільності, а не в максимумі. Виграш у наведених запитах невеликий (1 позиція).

### Виграш: Q48 — «Which FORMAT fields can bcftools call emit per sample, and how is a bcftools plugin invoked compared with a normal command?»

Перша релевантна позиція: BM25 = 4, dense = 4, **гібрид = 3**, гібрид+rerank = 5.

- BM25 top-3: bcftools_manual#h023; bcftools_manual#h101; bcftools_manual#h009
- dense top-3: bcftools_manual#h000; sarek_output#h025; bcftools_manual#h023
- RRF top-3: bcftools_manual#h023; bcftools_manual#h026; bcftools_manual#h095 ✔

Пояснення: Багатокроковий запит про поля FORMAT і виклик плагінів: релевантні фрагменти розкидані по довгому мануалу; BM25 і dense окремо ставлять перший доказ на 4-те місце, а їх поєднання — на 3-тє (обидва списки містять потрібний, але з різними відволікаючими фрагментами).

### Виграш: Q35 — «Why do I need to change filtering settings when using a tiny tutorial dataset?»

Перша релевантна позиція: BM25 = 2, dense = 3, **гібрид = 1**, гібрид+rerank = 1.

- BM25 top-3: sarek_vc_sarek#h003; sarek_vc_sarek#h007 ✔; rare_usage#h003
- dense top-3: sarek_vc_theory#h008; bcftools_manual#h056; sarek_vc_sarek#h007 ✔
- RRF top-3: sarek_vc_sarek#h007 ✔; sarek_vc_sarek#h003; sarek_usage#h050

Пояснення: Парафраз без спільних рідкісних слів: BM25 знаходить фрагмент за загальними словами (filtering, dataset) на 2-й позиції, dense за змістом — на 3-й; обидва тримають його високо, тому RRF піднімає на 1-ше місце.

### Виграш: Q18 — «bcftools annotate merge-logic»

Перша релевантна позиція: BM25 = 3, dense = 2, **гібрид = 1**, гібрид+rerank = 1.

- BM25 top-3: bcftools_manual#h017; bcftools_manual#h069; bcftools_manual#h019 ✔
- dense top-3: bcftools_manual#h022; bcftools_manual#h019 ✔; bcftools_manual#h018
- RRF top-3: bcftools_manual#h019 ✔; bcftools_manual#h017; bcftools_manual#h016

Пояснення: Ключові слова `merge-logic` зустрічаються в кількох фрагментах розділу `bcftools annotate`, тому BM25 ставить потрібний на 3-є місце, а dense — на 2-ге (його сусіди — інші опції annotate). Потрібний фрагмент є в обох списках, а різні сусіди рознесені: сума внесків 1/(60+r) виводить його на 1-ше.

### Програш: Q12 — «What are the stages of launching the rare disease workflow and what goes in the sample table?»

Позиція першої релевантної відповіді: BM25 = немає в top-10, dense = 2, **гібрид = 10**, гібрид+rerank = 2.

Пояснення: запит довгий і складається із загальних слів (stages, launching, workflow, sample, table), які поширені в десятках фрагментів документації nf-core; BM25 розподіляє вагу між ними й не має релевантного фрагмента в top-10, а RRF додає його шум до гарного dense-списку (релевантний фрагмент був 2-м). RRF сліпо довіряє обом спискам однаково, тому слабкий список знижує результат. Те саме відбувається з українськими запитами до англійських документів (напр. Q29: dense = 1, гібрид = 6): лексичного перекриття немає, BM25 повертає випадкові фрагменти українських документів. Практичні виходи: вага списків у RRF, запуск BM25 лише для запитів тієї ж мови, що й корпус.

