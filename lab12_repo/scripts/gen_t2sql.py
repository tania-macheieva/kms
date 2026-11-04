"""Offline generation protocol for text-to-SQL. step 1: python3 scripts/gen_t2sql.py prep  -> llm_log/in/t2sql_in.json (prompts missing in the cache)
step 2 (subagent run, see llm_log/prompts/gen_protocol_t2sql_v1.txt) -> llm_log/raw/t2sql_out.json;  step 3: python3 scripts/gen_t2sql.py ingest"""
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT))
from t2sql.pipeline import Pipeline, ReplayLLM, SYSTEM, CacheMiss
tests = [json.loads(l) for l in open(ROOT / "tests/t2sql.jsonl", encoding="utf-8")]; p = Pipeline(ReplayLLM())
if sys.argv[1] == "prep":
    items = []
    for t in tests:
        user = p.prompt(t["question"])
        try: ReplayLLM().generate(SYSTEM, user)
        except CacheMiss: items.append(dict(id=t["id"], user=user))
    json.dump(dict(system=SYSTEM, items=items), open(ROOT / "llm_log/in/t2sql_in.json", "w"), ensure_ascii=False, indent=1); print("prompts to generate:", len(items))
else:
    inp = json.load(open(ROOT / "llm_log/in/t2sql_in.json", encoding="utf-8")); out = {o["id"]: o["text"] for o in json.load(open(ROOT / "llm_log/raw/t2sql_out.json", encoding="utf-8"))}
    for it in inp["items"]: ReplayLLM.store(inp["system"], it["user"], out[it["id"]])
    print("stored", len(inp["items"]))
