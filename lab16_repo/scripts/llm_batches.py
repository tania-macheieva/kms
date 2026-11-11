"""Offline LLM protocol (no API key). 
  python scripts/llm_batches.py export <name> <todo.json> [--size 8]  -> llm_log/in/<name>_NN.json   (prompts the replay cache is missing)
  python scripts/llm_batches.py ingest                                  -> reads llm_log/raw/*.json ({key: text}) into llm_cache/ and appends llm_log/log.csv
Each in-file: {"batch": ..., "items": [{"key","tag","system","user"}]}; the blind LLM writes llm_log/raw/<same name>.json = {"<key>": "<raw output>"}."""
import sys, json, pathlib, csv, datetime as dt
ROOT = pathlib.Path(__file__).resolve().parent.parent; sys.path.insert(0, str(ROOT))
from reco.llm import ReplayLLM, key_of, MODEL
def export(name, todo, size=8):
    todo = json.load(open(todo, encoding="utf-8")); items = list(todo.values()); (ROOT / "llm_log/in").mkdir(parents=True, exist_ok=True)
    for i in range(0, len(items), size):
        f = ROOT / f"llm_log/in/{name}_{i // size:02d}.json"; json.dump(dict(batch=f.stem, items=items[i:i + size]), open(f, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(len(items), "prompts ->", (len(items) + size - 1) // size, "batch files")
def ingest():
    n = 0; log = ROOT / "llm_log/log.csv"; new = not log.exists(); rows = []
    for f in sorted((ROOT / "llm_log/raw").glob("*.json")):
        raw = json.load(open(f, encoding="utf-8")); inp = ROOT / "llm_log/in" / f.name
        if not inp.exists(): continue
        items = {it["key"]: it for it in json.load(open(inp, encoding="utf-8"))["items"]}
        for k, text in raw.items():
            it = items.get(k)
            if it is None or (ROOT / "llm_cache" / f"{k}.json").exists(): continue
            ReplayLLM.store(it["system"], it["user"], text); n += 1; rows.append([dt.date.today().isoformat(), f.stem, k[:12], it.get("tag", ""), MODEL, "temperature=default(not controllable); seed=n/a", len(text)])
    with open(log, "a", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        if new: w.writerow(["date", "batch", "key12", "tag", "model", "parameters", "raw_chars"])
        w.writerows(rows)
    print("ingested", n)
if __name__ == "__main__":
    a = sys.argv[1:]
    if a[0] == "export": export(a[1], a[2], int(a[a.index("--size") + 1]) if "--size" in a else 8)
    else: ingest()
