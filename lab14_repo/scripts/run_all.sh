#!/usr/bin/env bash
# Run everything from scratch. Needs ../lab11_repo (models fetched, graph imported) — see README. Offline: no API key needed.
set -euo pipefail; cd "$(dirname "$0")/.."; export PYTHONHASHSEED=0
python3 scripts/make_pairs.py                     # only if you want to regenerate the labelling batches (LLM labels in llm_log/raw are kept)
python3 scripts/build_pairs_gold.py
python3 scripts/eval_dedup.py
python3 scripts/make_judge_pairs.py
python3 scripts/run_dedup.py
python3 scripts/build_clean_store.py
python3 scripts/demo_alternatives.py
python3 quality/profile.py --store store --label baseline --sample llm_log/raw/accuracy_expert.json
cp quality/metrics_baseline.json quality/metrics.json
python3 quality/profile.py --store store_clean --label after --sample llm_log/raw/accuracy_expert.json llm_log/raw/accuracy_expert_after.json llm_log/raw/accuracy_expert_after_absorbed.json
python3 -m pytest tests -q
python3 scripts/history_demo.py
python3 scripts/inject_defects.py
python3 quality/gate.py --store store_clean --label ci | tee quality/gate_log.txt
python3 scripts/run_rag_after.py run && python3 scripts/aggregate_after.py && python3 scripts/probe_dups.py
python3 scripts/make_docs.py
