"""Select source chunks (seed 42) for LLM query generation. Writes llm_log/in/gold_*.json and the prompts."""
import json, random, collections
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
rnd = random.Random(42)
C = [json.loads(l) for l in open(ROOT / "data/corpus.jsonl", encoding="utf-8")]
BAD_TYPES = {"citations"}
ok = [c for c in C if 80 <= c["n_words"] <= 280 and c["type"] not in BAD_TYPES]
pub = [c for c in ok if c["sensitivity"] == "public"]; inn = [c for c in ok if c["sensitivity"] != "public"]
rnd.shuffle(pub); rnd.shuffle(inn)
cap, per, picked = 4, collections.Counter(), []
for c in pub:
    if per[c["doc_id"]] < cap and len(picked) < 42: picked.append(c); per[c["doc_id"]] += 1
uk_int = inn[:4]
kinds = ["keyword"] * 18 + ["paraphrase"] * 20 + ["uk_cross"] * 4
rnd.shuffle(kinds)
single = [dict(chunk_id=c["chunk_id"], kind=k, doc=c["title"], section=c["section"], text=c["text"]) for c, k in zip(picked, kinds)]
single += [dict(chunk_id=c["chunk_id"], kind="uk_internal", doc=c["title"], section=c["section"], text=c["text"]) for c in uk_int]
# pairs: two non-adjacent chunks of one document
bydoc = collections.defaultdict(list)
for c in pub: bydoc[c["doc_id"]].append(c)
docs = [d for d, v in bydoc.items() if len(v) >= 4]; rnd.shuffle(docs); pairs = []
for d in docs[:10]:
    a, b = rnd.sample(bydoc[d], 2); pairs.append(dict(pair_id=f"{a['chunk_id']}+{b['chunk_id']}", doc=a["title"], chunk_a=dict(chunk_id=a["chunk_id"], section=a["section"], text=a["text"]), chunk_b=dict(chunk_id=b["chunk_id"], section=b["section"], text=b["text"])))
titles = sorted({(c["title"], c["doc_id"]) for c in C if c["sensitivity"] == "public"})
json.dump(single, open(ROOT / "llm_log/in/gold_single.json", "w"), ensure_ascii=False, indent=1)
json.dump(pairs, open(ROOT / "llm_log/in/gold_pairs.json", "w"), ensure_ascii=False, indent=1)
json.dump([t for t, _ in titles], open(ROOT / "llm_log/in/gold_titles.json", "w"), ensure_ascii=False, indent=1)
print(len(single), len(pairs), len(titles), collections.Counter(s["kind"] for s in single))
