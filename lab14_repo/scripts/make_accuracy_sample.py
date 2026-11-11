import sys, json, random, collections, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from quality.common import ROOT, chunks
random.seed(14); ch = chunks(ROOT / "store"); by = collections.defaultdict(list)
for c in ch: by[c["doc_id"]].append(c)
docs = sorted(by); pick = []
for d in docs: pick.append(random.choice(by[d]))                       # one per document (29 docs)
rest = [c for c in ch if c not in pick]; pick += random.sample(rest, 36 - len(pick)); random.shuffle(pick)
items = [dict(n=i + 1, chunk_id=c["chunk_id"], doc_id=c["doc_id"], title=c["title"], section=c["section"], type=c["type"], date=c["date"], sensitivity=c["sensitivity"], source_url=c["source_url"], lang=c["lang"], text=c["text"]) for i, c in enumerate(pick)]
json.dump(items, open(ROOT / "llm_log/in/accuracy_expert.json", "w"), ensure_ascii=False, indent=0); print(len(items), len({i["doc_id"] for i in items}), "docs")
