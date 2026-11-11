# Domain Knowledge Hub — рекомендаційна система та фінальний демонстратор (ЛР16)

Предметна область: біомедичні дані / аналіз варіантів (документація sarek, GATK Funcotator, bcftools, rare-disease pipeline + внутрішні нотатки Hub). Гілка репозиторію: `lab16`.

## Що всередині
| шлях | призначення |
|---|---|
| `reco/` | дані й фільтри (`data.py`), сутності (`entities.py`), граф у FalkorDB (`graphdb.py`), моделі (`models.py`: популярність, граф, kNN, гібрид), синтетичний журнал (`synth.py`), оцінка (`eval.py`, `ablation.py`, `report.py`), пояснення (`explain.py`), cold start (`cold.py`), LLM-шар (`llm.py`) |
| `app/` | FastAPI-демонстратор (`app/main.py`), ядро (`app/core.py`), CLI (`app/cli.py`), UI (`app/static/index.html`) |
| `docs/` | `reco_design.md`, `reco_eval.md`, `cold_start.md`, `demo_script.md`, `whitepaper.pdf`, `filters_demo.txt`, `img/` |
| `eval/` | сирі та зведені результати (`res_*.json`, `summary.json`, `table.md`, `ablation.json`, `cold*.json`, `explanations.json`) |
| `llm_log/`, `claims/` | протокол LLM-експерта і таблиця тверджень |
| `hub/`, `data/` | корпус Hub (680 розділів), граф знань, embeddings (`emb_bge.npy`), синтетичні взаємодії (`interactions.csv`, `profiles.json`) |

## Вимоги (перевірені версії)
Python 3.13 (розроблено на 3.13; див. `requirements.txt`: numpy 2.5.3, rank-bm25 0.2.2, falkordblite 0.11.0, fastapi 0.162.0, uvicorn 0.54.0, pydantic 2.13.5, httpx 0.28.1, pytest 9.1.1, matplotlib 3.11.2). Docker ≥ 29 + Compose ≥ 5 — лише для запуску в контейнері. Мережа потрібна тільки для `pip install`/`docker build`.

## Запуск однією командою
**Docker:** `docker compose up --build` → API на `http://localhost:8000` (UI `/`, OpenAPI `/docs`, `GET /health`). Демо-сценарій у терміналі: `docker compose --profile demo run --rm demo`.
**Без Docker:** лише Linux x86_64 або WSL2 (`falkordblite` не підтримує native Windows): `bash scripts/run_demo.sh` (створює `.venv`, ставить залежності, запускає 18 тестів і 5-кроковий демо-сценарій); `bash scripts/run_demo.sh serve` — API. У Windows використовуйте Docker Desktop з командами Docker вище або запускайте без Docker із WSL2.

## Змінні середовища
`PYTHONHASHSEED=0` (детермінізм; задано в compose та `run_demo.sh`). `ANTHROPIC_API_KEY` — **необов'язкова**: потрібна лише для живих перефразів (`reco/llm.py::AnthropicLLM`); за замовчуванням використовується кеш відповідей `llm_cache/`. Ключі в коді та звіті відсутні; у LLM не передаються персональні й конфіденційні дані (журнал взаємодій синтетичний).

## Тестові дані
`data/interactions.csv` (3 683 події, 64 користувачі, seed 0) генерує `reco/synth.py` (`python -c "from reco.eval import World; ..."` — див. `docs/reco_eval.md`); **дані синтетичні**. Корпус `hub/corpus.jsonl` — 674 чисті розділи з ЛР14 + 6 фікстур (`hub/fixtures.json`, дві отруєні для перевірки захисту). Embeddings `hub/emb_bge.npy` будуються `python scripts/build_embeddings.py` (потрібна модель bge з ЛР11; готовий файл у репозиторії).

## Тести та відтворення результатів
`python -m pytest -q tests` (18 тестів: поділ без витоку, популярність лише з train, фільтри, гібрид, метрики на ручному прикладі, пояснення й негативні контролі, cold start, API).
Повне відтворення оцінки (≈ 10 хв на 2 ядрах): `for s in 0 1 2 3 4; do python -m reco.eval --seeds $s --out eval/res_$s.json; done; python -m reco.ablation; python -m reco.cold; python -m reco.report`. Пояснення: `python scripts/make_explanations.py final`. Твердження: `python scripts/verify_claims.py`. Фільтри: `python scripts/filters_demo.py`.

## Статус перевірки запуску (чесно)
* Із чистої розпаковки архіву: `bash scripts/run_demo.sh` — виконано, лог `logs/fresh_unzip.log`.
* Docker: реєстри образів із середовища розробки недоступні, тому `python:3.13-slim` зібрано локально з файлової системи середовища (`docker import`), а замість `RUN pip install` використано `Dockerfile.offline` + `docker-compose.offline.yml`; `docker compose up` і сервіс `demo` відпрацювали (`logs/docker_verification.log`). **Звичайні `Dockerfile`/`docker-compose.yml` (з `pip install`) у середовищі розробки не збиралися** — лише `docker compose config` пройшов успішно.
