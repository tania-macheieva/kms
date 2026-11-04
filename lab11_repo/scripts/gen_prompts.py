"""Offline generation protocol, step 1: run the pipeline with a recorder LLM and write the prompts that are NOT yet in data/llm_cache/ to llm_log/in/gen_<set>.json.
sets: A (34 tests, reranker on) | B (34 tests, reranker off) | R2 (graph questions: text-only + graph mode)."""
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT))
from src.rag import RAG, Config
from src.graph_context import GraphContextBuilder
from src.llm import ReplayLLM, key_of
from src import evalrag as E

def todo_for(rag, rec, jobs):
    for question, role, cfg, qid, extra in jobs: rag.ask(question, role, cfg, qid=qid, extra_chunks=extra)
    uniq = {}
    for t in rec.todo: uniq[key_of(E.GEN_MODEL, t["system"], t["user"])] = t
    return uniq

def main(which):
    rec = E.Recorder(ReplayLLM(E.GEN_MODEL)); rag = RAG(rec, graph=GraphContextBuilder(), log=False); fx = E.fixtures(); tests = E.load_tests(); jobs = []
    if which in ("A", "B"):
        cfg = Config(name=which, rerank=(which == "A"))
        jobs = [(t["question"], t["role"], cfg, t["id"], [fx[i] for i in t.get("fixtures", [])]) for t in tests]
    elif which == "R2":
        jobs = [(g["question"], g["role"], Config(name="R2-text", use_graph=False), g["id"] + "-text", []) for g in E.load_gq()]
        jobs += [(g["question"], g["role"], Config(name="R2-graph", use_graph=True), g["id"] + "-graph", []) for g in E.load_gq()]
    uniq = todo_for(rag, rec, jobs)
    items = [dict(id=f"{which}-{i:03d}", key=k, user=v["user"]) for i, (k, v) in enumerate(uniq.items(), 1)]
    system = next(iter(uniq.values()))["system"] if uniq else ""
    out = ROOT / f"llm_log/in/gen_{which}.json"; json.dump(dict(system=system, items=items), open(out, "w"), ensure_ascii=False, indent=1)
    print(which, "prompts to generate:", len(items), "of", len(jobs), "jobs ->", out.name)

if __name__ == "__main__": main(sys.argv[1])
