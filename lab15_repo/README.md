# Domain Knowledge Hub — ЛР15: LLM-агент з інструментами над сховищем знань
Домен: Медицина / «Аналіз біомедичних даних». Агент відповідає на запитання про Hub (документація GATK/Sarek/bcftools, граф знань, склад DuckDB із семантичним шаром, реєстр суперечливих тверджень) **лише з отриманих доказів**, із цитатами, і каже «не знаю», коли доказів немає або роль не має доступу. Гілка `lab15`.

## Що тут
| Результат | Де |
|---|---|
| R1 специфікація агента (мета, ролі, 5 інструментів зі схемами, ліміти, заборони, HITL-правила, памʼять з TTL) | `docs/agent_spec.md` (генерується `scripts/make_spec.py` з коду) |
| R2 агент LangGraph (plan→act→draft→verify) і MCP-сервер, read-only + перевірка прав, перевірка цитат, трейс ≥5 запитів | `agent/`, `mcp_server/`, `logs/trace_v2.jsonl` (25 запитів), `logs/mcp_demo_*.json`, `tests/test_agent.py` |
| R3 25 сценаріїв (13 успіх / 6 «не знаю» / 6 конфлікт), метрики, 3 збої з виправленнями, повторний прогін | `tests/agent_scenarios.jsonl`, `docs/agent_eval.md`, `eval/v{0,1,2}.json`, `eval/metrics.json` |
| R4 22 атаки (7 типів), до/після захистів, ablation, залишкові ризики | `tests/attacks.jsonl`, `tests/attacks_obey.json`, `docs/agent_security.md`, `eval/e2_*.json`, `eval/attacks_*.json` |
| R5 `propose_fact` (SHACL + джерело, ризики low/medium/high, черга схвалення, аудит-журнал, метрики) | `agent/propose_fact.py`, `docs/hitl.md`, `proposals/`, `eval/hitl_demo.json`, `tests/test_hitl.py` |
| Протокол LLM | `llm_log/` (промпти, in/raw, `log.csv`), `claims/claims.csv` |

`hub/` — знімок даних Hub із ЛР9/11/12/14 (граф у CSV, реєстр альтернатив, SHACL-шейпи, паркет складу, семантичний шар).

## Запуск з нуля (без ключів API)
Потрібні Python 3.13 і Linux x86_64 або WSL2; `falkordblite` не підтримує native Windows. Bash-скрипти й команди нижче виконуйте з Linux/WSL у каталозі `lab15_repo`.
```bash
python3 -m venv .venv && . .venv/bin/activate        # Python 3.13
pip install -r requirements.txt                       # langgraph 1.2.20, mcp 2.3.0, falkordblite 0.11.0, duckdb 2.0.0, pyshacl 0.40.2 ...
# search_docs використовує RAG з ЛР11: розпакувати її поруч як ../lab11_repo і підготувати моделі та граф
(cd ../lab11_repo && bash scripts/fetch_models.sh)
export LAB11_REPO=$(realpath ../lab11_repo) PYTHONHASHSEED=0
python3 -m pytest tests -q                            # 67 тестів: read-only, ролі, guards, памʼять TTL, HITL
bash scripts/run_all.sh                               # усі прогони з replay-кешу + генерація docs/*.md
python3 scripts/demo_mcp.py analyst                   # MCP-клієнт: список інструментів, виклики, відмови
python -m mcp_server.server                           # MCP-сервер (stdio); DKH_ROLE=reader|analyst|clinician; конфіг для IDE: mcp_server/mcp.json
```
Відповіді LLM відтворюються з `llm_cache/` (ключ = sha256(модель|system|user)). Нові запити потребують або нового офлайн-пакета (`scripts/llm_batches.py export/ingest`, див. `llm_log/README.md`), або `ANTHROPIC_API_KEY` у середовищі (клас `AnthropicLLM`, **у цій роботі не тестувався**; ключів у коді й звіті немає). Seed: температура й seed субагентів недоступні, тож прогін LLM — одна вибірка; весь інший код детермінований (PYTHONHASHSEED=0).

## Чесні обмеження
* «Мозок» агента — сліпі субагенти (claude-haiku-4-5, як налаштовано; фактична модель могла відрізнятися), не прямий API; усі «людські» ролі (рецензент, схвалювач у HITL) виконував LLM-асистент: **V3 студента очікується**, рішення HITL-демо позначені `decision_simulated=true`.
* R3: 25 сценаріїв автора; набір розширено після першого прогону; v0→v2 — не чисте held-out порівняння; 100 % на 25 сценаріях не доводить надійності.
* R4: у E1 справжня модель опиралась усім атакам навіть без захистів (0/22) → користь захистів показано лише в E2 «assume-breach» (скриптована «послушна» модель, моє припущення): naive 21/22 → hardened 1/22; залишається парафраз-ін'єкція A09. n = 22.
* Вартість — модельна (оцінка токенів × припущена ціна), не рахунок.
* Агент не медичний виріб; дані синтетичні; відповіді не перевірені клініцистом.
