"""Run the 34 tests through the pipeline with the replayed LLM answers; automatic metrics -> eval/results_<cfg>.json"""
import json, sys, statistics as st
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT))
from src.rag import RAG, Config
from src.graph_context import GraphContextBuilder
from src.llm import ReplayLLM
from src import evalrag as E

def main(which):
    cfg = Config(name=which, rerank=(which == "A"))
    rag = RAG(ReplayLLM(E.GEN_MODEL), graph=GraphContextBuilder(), log=False); fx = E.fixtures(); tests = E.load_tests(); res = []
    for t in tests:   # first call warms caches (token vectors for the reranker are cached per chunk)
        pass
    for rep in range(2):  # 2 passes: pass 0 = cold, pass 1 = warm; latency statistics use the warm pass
        res_pass = []
        for t, r in E.run_tests(rag, tests, cfg, fx):
            m = E.auto_metrics(t, r, rag); m.update(answer=r.answer, cited=r.cited, invalid=r.invalid_citations, guard=r.guard, context_ids=r.context_ids, question=t["question"], prompt_user=r.prompt_user, latency=r.latency)
            if t.get("gold_facts"): m["facts_hit"], m["facts_total"] = E.fact_hits(r.answer, t)
            res_pass.append(m)
        res = res_pass
        if rep == 0: cold = [x["latency"]["retrieve_ms"] for x in res_pass]
    for m, c in zip(res, cold): m["retrieve_ms_cold"] = c
    json.dump(res, open(ROOT / f"eval/results_{which}.json", "w"), ensure_ascii=False, indent=1)
    print(which, len(res), "status_ok", sum(m["status_ok"] for m in res), "invalid cites", sum(m["n_invalid"] for m in res), "uncited", sum(m["uncited"] for m in res))
    for m in res:
        if not m["status_ok"] or m["n_invalid"] or m.get("injection_resisted") is False: print(" !", m["id"], m["category"], m["status"], "exp", m["expected"], "inv", m["invalid"], "resisted", m.get("injection_resisted"))

if __name__ == "__main__": main(sys.argv[1])
