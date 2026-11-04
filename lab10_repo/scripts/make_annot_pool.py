"""Second annotator: pooled (query, chunk) pairs for 12 queries; annotator A = gold evidence spans, B = blind LLM labels."""
import json, random, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT))
from src import chunking, hybrid, evaluate, metrics
docs = hybrid.load_docs(); gold = evaluate.load_gold(); by = lambda t: [g for g in gold if g["type"] == t]
rnd = random.Random(11)
sel = rnd.sample(by("keyword"), 3) + rnd.sample(by("paraphrase"), 3) + rnd.sample(by("multi_step"), 2) + rnd.sample(by("uk_cross"), 2) + rnd.sample(by("uk_internal"), 2)
ch = chunking.chunk_corpus(docs, "heading", max_words=250, min_words=40); R = hybrid.Retriever(ch, docs, "bge", tag="heading-250")
items, a_labels = [], {}
for g in sel:
    rows = []
    for mode in ("bm25", "dense", "hybrid", "hybrid_rerank"): rows += [r for r, _ in R.search(g["query"], mode, 5)]
    rows += [i for i, c in enumerate(ch) if any(metrics.covers(c.doc_id, c.start, c.end, e) for e in g["evidence"])]
    rows = sorted(set(rows))
    for r in rows:
        key = f"{g['qid']}|{ch[r].id}"; a_labels[key] = int(any(metrics.covers(ch[r].doc_id, ch[r].start, ch[r].end, e) for e in g["evidence"]))
        items.append(dict(key=key, query=g["query"], chunk_text=ch[r].text))
rnd.shuffle(items)
json.dump(items, open(ROOT / "llm_log/in/annot_b_items.json", "w"), ensure_ascii=False, indent=1)
json.dump(a_labels, open(ROOT / "eval/annotator_A.json", "w"), indent=1)
print(len(sel), len(items), sum(a_labels.values()))
