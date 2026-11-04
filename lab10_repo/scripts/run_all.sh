#!/usr/bin/env bash
# Full pipeline. With data/cache present (shipped in the zip) it takes ~6-8 min on 2 CPU cores; without it ~35 min (embedding on CPU).
set -euo pipefail
cd "$(dirname "$0")/.."
export PYTHONHASHSEED=0
[ -f data/models/bge/model.onnx ] && [ -f data/models/minilm/model.onnx ] || bash scripts/fetch_models.sh
sha256sum -c data/models/SHA256SUMS
python3 scripts/build_corpus.py            # R1  data/corpus.jsonl, docs_clean/
python3 scripts/make_corpus_card.py        # R1  docs/corpus_card.md
python3 scripts/build_gold.py              # R5  eval/gold.jsonl (LLM candidates + review + adjudication)
python3 scripts/make_subsets.py            #     10 / 20 query subsets (seed 7)
python3 scripts/exp_chunking.py            # R2  docs/evidence/chunking.json, chosen_chunking.json
python3 scripts/exp_index.py               # R3  docs/evidence/index.json
python3 scripts/exp_update.py              # R3  upsert/delete on 5 documents
python3 scripts/exp_timing.py              # R3  uncached embedding throughput
python3 scripts/exp_hybrid.py              # R4  docs/evidence/hybrid.json
python3 scripts/exp_eval.py                # R5  docs/evidence/search_eval.json
python3 scripts/exp_paired.py              # R5  paired bootstrap
python3 scripts/make_docs.py               # docs/{chunking_cmp,embeddings_cmp,hybrid_report,search_eval}.md
python3 -m pytest -q tests
