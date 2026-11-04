"""Оцінка відповідей LLM: python3 scripts/eval_t2s.py v1 [v2 ...] → llm_log/eval_{v}.json і зведення метрик за split."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import t2s  # noqa: E402

ROOT = t2s.ROOT


def load_raw(v):
    d = {}
    for f in sorted((ROOT / "llm_log/raw").glob(f"{v}_b*.json")): d.update(json.loads(f.read_text(encoding="utf-8")))
    return d


def evaluate(v):
    qs = [json.loads(l) for l in (ROOT / "tests/t2s.jsonl").read_text(encoding="utf-8").splitlines()]
    raw = load_raw(v); vocab = t2s.vocabulary(); out = []
    for q in qs:
        r = t2s.evaluate_one(None, vocab, raw.get(q["id"], ""), q["gold_answer"])
        out.append({"id": q["id"], "split": q["split"], "raw": raw.get(q["id"], ""), **r})
    (ROOT / f"llm_log/eval_{v}.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    return out


def metrics(rows):
    n = len(rows)
    return {"n": n, "syntax": sum(r["syntax_ok"] for r in rows), "schema": sum(r["syntax_ok"] and r["schema_ok"] for r in rows), "result": sum(r["result_ok"] for r in rows)}


if __name__ == "__main__":
    for v in sys.argv[1:]:
        o = evaluate(v)
        for sp in (None, "dev", "heldout"):
            rows = [r for r in o if sp is None or r["split"] == sp]; print(v, sp or "all", metrics(rows))
        for r in o:
            if not r["result_ok"]: print("  ", r["id"], r["error_stage"], r["detail"][:200])
