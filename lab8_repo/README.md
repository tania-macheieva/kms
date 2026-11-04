# Domain Knowledge Hub — ЛР8: RDF-сховище та SPARQL-запити

Предметна область: біомедичні дані (контроль якості варіантів GATK, каскадне тестування BRCA). Гілка: `lab08`. Дані синтетичні; персональних даних немає; ключів API немає.

## Структура
| Шлях | Зміст |
|---|---|
| `data/kb.ttl`, `data/graphs/*.ttl` | граф знань (TBox, ABox, виведене HermiT), версія kb-0.1.0 |
| `data/kb.jsonld` | JSON-LD для 69 сутностей |
| `data/links.ttl`, `data/links_decisions.csv` | зв'язки з Wikidata (прийняті/відхилені) |
| `docs/load_log.md` | завантаження в триплстор + підтвердження COUNT |
| `queries/*.rq`, `docs/sparql_results.md` | 9 запитів, результати, час, ручна перевірка |
| `shapes/shapes.ttl`, `docs/shacl_report.md` | форми SHACL, звіти, OWL vs SHACL |
| `tests/t2s.jsonl`, `docs/t2s_eval.md` | text-to-SPARQL: 24 питання, метрики v1/v2, помилки |
| `docs/links_verification.md` | перевірка зв'язків, відхилені, федеративний запит |
| `llm_log/`, `claims/` | протокол роботи з LLM |

## Запуск з нуля
Версії: Python 3.13 (3.11+), Java 17+ (HermiT з owlready2), pyoxigraph 0.5.13, rdflib 7.6.0, pyshacl 0.40.1, owlready2 0.51.
Linux/macOS:
```
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
bash scripts/run_all.sh        # seed 42; ~1–2 хв
```
Windows PowerShell (активація середовища):
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python scripts/load_store.py
python -m pytest -q tests
```
`load_store.py` треба виконати перед окремим запуском тестів: він створює локальне сховище `store/` з RDF-файлів у `data/graphs/`. Повний `scripts/run_all.sh` робить це автоматично.
Якщо PowerShell забороняє запуск `Activate.ps1`, виконайте для поточного вікна `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`, а потім повторіть команду активації. Повний `scripts/run_all.sh` потребує Bash: запускайте його в Git Bash, попередньо активувавши Windows-середовище командою `source .venv/Scripts/activate`, або у WSL зі створеним окремо Linux-середовищем. Окремо для Linux/macOS: `python3 -m pytest -q tests`. Seed когорти — 42 (`scripts/build_kb.py`, `scripts/bench.py`).

## Відомі обмеження (чесно)
- Замість Fuseki/GraphDB використано **pyoxigraph** (Docker і Maven у середовищі недоступні).
- Федеративний запит (q09) працює проти **локального дзеркала** міток Wikidata (`scripts/mock_wikidata.py`), а не живої Wikidata. Для живого ендпоїнта: `WIKIDATA_ENDPOINT=https://query.wikidata.org/sparql python3 scripts/run_queries.py`.
- Зв'язки з Wikidata перевірено лише за заголовками у списку пошуку (рівень V1).
- LLM-генератори text-to-SPARQL — субагенти тієї самої моделі; температура/seed не контролювались; еталони склала та сама система.
- Дані синтетичні; питання CQ19 додано у ЛР8.
- `store/` перебудовується скриптом `load_store.py`; у архів не входить.
