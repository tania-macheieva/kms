#!/usr/bin/env bash
# Повний відтворюваний запуск ЛР8 (seed 42). Потрібні Python 3.11+, Java 17+ (для HermiT через owlready2).
set -euo pipefail
cd "$(dirname "$0")/.."
export NO_PROXY=127.0.0.1,localhost no_proxy=127.0.0.1,localhost
python3 scripts/build_kb.py            # data/graphs/*.ttl, data/kb.ttl (когорта VAR-101..160, seed 42, HermiT)
python3 scripts/build_links.py         # data/links.ttl, links_decisions.csv, wikidata_mirror.ttl
python3 scripts/load_store.py          # store/ + docs/load_log.md + data/kb.jsonld (перебудовує store з нуля)
python3 scripts/bench.py 50000         # queries/results/bench.json
python3 scripts/run_queries.py         # queries/results/results.json (+ docs/sparql_results.md)
python3 scripts/verify_manual.py       # queries/results/manual_verification.json
python3 scripts/run_queries.py         # вдруге: docs/sparql_results.md вже з результатами ручної перевірки
python3 scripts/shacl_check.py         # shapes/report_*.ttl, shapes/shacl_summary.json
python3 scripts/owl_vs_shacl.py        # shapes/owl_vs_shacl.json (HermiT)
python3 scripts/make_shacl_report.py   # docs/shacl_report.md
python3 scripts/build_t2s.py           # tests/t2s.jsonl
python3 scripts/make_prompts.py        # llm_log/prompts, llm_log/in
python3 scripts/eval_t2s.py v1 v2      # llm_log/eval_*.json (відповіді моделі вже в llm_log/raw/)
python3 scripts/make_t2s_report.py     # docs/t2s_eval.md
python3 scripts/make_links_report.py   # docs/links_verification.md
python3 -m pytest -q tests
