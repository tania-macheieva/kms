# ЛР11 — Чат-бот на основі гібридного сховища (RAG + граф), Domain Knowledge Hub, медицина

RAG-конвеєр над корпусом ЛР10 (688 фрагментів, BM25 + bge + RRF, reranker MaxSim) і графом ЛР9 (FalkorDB, 370 вузлів), з цитуванням `[id]`, політикою «не знаю», FastAPI-сервісом і оцінюванням.

## Артефакти за результатами
| Результат | Файли |
|---|---|
| R1 RAG-конвеєр | `src/rag.py`, `prompts/rag_v1.md`, `docs/rag.md`, `logs/rag_log.jsonl` (створюється під час запуску; не входить до початкового набору файлів), `docs/evidence/demo_rag.txt` |
| R2 Граф у контексті | `src/graph_context.py`, `docs/graph_vs_text.md`, `eval/graph_questions.jsonl`, `eval/results_R2.json` |
| R3 API | `api/main.py`, `docs/api.md`, `docs/openapi.json`, `tests/test_api.py` |
| R4 Оцінювання | `eval/rag_eval.jsonl`, `docs/rag_eval.md`, `eval/results_A.json`, `eval/metrics_A.json`, `eval/manual_checks.json` |
| R5 Оптимізація | `docs/rag_optimization.md`, `eval/results_B.json`, `eval/metrics_B.json` |
| Протокол LLM | `llm_log/`, `claims/claims.csv` |

## Що відрізняється від завдання (чесно)
- **Немає ключа LLM API.** Відповіді генерував `claude-haiku-4-5-20251001` через «сліпі» субагентні пакети, суддя — `claude-sonnet-5-5` (інша модель); відповіді лежать у хеш-кеші `data/llm_cache/` і відтворюються без мережі. `AnthropicLLM` (ключ лише з `ANTHROPIC_API_KEY`) написано, але **не запускалось**.
- **Затримка LLM і вартість — модельні** (припущення в `docs/rag_optimization.md`); виміряні лише час пошуку й побудови піддерева. Ціну токенів не вдалося звірити з прайсом (claims C18).
- **«Людські» перевірки (13 відповідей, κ=0.66) виконав LLM-рецензент**, не студент (V3 pending). κ нестабільний (мало негативних міток).
- Оракул ін'єкцій і guard виходу уточнено **після** першого прогону (`eval/results_A_run1.json` збережено); тестовий набір створено тією ж сесією, що й систему.
- Температура/seed LLM не керуються; пошук і метрики детерміновані (`PYTHONHASHSEED=0`).

## Запуск з нуля
Платформа: Linux x86_64 або WSL2; `falkordblite` не підтримує native Windows. Виконуйте команди в Bash усередині Linux/WSL (Windows PowerShell не запускає ці `.sh`-скрипти).
```bash
python3 -m venv .venv && . .venv/bin/activate     # Python 3.13
pip install -r requirements.txt
bash scripts/fetch_models.sh                       # ваги ONNX з npm (~150 МБ), потрібні node/npm
bash scripts/run_all.sh                            # граф, набір тестів, 31 автотест, прогони A/B, R2, метрики, docs/*.md (~3 хв з кешем)
DKH_API_KEYS="demo-reader-key:reader,demo-clinician-key:clinician" uvicorn api.main:app --port 8000    # API, див. docs/api.md
```
Нові генерації (якщо змінюється промпт/контекст): `python3 scripts/gen_prompts.py <A|B|R2>` → пакети в `llm_log/in/` → згенерувати/оцінити моделлю → `scripts/ingest_gen.py`, `scripts/make_judge_input.py`. Без кешу `ReplayLLM` кидає `CacheMiss`.

Гілка git: `lab11` (git-репозиторій у сесії не ініціалізовано — створіть гілку при коміті). Ключі API у коді/звіті відсутні (демо-ключі `demo-*-key` — фіктивні); персональні дані зовнішнім сервісам не передавалися (дані синтетичні).
