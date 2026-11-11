#!/usr/bin/env bash
# Reproduces all numbers of lab 15 from the replay cache (no API key). Needs ../lab11_repo (or LAB11_REPO) with models + graph (see README).
set -euo pipefail; cd "$(dirname "$0")/.."; export PYTHONHASHSEED=0; export LAB11_REPO="${LAB11_REPO:-$(realpath ../lab11_repo)}"
python3 -m pytest tests -q                                                              # read-only, roles, guards, memory, HITL
python3 scripts/run_agent.py tests/agent_scenarios.jsonl --policy hardened --plan plan_v2 --draft draft_v2 --out eval/v2.json --trace logs/trace_v2.jsonl
python3 scripts/eval_metrics.py eval/v0.json eval/v1.json eval/v2.json                  # v0/v1 are stored runs (their prompts/cache are in llm_cache)
python3 scripts/run_attacks.py --policy naive --brain compromised --out eval/e2_naive.json
python3 scripts/run_attacks.py --policy hardened --brain compromised --out eval/e2_hardened.json --trace logs/trace_e2_hardened.jsonl
for d in input_filter output_guard ro_validator role_scope tool_pinning verify limits; do python3 scripts/run_attacks.py --policy hardened --brain compromised --off $d --out eval/e2_off_$d.json; done
python3 scripts/run_attacks.py --policy naive --out eval/attacks_naive.json                      # E1 (replayed real-brain outputs)
python3 scripts/run_attacks.py --policy hardened --out eval/attacks_hardened.json
python3 scripts/demo_hitl.py
python3 scripts/demo_mcp.py analyst && python3 scripts/demo_mcp.py reader
python3 scripts/make_spec.py && python3 scripts/make_eval.py && python3 scripts/make_security.py && python3 scripts/make_hitl_doc.py && python3 scripts/make_llm_log.py
