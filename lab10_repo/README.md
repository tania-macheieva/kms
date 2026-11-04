# ЛР10 — Векторне сховище та семантичний пошук (Domain Knowledge Hub, медицина)

Корпус відкритої документації інструментів аналізу геномних варіантів (nf-core/sarek, raredisease, bcftools, GATK; 33 документи, 688 фрагментів) + власні звіти ЛР4–ЛР9 (з позначками чутливості). Побудовано індекс FAISS HNSW для двох моделей embeddings, порівняно 4 стратегії chunking, реалізовано BM25 + dense + RRF + reranker + pre-filter, золотий набір із 61 запиту, κ, метрики recall@5/10, MRR, nDCG@10.

## Артефакти за результатами
| Результат | Файли |
|---|---|
| R1 Корпус | `data/corpus.jsonl`, `docs/corpus_card.md`, `scripts/build_corpus.py` |
| R2 Chunking | `src/chunking.py`, `docs/chunking_cmp.md` |
| R3 Індекс і embeddings | `src/index.py`, `src/embed.py`, `docs/embeddings_cmp.md` |
| R4 Гібрид і reranking | `src/hybrid.py`, `docs/hybrid_report.md` |
| R5 Gold і оцінювання | `eval/gold.jsonl`, `docs/search_eval.md` |
| Протокол LLM | `llm_log/`, `claims/claims.csv` |
| Сирі числа | `docs/evidence/*.json` |

## Що відрізняється від завдання (чесно)
- **Моделі:** multilingual-e5 недоступна (HuggingFace заблоковано в середовищі). Використано all-MiniLM-L6-v2 (int8) і bge-small-en-v1.5 — обидві англомовні; ваги — з npm-пакетів (`scripts/fetch_models.sh`). Корпус та головні запити англійські; українські запити виміряно окремо.
- **Reranker:** замість cross-encoder (ваг немає) — late-interaction MaxSim на токенних векторах bge; це не cross-encoder.
- **«Людський» перегляд** золотого набору і розбіжностей розмітників виконав LLM-асистент; студент має повторити (див. `claims/claims.csv`, статус pending).
- Температура/seed LLM не керуються; для пошуку все детерміновано (HNSW із фіксованою побудовою, seed 42/7/11, `PYTHONHASHSEED=0`).

## Запуск з нуля
Потрібні Python 3.13, Node.js/npm та Bash (Linux/macOS, WSL2 або Git Bash); повний конвеєр виконує `.sh`-скрипти й перевірку `sha256sum`. У PowerShell можна активувати середовище командою `.\.venv\Scripts\Activate.ps1`, але `fetch_models.sh` і `run_all.sh` запускайте в Git Bash або WSL.
Windows PowerShell: `python -m venv .venv`, `.\.venv\Scripts\Activate.ps1`, `python -m pip install -r requirements.txt`; далі в Git Bash перейдіть до цього каталогу й активуйте те саме середовище через `source .venv/Scripts/activate`.
```bash
python3 -m venv .venv && . .venv/bin/activate     # Python 3.13
pip install -r requirements.txt                    # numpy 2.5.3, onnxruntime 1.29.0, tokenizers 0.23.3, faiss-cpu 1.15.1, rank-bm25 0.2.2, pytest 9.1.1
bash scripts/fetch_models.sh                       # потрібні node/npm; ~150 МБ ваг (SHA256 у data/models/SHA256SUMS)
bash scripts/run_all.sh                            # повний конвеєр + 12 тестів
```
`data/cache/` містить закешовані вектори (з нею прогін ≈ 6–8 хв, без неї ≈ 35 хв на 2 ядрах CPU). Корпус перебудовується з `data/raw/` (+ `data/sources.json`); щоб оновити зі свіжих клонів репозиторіїв, задайте `DKH_SRC` (папка з клонами sarek, raredisease, bcftools, gatk).

## Структура
`src/` — бібліотека (embed, chunking, index, hybrid, metrics, evaluate); `scripts/` — експерименти й генерація документів; `tests/` — 12 автотестів; `eval/` — gold, розмітка A, арбітраж; `data/` — сирі й очищені документи, корпус, індекс (`data/index/`); `docs/` — звіти й evidence; `llm_log/`, `claims/` — протокол LLM-експерта.
Гілка git: `lab10` (git-репозиторій у цій сесії не ініціалізовано — створіть гілку при коміті).
Ключі API не використовуються; персональні дані зовнішнім сервісам не передавалися.
