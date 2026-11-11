"""Offline protocol step 2: raw generator outputs -> replay cache (llm_cache/), keyed by sha256(model|system|user)."""
import os, sys, json, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent; L11 = pathlib.Path(os.environ.get("LAB11_REPO", ROOT.parent / "lab11_repo")).resolve(); sys.path.insert(0, str(L11))
from src.llm import ReplayLLM
from src import evalrag as E
inp = json.load(open(ROOT / "llm_log/in/gen_after.json")); out = {o["id"]: o["text"] for o in json.load(open(ROOT / "llm_log/raw/gen_after_out.json"))}
miss = [i["id"] for i in inp["items"] if i["id"] not in out]; assert not miss, miss
for it in inp["items"]: ReplayLLM.store(E.GEN_MODEL, inp["system"], it["user"], out[it["id"]], cache_dir=ROOT / "llm_cache")
print("stored", len(inp["items"]))
