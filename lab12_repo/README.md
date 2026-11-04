# ЛР12 — OLAP-куб на основі таксономії (Domain Knowledge Hub, медицина)

Зіркова схема для процесу «виклик варіантів у геномній лабораторії» з таксономією ЛР5 як виміром (IRI), ELT у DuckDB/Parquet, 15 OLAP-запитів, семантичний шар метрик, text-to-SQL із захистами і панель.

## Артефакти за результатами
| Результат | Файли |
|---|---|
| R1 Зерно, питання, схема | `docs/star_design.md`, `docs/star_schema.png`, `sql/ddl.sql` |
| R2 ELT | `etl/generate.py`, `etl/load.py`, `data/raw/*.csv`, `data/parquet/*.parquet`, `data/VERSION.json`, `docs/dq_report.json` |
| R3 OLAP | `sql/olap/*.sql` (15), `docs/olap_results.md`, `eval/olap_verify.json` |
| R4 Семантичний шар | `semantic/metrics.yml`, `semantic/sl.py`, `docs/semantic_layer.md` |
| R5 Text-to-SQL і панель | `t2sql/pipeline.py`, `tests/t2sql.jsonl`, `docs/t2sql.md`, `dashboard/index.html` |
| Протокол LLM | `llm_log/`, `claims/claims.csv` |

## Що відрізняється від завдання (чесно)
- **Дані синтетичні** (документований генератор `etl/generate.py`, seed 42; 20 000 викликів); висновки в OLAP-інтерпретаціях і на панелі описують закладені в генератор ефекти, а не біологію.
- **Немає ключа LLM API:** SQL генерував `claude-haiku-4-5-20251001` через «сліпі» субагентні запуски; відповіді відтворюються з `data/llm_cache/`. Вартість text-to-SQL — модельна (ціну токенів не звірено).
- Тести text-to-SQL складала та сама сесія, що й схему → набір легкий; «м'яку» метрику визначено після перегляду результатів (подано окремо від строгої).
- «Людський» перегляд виконав LLM-рецензент; рівень V3 лишається pending.
- Температура/seed LLM не керуються; усе інше детерміноване (`PYTHONHASHSEED=0`).

## Запуск з нуля
Повний `scripts/run_all.sh` потребує Bash (Linux/macOS, WSL2 або Git Bash). У Windows PowerShell можна створити середовище й запустити окремі Python-команди нижче, але повний скрипт запускайте через WSL2 або Git Bash.
Windows PowerShell: `python -m venv .venv`, `.\.venv\Scripts\Activate.ps1`, `python -m pip install -r requirements.txt`; для повного запуску в Git Bash активуйте це середовище командою `source .venv/Scripts/activate`, тоді виконайте `bash scripts/run_all.sh`.
```bash
python3 -m venv .venv && . .venv/bin/activate     # Python 3.13
pip install -r requirements.txt                    # duckdb 2.0.0, pandas 3.0.5, sqlglot 30.27.0, plotly 7.1.0 ...
bash scripts/run_all.sh                            # ~1 хв: дані, ELT, OLAP, перевірки, 45 тестів, документи, панель
python3 etl/load.py && python3 scripts/run_olap.py -v   # окремі кроки
```
Панель: відкрийте `dashboard/index.html` (самодостатній файл, без мережі). Нові SQL-генерації: `python3 scripts/gen_t2sql.py prep` → запуск моделі за `llm_log/prompts/gen_protocol_t2sql_v1.txt` → `python3 scripts/gen_t2sql.py ingest`.

Гілка git: `lab12` (git-репозиторій у сесії не ініціалізовано — створіть гілку при коміті). Ключі API у коді відсутні; персональних даних немає (зразки — анонімні коди).
