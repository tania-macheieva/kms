# Лабораторна робота 5. Таксономія понять предметної області
Область: Медицина / аналіз біомедичних даних. Результати: корпус термінів → три чернетки таксономії → метрики → підсумкова таксономія → SKOS і тести.

| Результат | Артефакти |
|---|---|
| 1. Корпус | `models/terms.csv` (121 термін), `scripts/normalize_terms.py`, `data/curation.py` |
| 2. Три чернетки | `models/tax_expert.csv`, `models/tax_llm.json`, `models/tax_cluster.csv`, `scripts/cluster_taxonomy.py` |
| 3. Метрики | `docs/taxonomy_eval.md`, `scripts/eval_taxonomies.py`, `annotations/` |
| 4. Підсумкова | `models/taxonomy_final.csv`, `docs/taxonomy_final.png/.svg`, `docs/taxonomy_change_process.md` |
| 5. SKOS і тести | `models/taxonomy.ttl`, `tests/test_taxonomy.py` (+ `test_corpus_versions.py`), `docs/evidence/pytest_all.txt` |
| LLM-експерт | `llm_log/`, `claims/claims.csv` |

## Запуск з нуля
```
python -m venv .venv && source .venv/bin/activate        # Python 3.13 (перевірено), >= 3.10
pip install -r requirements.txt
pip install https://github.com/explosion/spacy-models/releases/download/en_core_web_md-3.8.0/en_core_web_md-3.8.0-py3-none-any.whl
python scripts/normalize_terms.py        # models/terms.csv
python scripts/build_expert_tax.py       # models/tax_expert.csv
python scripts/cluster_taxonomy.py       # models/tax_cluster.csv (seed 42; потрібен spaCy md 3.8.0)
python scripts/eval_taxonomies.py        # метрики, κ, ARI
python scripts/build_final_tax.py && python scripts/export_skos.py && python scripts/draw_tree.py   # (draw_tree потребує Graphviz `dot`)
python -m pytest -v                      # 19 passed
```
`tax_llm.json` — дослівний вихід LLM (не перегенеровується). Seed: 42 (кластеризація; Ward детермінований), 7 (вибірка для κ).

## Правила нормалізації корпусу (результат 1, C4)
1. Обрізати пробіли, звести тире й нерозривні пробіли до звичайних.
2. Ключ порівняння: casefold, дефіс → пробіл, без кінцевої пунктуації; канонічна мова — англійська (кириличні форми зіставляються з `label_uk`).
3. Однина: -ies → -y, -es (після s/x/ch/sh) → -, -s → - (виключення: analysis, diagnosis, genomics, proteomics тощо).
4. Синоніми й абревіатури зливаються в канонічний термін і зберігаються в `alt_labels` (SNP → single nucleotide polymorphism, VQSR тощо).
5. Шум (`data`, `thing`, `etc`, `other`…) видаляється; нерозпізнані форми потрапляють у звіт, а не в корпус.
6. `freq` — кількість вживань канонічного терміна та його alt_labels у двох текстах (gatk, cdc) із ЛР4; `source = llm_domain` — термін запропоновано LLM і в текстах не знайдено.
Журнал: `docs/evidence/normalize_log.txt` (722 сирих кандидатів → 121 канонічний термін, 0 нерозпізнаних, 18 шумових форм видалено).
