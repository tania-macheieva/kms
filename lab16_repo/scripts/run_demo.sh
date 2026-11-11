#!/usr/bin/env bash
# One command without Docker:  bash scripts/run_demo.sh [demo|serve|test]   (default: test + demo)
# Creates ./.venv, installs requirements.txt, then runs the unit tests and the 5-step demo (or serves the API on :8000).
set -euo pipefail
cd "$(dirname "$0")/.."
PY=${PYTHON:-python3}
if [ ! -d .venv ]; then "$PY" -m venv .venv; fi
. .venv/bin/activate
pip install -q -r requirements.txt
export PYTHONHASHSEED=0
case "${1:-all}" in
  test)  python -m pytest -q tests ;;
  demo)  python -m app.cli demo ;;
  serve) exec uvicorn app.main:app --host 0.0.0.0 --port 8000 ;;
  all)   python -m pytest -q tests && python -m app.cli demo ;;
esac
