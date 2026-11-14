# Самостійна робота 12 — Проєктування зіркової схеми

## Процес та зерно

Модель описує оцінювання RAG-відповідей: один рядок факту — одне тестове питання в одному прогоні. Зерно ключа `PRIMARY KEY (run_key, test_key)` відповідає всім п'яти аналітичним запитам; роль користувача зберігається як вимірний атрибут.

## Артефакти

- `sql/ddl.sql` — DuckDB DDL вимірів, факту, SCD2 view та обмежень.
- `sql/queries.sql` — п'ять запитів для бізнес-питань.
- `sql/queries_results.txt` — результати запитів на 88 рядках фактів (прогони A, B та SR11).
- `star.mmd`, `star_schema.png` — діаграма зіркової схеми.
- `src_data/` — вхідні результати оцінювання RAG.
- `llm_proposal.md`, `flaws_demo.py`, `flaws_demo_output.txt` — запропонована LLM схема й демонстрація трьох дефектів та їхніх наслідків.

У власній схемі похідні частки не зберігаються: точність, faithfulness і context recall розраховуються з адитивних чисельників та знаменників. SCD2 реалізовано append-only через `valid_from`; `valid_to` та `is_current` обчислюються у view.

## Відтворення

Залежність: `duckdb`. Із PowerShell у цій папці:

```powershell
python -X utf8 build_dw.py
python -X utf8 run_queries.py
python -X utf8 flaws_demo.py
```

`build_dw.py` створює `out/sr12.duckdb`; `run_queries.py` виконує п'ять SQL-запитів і оновлює текстові результати. `flaws_demo.py` тестує помилкову LLM-схему й SCD2 на тимчасовій копії бази.
