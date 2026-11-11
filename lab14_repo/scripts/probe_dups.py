"""Retrieval-only probe: one query per duplicate cluster (first ~18 words of the canonical chunk body, deterministic, no LLM), top-5 before vs after.
Redundant slots = top-5 slots minus distinct duplicate-clusters/chunks (a slot is redundant if another chunk of the same cluster is already in the top 5)."""
import os, sys, json, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent; L11 = pathlib.Path(os.environ.get("LAB11_REPO", ROOT.parent / "lab11_repo")).resolve(); sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(L11)); os.chdir(L11)
from src.rag import RAG, Config
from src.graph_context import GraphContextBuilder
from src.llm import ReplayLLM
from src import evalrag as E
from quality.common import read_jsonl
sys.path.insert(0, str(ROOT / "scripts")); import run_rag_after as R
from quality import dedup as D
log = read_jsonl(ROOT / "quality/merge_log.jsonl"); absorbed = {a: g["canonical"] for g in log for a in g["absorbed"]}; cluster_of = {}
for i, g in enumerate(log):
    for x in [g["canonical"]] + g["absorbed"]: cluster_of[x] = i
by = {c["chunk_id"]: c for c in read_jsonl(ROOT / "store/corpus.jsonl")}
queries = []
for g in log:
    body = D.normalise(by[g["canonical"]]["text"]).split(); queries.append((g["canonical"], " ".join(body[:18])))
llm = ReplayLLM(E.GEN_MODEL, cache_dir=ROOT / "llm_cache"); before = RAG(llm, graph=GraphContextBuilder(), log=False); after = R.CleanRAG(llm, graph=GraphContextBuilder(), log=False, absorbed=absorbed); cfg = Config(name="A", rerank=True)
def top5(rag, q): hits, _ = rag.retrieve(q, "reader", cfg); return [rag.ret.chunks[h[0]].id for h in hits[:5]]
def stats(ids):
    cl = [cluster_of.get(i, i) for i in ids]; return dict(slots=len(ids), distinct=len(set(cl)), redundant=len(ids) - len(set(cl)))
out = []; tb = ta = 0
for cid, q in queries:
    b, a = top5(before, q), top5(after, q); sb, sa = stats(b), stats(a); tb += sb["redundant"]; ta += sa["redundant"]
    out.append(dict(cluster=cid, query=q, before=b, after=a, redundant_before=sb["redundant"], redundant_after=sa["redundant"], target_in_top5_before=cid in b or any(absorbed.get(x) == cid or cluster_of.get(x) == cluster_of[cid] for x in b), target_in_top5_after=any(cluster_of.get(x) == cluster_of[cid] for x in a)))
res = dict(queries=len(out), redundant_slots_before=tb, redundant_slots_after=ta, total_slots=5 * len(out), distinct_before=sum(len({cluster_of.get(i, i) for i in o["before"]}) for o in out), distinct_after=sum(len({cluster_of.get(i, i) for i in o["after"]}) for o in out),
           cluster_found_before=sum(o["target_in_top5_before"] for o in out), cluster_found_after=sum(o["target_in_top5_after"] for o in out), detail=out)
json.dump(res, open(ROOT / "eval/probe_dups.json", "w"), indent=1); print({k: v for k, v in res.items() if k != "detail"})
