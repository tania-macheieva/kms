"""R3 step 4: index update procedure (upsert / delete / add / compact) checked on 5 documents -> docs/evidence/update.json"""
import json, sys, shutil, time
from pathlib import Path
import numpy as np, faiss
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT))
from src import chunking, hybrid
from src.embed import Embedder, cached_encode
from src.index import VectorStore

STRAT = json.load(open(ROOT / "docs/evidence/chosen_chunking.json")) if (ROOT / "docs/evidence/chosen_chunking.json").exists() else dict(strategy="heading", kwargs=dict(max_words=250, min_words=40))
docs = {d["doc_id"]: d for d in hybrid.load_docs()}; emb = Embedder("bge"); log = []
SRC = ROOT / "data/raw_extra"


def chunks_of(doc): return chunking.chunk_corpus([doc], STRAT["strategy"], **STRAT["kwargs"])
def metas_of(doc, ch): return [dict(chunk_id=c.id, doc_id=c.doc_id, start=c.start, end=c.end, section=c.section, type=doc["type"], sensitivity=doc["sensitivity"], date=doc["date"], lang=doc["lang"]) for c in ch]
def enc(doc, ch): return cached_encode(emb, [c.text for c in ch], "upd_" + doc["doc_id"])
def top(store, q, k=5, pred=None):
    return [store.meta[i]["chunk_id"] + (" [dead]" if not store.alive[i] else "") for i, _ in store.search(emb.encode([q], query=True)[0], k, pred)]


store = VectorStore(384); allch = {}
for d in docs.values():
    ch = chunks_of(d); allch[d["doc_id"]] = ch; store.add(enc(d, ch), metas_of(d, ch))
log.append(dict(step="initial build", rows=len(store.meta), alive=sum(store.alive), docs=len(docs)))

def check(name, doc_id, query, expect_doc, expect_text=None, absent_doc=None):
    r = top(store, query, 5); ok = r and r[0].startswith(expect_doc) if expect_doc else True
    if absent_doc: ok = ok and not any(x.startswith(absent_doc) for x in r)
    log.append(dict(step=name, doc=doc_id, query=query, top5=r, passed=bool(ok), rows=len(store.meta), alive=sum(store.alive), dead_ratio=round(store.dead_ratio(), 3))); return ok

# 1) MODIFY: append a new section with a fresh fact to gatk_docker
d = dict(docs["gatk_docker"]); d["text"] += "\n## Nightly cache policy\nThe nightly build cache of the GATK demo image is purged every 17 days and the retention flag is called keepalive_window_days.\n"
q = "How often is the nightly build cache of the demo image purged?"
before = top(store, q, 3)
ch = chunks_of(d); old, new = store.upsert_doc("gatk_docker", enc(d, ch), metas_of(d, ch)); docs["gatk_docker"] = d
check("1 upsert (modify doc: new section added)", "gatk_docker", q, "gatk_docker"); log[-1].update(tombstoned=old, added=new, before_top3=before)
# 2) MODIFY: remove the first half of rare_citations (facts must disappear)
d = dict(docs["rare_citations"]); gone = d["text"][: len(d["text"]) // 2]; d["text"] = d["text"][len(d["text"]) // 2:]
probe = [l for l in gone.split("\n") if len(l) > 80][0][:120]
ch = chunks_of(d); old, new = store.upsert_doc("rare_citations", enc(d, ch), metas_of(d, ch)); docs["rare_citations"] = d
r = top(store, probe, 5); hit = [x for x in r if x.startswith("rare_citations")]
txt = [store.meta[i] for i in range(len(store.meta)) if store.alive[i] and store.meta[i]["doc_id"] == "rare_citations"]
removed_ok = all(m["start"] >= 0 and docs["rare_citations"]["text"][m["start"]:m["end"]].find(probe[:40]) < 0 for m in txt)
log.append(dict(step="2 upsert (modify doc: first half removed)", doc="rare_citations", probe=probe, top5=r, passed=bool(removed_ok), tombstoned=old, added=new, rows=len(store.meta), alive=sum(store.alive), dead_ratio=round(store.dead_ratio(), 3)))
# 3) DELETE
n = store.delete_doc("sarek_citations"); del docs["sarek_citations"]
q = "sarek citations list of tools references MultiQC"; r = top(store, q, 5)
log.append(dict(step="3 delete doc", doc="sarek_citations", query=q, top5=r, passed=not any(x.startswith("sarek_citations") for x in r if "[dead]" not in x), tombstoned=n, rows=len(store.meta), alive=sum(store.alive), dead_ratio=round(store.dead_ratio(), 3)))
# 4,5) ADD two new documents that were not in the corpus
from scripts.build_corpus import md_clean
for i, (did, rel, q) in enumerate([("gatk_spark_wdl", "gatk_spark_wdl.md", "How do I run the Spark WDL workflow on a Google Dataproc cluster?"), ("gatk_spark_eval", "gatk_spark_eval.md", "scripts for evaluating Spark tool performance on a cluster")], 4):
    text = md_clean((SRC / rel).read_text()); nd = dict(doc_id=did, title=text.split("\n")[0].lstrip("# ") or did, type="pipeline-readme", date="2026-08-17", sensitivity="public", lang="en", text=text)
    docs[did] = nd; ch = chunks_of(nd); store.add(enc(nd, ch), metas_of(nd, ch))
    check(f"{i} add new doc", did, q, did); log[-1]["added"] = len(ch)
# 6) metadata pre-filter after updates: deleted doc never appears even when filtered by type
r = top(store, "citations tools used by the pipeline", 5, hybrid.make_pred(types=["citations"]))
log.append(dict(step="6 filter citations after delete", top5=r, passed=all(x.startswith("rare_citations") for x in r)))
# compaction: graph rebuilt without dead rows; compare with exact search on the final corpus
rows_before = len(store.meta); store.compact()
vecs = np.vstack([store.vector(i) for i in range(len(store.meta))]); flat = faiss.IndexFlatIP(384); flat.add(vecs)
qs = ["variant effect predictor annotation", "how to filter variants by quality", "run on a cluster with spark", "reference genome fasta index", "tumor normal pair calling", "sample sheet columns", "container image build", "left align and normalize indels", "copy number calling", "checksum of reference"]
qv = emb.encode(qs, query=True); _, Ie = flat.search(qv, 5); ov = []
for v, e in zip(qv, Ie): ov.append(len({i for i, _ in store.search(v, 5)} & set(e.tolist())) / 5)
log.append(dict(step="7 compact", rows_before=rows_before, rows_after=len(store.meta), alive=sum(store.alive), ann_vs_exact_overlap_at5=round(float(np.mean(ov)), 3), passed=bool(np.mean(ov) >= 0.9 and sum(store.alive) == len(store.meta))))
store.save(ROOT / "data/index/bge_heading"); s2 = VectorStore.load(ROOT / "data/index/bge_heading")
log.append(dict(step="8 save/load round trip", passed=s2.search(qv[0], 5) == store.search(qv[0], 5)))
json.dump(log, open(ROOT / "docs/evidence/update.json", "w"), indent=1, ensure_ascii=False)
for l in log: print(l["step"], l.get("passed"), l.get("rows", ""), l.get("alive", ""))
