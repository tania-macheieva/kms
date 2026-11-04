#!/usr/bin/env bash
# Model weights are not stored in git/zip (150 MB). They are public, permissively licensed ONNX exports shipped
# inside npm packages (HuggingFace is not reachable from the lab sandbox). Needs node/npm + network to registry.npmjs.org.
set -euo pipefail
cd "$(dirname "$0")/.."
T=$(mktemp -d); mkdir -p data/models/minilm data/models/bge
( cd "$T" && npm pack @ryanstark24/sfgraph-models@1.6.2 @coree-ai/coree-model-bge-small-en-v1.5@1.0.2 --silent && for f in *.tgz; do mkdir -p "x/${f%.tgz}" && tar xzf "$f" -C "x/${f%.tgz}"; done )
M=$(ls -d "$T"/x/ryanstark24-*/package/data/Xenova/all-MiniLM-L6-v2)
cp "$M/onnx/model_quantized.onnx" data/models/minilm/model.onnx; cp "$M/tokenizer.json" "$M/tokenizer_config.json" data/models/minilm/
B=$(ls -d "$T"/x/coree-ai-*/package/model/models--Xenova--bge-small-en-v1.5/snapshots/*)
cp "$B/onnx/model.onnx" "$B/tokenizer.json" "$B/tokenizer_config.json" data/models/bge/
sha256sum data/models/*/model.onnx | tee data/models/SHA256SUMS; rm -rf "$T"
