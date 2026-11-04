#!/usr/bin/env bash
# Full ЛР12 pipeline (no network, no API keys; LLM outputs are replayed from data/llm_cache). Prereq: pip install -r requirements.txt
set -euo pipefail
cd "$(dirname "$0")/.."
export PYTHONHASHSEED=0
python3 etl/generate.py                 # data/raw/*.csv (seed 42)
python3 etl/load.py                     # DuckDB star schema, 22 DQ checks, Parquet, data/VERSION.json
python3 scripts/run_olap.py             # 15 OLAP queries -> eval/olap_results.json
python3 scripts/verify_olap.py          # independent pandas check
python3 scripts/check_semantic.py       # semantic-layer consistency
python3 scripts/build_t2sql.py && python3 scripts/eval_t2sql.py && python3 scripts/eval_t2sql.py naive
python3 -m pytest tests -q
python3 scripts/make_doc_olap.py && python3 scripts/make_doc_semantic.py && python3 scripts/make_doc_t2sql.py
python3 dashboard/build_dashboard.py
echo "OK"
