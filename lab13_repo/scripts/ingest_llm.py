"""Ingest batch answers into the replay cache: python scripts/ingest_llm.py <pending.json> <raw_out.json> [model_actual]
raw_out.json: list of {"key": ..., "output": "<raw model text>"}; recorded in llm_log/log.csv by hand-free append."""
import json, sys, pathlib, csv, datetime
ROOT = pathlib.Path(__file__).resolve().parent.parent
pend = json.load(open(sys.argv[1])); raw = json.load(open(sys.argv[2])); model = pend["model"]
keys = {i["key"] for i in pend["items"]}; n = 0
(ROOT / "llm_cache").mkdir(exist_ok=True)
with open(ROOT / "llm_cache/cache.jsonl", "a", encoding="utf-8") as f:
    for r in raw:
        if r["key"] in keys:
            f.write(json.dumps({"key": r["key"], "model": model, "output": r["output"], "live": False, "ingested": datetime.date.today().isoformat(),
                                "source_file": pathlib.Path(sys.argv[2]).name}, ensure_ascii=False) + "\n"); n += 1
print(f"ingested {n}/{len(keys)}")
