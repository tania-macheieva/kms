# Таблиця тверджень (`claims.csv`)

Колонки: `id, claim, type (fact/rule/hypothesis), source, V1, V2, V3, V4, status (verified/rejected/pending), comment`.
* **V1** — відтворювана перевірка (`python scripts/verify_claims.py` звіряє число з `eval/*.json` або з текстовим витягом звіту в `claims/sources/`); **V2** — тести/узгодження кількох джерел; **V3** — рецензент-людина (усюди `pending`: її має виконати студент); **V4** — метрики експерименту.
* Підсумок: 33 твердження, 26 verified (79 %), 3 rejected (c05, c07, c29), 4 pending (c09, c31, c32, c33). Відхилені — з поясненнями в `comment`.
* Частка пояснень, що збігаються зі шляхом у графі: 100/100 (c08, c10); детальніше `docs/cold_start.md`.
