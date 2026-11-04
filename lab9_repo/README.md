# Domain Knowledge Hub — ЛР9: Графова база знань (LPG, Cypher)

Предметна область: біомедичні дані (якість варіантів GATK, каскадне тестування BRCA). Гілка: `lab09`. Дані синтетичні; персональних даних і ключів API немає.

## ⚠ Рушій: FalkorDB, не Neo4j
У середовищі виконання не було Docker-демона, а завантаження Neo4j заблоковане, тому використано **FalkorDB** (вбудований `falkordblite`, мова openCypher). Наслідки: (1) `SHOW CONSTRAINTS/INDEXES` замінено на `CALL db.constraints()/db.indexes()`, DDL створення обмежень виконується API, а не Cypher (довідковий Neo4j-DDL — `import/00_schema.neo4j.cypher`); (2) `shortestPath` дозволений лише в `RETURN/WITH` і лише спрямований; (3) GDS немає: PageRank — нативний `algo.pageRank`, Louvain — `networkx` (seed 42); (4) read-only — через `GRAPH.RO_QUERY`. Для справжнього Neo4j 5 див. `docker-compose.yml` (не перевірено).

## Структура
| Шлях | Зміст |
|---|---|
| `docs/graph_schema.png`, `docs/cq_mapping.md` | R1: схема, 12 CQ → шаблони, походження, порівняння з ЛР7 |
| `data/*.csv`, `import/*.cypher`, `docs/import_log.md` | R2: CSV, LOAD CSV/MERGE, обмеження, індекси, ідемпотентність |
| `queries/c*.cypher`, `docs/cypher_results.md` | R3: 11 запитів, 2 аналізи впливу, ручна перевірка |
| `docs/gds_report.md` | R4: PageRank, Louvain, PROFILE, оптимізація |
| `docs/sparql_vs_cypher.md`, `tests/t2c.jsonl` | R5: порівняння, text-to-Cypher |
| `llm_log/`, `claims/` | протокол «LLM-експерт» |

## Запуск з нуля
Потрібні Python 3.11+ (перевірено 3.13) і Linux x86_64 або WSL2: `falkordblite` не підтримує native Windows. Версії пакетів — `requirements.txt` (falkordblite 0.11.0, pyoxigraph 0.5.13, rdflib 7.6.0, networkx).
```
python3 -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt
bash scripts/run_all.sh          # ~1 хв; LOAD CSV читає з /var/lib/FalkorDB/import (змінна FALKORDB_IMPORT_DIR)
```
У Windows запускайте команди з WSL2, перебуваючи в Linux-копії проєкту; Windows `.venv` і PowerShell для цієї роботи не підходять. Вхід — `data/graphs/*.ttl` (RDF-граф ЛР8; `scripts/store.py` взято з ЛР8). Seed 42 — лише Louvain; синтетичний граф для оптимізації детермінований формулою.

## Відомі обмеження
- Не Neo4j/GDS (див. вище); діалектні відмінності вплинули на один із text-to-Cypher запитів (t20).
- `toFloat()` у FalkorDB повертає float32-точність → у `import/*.cypher` значення округлюються `round(x*1000)/1000`.
- Еталони, запити й схему склала та сама система, що генерувала відповіді; V3/V4 не досягнуто.
- 11 «складних» питань text-to-Cypher додано після перших результатів.
- `confidence` на зв'язках — мій призначений рівень за категорією джерела, не статистична оцінка.
- Каталог бази `fdb/` не входить в архів: створюється скриптами.
