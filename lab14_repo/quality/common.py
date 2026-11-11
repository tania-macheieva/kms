"""Shared access to the store snapshot (store/ = baseline from lab 11; store_clean/ = improved snapshot)."""
import json, csv, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
STORE = ROOT / "store"
def read_jsonl(p): return [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()]
def chunks(store=STORE): return read_jsonl(pathlib.Path(store) / "corpus.jsonl")
def graph_csv(store, name):
    return list(csv.DictReader(open(pathlib.Path(store) / "graph" / name, encoding="utf-8")))
def manifest(store=STORE): return json.load(open(pathlib.Path(store) / "docs_manifest.json", encoding="utf-8"))
