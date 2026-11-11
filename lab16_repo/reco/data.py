"""Catalogue of recommendable items = Hub chunks (lab 14 clean store + 6 unverified fixture notes) with access / quality metadata."""
from __future__ import annotations
import json, pathlib, datetime as dt
import numpy as np
ROOT = pathlib.Path(__file__).resolve().parent.parent; HUB = ROOT / "hub"
ROLE_RANK = {"reader": 0, "analyst": 1, "clinician": 2}; SENS_RANK = {"public": 0, "internal": 1, "restricted": 2}
AS_OF = dt.date(2026, 11, 8)                       # "today" for freshness
def load_items():
    """-> list of dict(id, doc, title, section, type, date, sensitivity, source_url, text, verified, kind). `verified` = official upstream doc with an https source or an own report whose provenance is a local lab file; fixtures are NOT verified."""
    items = []
    for l in open(HUB / "corpus.jsonl", encoding="utf-8"):
        c = json.loads(l); src = c["source_url"]
        ok = src.startswith("https://github.com/") or src.startswith("local:")
        items.append(dict(id=c["chunk_id"], doc=c["doc_id"], title=c["title"], section=c["section"], type=c["type"], date=c["date"], sensitivity=c["sensitivity"], source_url=src, text=c["text"], verified=ok, kind="doc"))
    for f in json.load(open(HUB / "fixtures.json", encoding="utf-8")):      # community / unreviewed notes (some poisoned) from labs 11, 14, 15
        items.append(dict(id=f["id"], doc="fx_" + f["id"], title=f["id"], section="note", type="community-note", date="2026-09-15", sensitivity="public" if "inject" in f["id"] or "java" in f["id"] else "internal", source_url="local:fixtures", text=f["text"], verified=False, kind="fixture"))
    return items
def allowed(item, role): return SENS_RANK[item["sensitivity"]] <= ROLE_RANK[role]
def age_days(item, as_of=AS_OF): return (as_of - dt.date.fromisoformat(item["date"])).days
def eligible(items, role, verified_only=True, max_age_days=None, as_of=AS_OF):
    """quality + access filters (R1 C2). Returns indices."""
    return [i for i, it in enumerate(items) if allowed(it, role) and (it["verified"] or not verified_only) and (max_age_days is None or age_days(it, as_of) <= max_age_days)]
def load_embeddings(items):
    f = HUB / "emb_bge.npy"; return np.load(f)
