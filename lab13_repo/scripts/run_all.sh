#!/usr/bin/env bash
# Full reproduction from a clean checkout (Python 3.13). ~3 min on CPU. No API key needed: LLM answers come from llm_cache/.
set -euo pipefail
cd "$(dirname "$0")/.."
pip install -r requirements.txt --break-system-packages -q
python -m spacy download en_core_web_md -q || true      # needs network; skip if model already installed
python scripts/select_passages.py                      # passages.jsonl (seed 13)  [already committed; deterministic]
python scripts/build_gold.py                           # gold.jsonl + kappa from raw annotations
mkdir -p results
python src/extract_rules.py --split dev  --out results/rules_dev.jsonl
python src/extract_rules.py --split test --out results/rules_test.jsonl
python src/extract_llm.py --split dev  --tag dev_v2  --prompt v2 --out results/llm_dev_v2.jsonl
python src/extract_llm.py --split test --tag test_v2 --prompt v2 --out results/llm_test_v2.jsonl
python scripts/analyze_test.py                         # metrics, hybrid, citations, cost, errors
python scripts/build_graph.py                          # entities_linked.csv, graph_load.ttl/.cypher, FalkorDB evidence query
python scripts/patterns.py && python scripts/make_patterns_md.py
python scripts/make_docs.py                            # docs/extraction_eval.md, docs/gold_card.md
python scripts/claims_summary.py
python -m pytest -q tests
