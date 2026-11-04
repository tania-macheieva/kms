#!/usr/bin/env bash
# Full ЛР11 pipeline from the replay cache (no network, no API keys). Prereq: pip install -r requirements.txt; bash scripts/fetch_models.sh
set -euo pipefail
cd "$(dirname "$0")/.."
export PYTHONHASHSEED=0
[ -d graph_kb/fdb ] && [ -n "$(ls -A graph_kb/fdb 2>/dev/null)" ] || ( cd graph_kb/scripts && python3 import_graph.py )   # build graph 'dkh' (370 nodes, 757 rels)
python3 scripts/build_eval.py                 # eval/rag_eval.jsonl, graph_questions.jsonl, fixtures.json
python3 -m pytest tests -q
python3 scripts/demo_rag.py > docs/evidence/demo_rag.txt            # R1 demo, logs/rag_log.jsonl
python3 scripts/run_eval.py A && python3 scripts/run_eval.py B       # eval/results_{A,B}.json
python3 scripts/aggregate.py A > /dev/null && python3 scripts/aggregate.py B > /dev/null
python3 scripts/run_r2.py > /dev/null          # R2 text vs graph
python3 scripts/make_doc_r2.py && python3 scripts/make_doc_r4.py && python3 scripts/make_doc_r5.py
echo "OK: docs/graph_vs_text.md docs/rag_eval.md docs/rag_optimization.md regenerated"
