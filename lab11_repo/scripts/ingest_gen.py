"""Offline generation protocol, step 2: move raw model outputs (llm_log/raw/gen_<set>_out.json) into the replay cache data/llm_cache/."""
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT))
from src.llm import ReplayLLM
from src import evalrag as E

def main(which):
    inp = json.load(open(ROOT / f"llm_log/in/gen_{which}.json", encoding="utf-8")); out = {o["id"]: o["text"] for o in json.load(open(ROOT / f"llm_log/raw/gen_{which}_out.json", encoding="utf-8"))}
    miss = [i["id"] for i in inp["items"] if i["id"] not in out]; assert not miss, miss
    for it in inp["items"]: ReplayLLM.store(E.GEN_MODEL, inp["system"], it["user"], out[it["id"]])
    print(which, "stored", len(inp["items"]))

if __name__ == "__main__": main(sys.argv[1])
