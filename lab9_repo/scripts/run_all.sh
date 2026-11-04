#!/usr/bin/env bash
# Повний відтворюваний запуск ЛР9 (seed 42 лише для Louvain; решта детермінована). Python 3.11+; запис у /var/lib/FalkorDB/import (або FALKORDB_IMPORT_DIR).
set -euo pipefail
cd "$(dirname "$0")/.."
python3 scripts/build_csv.py            # data/*.csv з RDF ЛР8 (data/graphs)
python3 scripts/make_import.py          # import/*.cypher
python3 scripts/import_graph.py         # схема, LOAD CSV/MERGE x2, обмеження, docs/import_log.md
python3 scripts/run_cypher.py           # queries/results/results.json
python3 scripts/verify_manual.py        # ручна звірка (Python по CSV)
python3 scripts/run_cypher.py           # вдруге: docs/cypher_results.md з ручною звіркою
python3 scripts/gds.py 20000            # PageRank, Louvain, збереження у граф, PROFILE, оптимізація (граф bench)
python3 scripts/make_gds_report.py      # docs/gds_report.md
python3 scripts/build_t2c.py            # tests/t2c.jsonl
python3 scripts/make_t2c_prompts.py     # llm_log/prompts, llm_log/in
python3 scripts/eval_t2c.py r1 r2       # llm_log/eval_t2c_*.json (відповіді LLM вже в llm_log/raw/)
python3 scripts/t2c_safety.py           # docs/evidence/t2c_safety.json
python3 scripts/compare_sparql_cypher.py
python3 scripts/make_sparql_vs_cypher.py
python3 -m pytest -q tests
