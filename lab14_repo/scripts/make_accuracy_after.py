"""Re-review input: the sampled records that were changed by the repair (title/section) or absorbed by dedup, in their store_clean version."""
import sys, json, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from quality.common import ROOT, chunks
old = json.load(open(ROOT / "llm_log/in/accuracy_expert.json")); new = {c["chunk_id"]: c for c in chunks(ROOT / "store_clean")}
absorbed = {m["chunk_id"]: c["chunk_id"] for c in new.values() for m in c.get("merged_from", [])}; out = []
for o in old:
    cid = o["chunk_id"]; c = new.get(cid) or new.get(absorbed.get(cid, ""))
    if c and (c["title"] != o["title"] or c["section"] != o["section"] or cid in absorbed):
        out.append(dict(n=o["n"], chunk_id=c["chunk_id"], sample_chunk_id=cid, doc_id=c["doc_id"], title=c["title"], section=c["section"], type=c["type"], date=c["date"], sensitivity=c["sensitivity"], source_url=c["source_url"], lang=c["lang"], text=c["text"]))
json.dump(out, open(ROOT / "llm_log/in/accuracy_expert_after.json", "w"), ensure_ascii=False, indent=0); print(len(out), [o["chunk_id"] for o in out])
