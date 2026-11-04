# ЛР13 — Видобування знань із текстів (Domain Knowledge Hub, медицина / геномні варіанти)
Конвеєр: схема → gold (два анотатори) → метод A (правила, spaCy) і метод B (LLM зі схемою) → оцінка P/R/F1 на test → нормалізація + граф із провенансом → закономірності.

## Запуск з нуля
Потрібні Python 3.13 і Linux x86_64 або WSL2; `falkordblite` не підтримує native Windows. Виконуйте команди в Linux Bash, у віртуальному середовищі:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m spacy download en_core_web_md
bash scripts/run_all.sh
```
Скрипт повторно перевіряє/встановлює залежності та модель; для чистого середовища потрібен доступ до PyPI і завантаження spaCy-моделі. Seed = 13 (відбір уривків, перестановки, бутстреп). **API-ключ не потрібен**: відповіді LLM відтворюються з `llm_cache/cache.jsonl` (ключ — sha256(модель|system|user)). Нова версія промпту → cache miss → `llm_log/in/pending_<tag>.json`, відповіді вносить `scripts/ingest_llm.py`; або `ANTHROPIC_API_KEY` у середовищі (ключ лише зі змінної, **живий режим не перевірявся**).

## Карта результатів
| Результат | Файли |
|---|---|
| R1 схема | `docs/extraction_schema.md`, `schema/extraction_output.schema.json`, `llm_log/prompts/annotate_v{1,2}.txt`, `llm_log/raw/pilot_out.json` |
| R2 gold | `data/gold.jsonl`, `docs/gold_card.md`, `eval/gold_stats.json`, `scripts/build_gold.py`, `llm_log/raw/annot_A{1,2}.json`, `llm_log/raw/adjudication.json` |
| R3 методи | `src/extract_rules.py`, `src/extract_llm.py`, `src/llm_client.py`, `results/*.jsonl` (провенанс: document, passage_id, start/end/doc_start, model, prompt_version), `eval/tuning_log.md` |
| R4 оцінка | `docs/extraction_eval.md`, `eval/test_summary.json`, `eval/errors.csv`, `src/evaluate.py`, `scripts/analyze_test.py` |
| R5 граф і патерни | `data/graph_load.cypher`, `data/graph_load.ttl`, `data/entities_linked.csv`, `docs/normalization.md`, `docs/patterns.md`, `eval/patterns_rules.csv`, `eval/graph_stats.json` |
| Протокол | `llm_log/` (log.csv, README), `claims/claims.csv` |

Граф: ребра `(:Entity)-[:HAS_OPTION|PERFORMS|…{source, start, end, doc_start, evidence, model, prompt_version, method, confidence}]->(:Entity)`. Завантаження у Neo4j: виконати `data/graph_load.cypher`; у середовищі виконання Neo4j недоступний, тому перевірено на FalkorDB (falkordblite, `GRAPH.RO_QUERY`) — evidence-запит див. `eval/graph_stats.json`. RDF: reified-вузли `ex:Statement` у `data/graph_load.ttl`.

## Відхилення від завдання та чесні застереження
- Обидва «анотатори», адʼюдикатор та екстрактор B — LLM (sonnet/haiku, одна родина); «людське» рішення ухвалював LLM-асистент, студент перевіряє вибірково (V3 = pending).
- Температура/seed LLM не керовані; вартість B — модельна (ціни не перевірено), реальних API-викликів не було.
- Відношень у gold 108 (≥150 тверджень досягнуто сумою з типізованими сутностями); типи COMPUTES_METRIC, USES_RESOURCE, INVOKES мають <6 прикладів на test.
- Словник методу A складено з dev gold → dev-оцінка A оптимістична; гібрид-політика з dev не узагальнилась; «постфактум-гібрид» — гіпотеза.
- Закономірності: 6 із 28 прийнято; 3 (VEP/SnpEff/vcfanno → annotation) мають спільний механізм.
- Гілка git: `lab13`. Ключів у коді немає.
