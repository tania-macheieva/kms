"""Оцінка відповідей LLM для text-to-Cypher: python3 scripts/eval_t2c.py r1 r2 → llm_log/eval_t2c_{r}.json"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import t2c  # noqa: E402

ROOT = t2c.ROOT
QS = [json.loads(l) for l in (ROOT / "tests/t2c.jsonl").read_text(encoding="utf-8").splitlines()]


def evaluate(run):
    raw = {}
    for suf in ("", "h"): raw.update(json.loads((ROOT / f"llm_log/raw/t2c_{run}{suf}.json").read_text(encoding="utf-8")))
    out = [{"id": q["id"], "tier": q["tier"], "raw": raw.get(q["id"], ""), **t2c.evaluate_one(raw.get(q["id"], ""), q["gold_answer"])} for q in QS]
    (ROOT / f"llm_log/eval_t2c_{run}.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    return out


if __name__ == "__main__":
    for run in sys.argv[1:]:
        o = evaluate(run); n = len(o)
        print(run, {"safe": sum(r["safe_ok"] for r in o), "schema": sum(r["schema_ok"] for r in o), "exec": sum(r["exec_ok"] for r in o), "result": sum(r["result_ok"] for r in o), "n": n})
        for r in o:
            if not r["result_ok"]: print("  ", r["id"], r["error_stage"], r["detail"][:230])
