"""R5: re-run the 34 lab-11 tests (config A: hybrid + reranker + graph) on the cleaned store.
  python scripts/run_rag_after.py record   -> llm_log/in/gen_after.json  (prompts missing from the replay cache)
  python scripts/run_rag_after.py run      -> eval/results_before.json (plain lab-11 RAG, re-run now for fair latency) and eval/results_after.json (CleanRAG)
The lab-11 code is imported from $LAB11_REPO (default ../lab11_repo); its models/graph must be installed (see README)."""
import os, sys, json, copy, dataclasses, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent; L11 = pathlib.Path(os.environ.get("LAB11_REPO", ROOT.parent / "lab11_repo")).resolve()
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(L11))
os.chdir(L11)    # lab-11 modules resolve their data paths relative to their own repo
from src.rag import RAG, Config
from src.graph_context import GraphContextBuilder
from src.llm import ReplayLLM, key_of
from src import evalrag as E
from quality.common import read_jsonl
CACHE = ROOT / "llm_cache"
class CleanRAG(RAG):
    """RAG over the improved store: absorbed duplicate chunks are never returned (the canonical chunk carries them); the store is over-fetched by 10 to keep k."""
    def __init__(self, *a, absorbed=(), **kw): super().__init__(*a, **kw); self.absorbed = set(absorbed)
    def retrieve(self, question, role, cfg):
        hits, ms = super().retrieve(question, role, dataclasses.replace(cfg, k=cfg.k + 10)) if self.absorbed else super().retrieve(question, role, cfg)
        if self.absorbed: hits = [h for h in hits if self.ret.chunks[h[0]].id not in self.absorbed][:cfg.k]
        return hits, ms
def register_chunks():
    """Claim-register notes (from store_clean/alternatives.jsonl) given to the model for the conflict tests, as ordinary sources `alt_<conflict>`."""
    cl = read_jsonl(ROOT / "store_clean/alternatives.jsonl"); by = {}
    for c in cl: by.setdefault(c["conflict_id"], []).append(c)
    out = {}
    for cid, cs in by.items():
        lines = [f"CLAIM REGISTER {cid} — {cs[0]['subject']} (decision proposed {cs[0]['decided_at']}, status: {cs[0]['decision_status']})"]
        for c in cs: lines.append(f"- [{c['status']}] value {c.get('op', '')} {c['value']}; scope: {c['scope']}; source: {c['source']}; valid {c['validFrom']}..{c.get('validTo') or 'open'}")
        out[cid] = dict(id=f"alt_{cid}", type="claim-register", text="\n".join(lines))
    return out
TEST_REG = {"T27": "CF-QD", "T28": "CF-FS", "T29": "CF-SOR", "T30": "CF-JAVA"}
def clean_inputs():
    cl = read_jsonl(ROOT / "store_clean/corpus.jsonl"); absorbed = {m["chunk_id"]: c["chunk_id"] for c in cl for m in c.get("merged_from", [])}; return absorbed
def run_set(rag, tests, fx, reg=None, merged=None):
    cfg = Config(name="A", rerank=True); res = []
    for rep in range(2):    # pass 0 cold, pass 1 warm (latency from the warm pass, as in lab 11)
        out = []
        for t in tests:
            extra = [fx[i] for i in t.get("fixtures", [])] + ([reg[TEST_REG[t["id"]]]] if reg and t["id"] in TEST_REG else [])
            r = rag.ask(t["question"], t["role"], cfg, qid=t["id"], extra_chunks=extra)
            if merged:       # a canonical chunk also carries the spans of the chunks it absorbed -> count them for context recall
                for s in list(r.sources):
                    for a, c in merged.items():
                        if c == s["id"]: r.sources.append(dict(s, id=a))
            m = E.auto_metrics(t, r, rag); m.update(answer=r.answer, cited=r.cited, invalid=r.invalid_citations, context_ids=r.context_ids, question=t["question"], prompt_user=r.prompt_user, latency=r.latency)
            if t.get("gold_facts"): m["facts_hit"], m["facts_total"] = E.fact_hits(r.answer, t)
            out.append(m)
        res = out
    return res
def main(mode):
    fx = E.fixtures(); tests = E.load_tests(); absorbed = clean_inputs(); reg = register_chunks()
    if mode == "record":
        rec = E.Recorder(ReplayLLM(E.GEN_MODEL, cache_dir=CACHE)); rag = CleanRAG(rec, graph=GraphContextBuilder(), log=False, absorbed=absorbed)
        run_set(rag, tests, fx, reg, absorbed); uniq = {}
        for t in rec.todo: uniq[key_of(E.GEN_MODEL, t["system"], t["user"])] = t
        items = [dict(id=f"after-{i:03d}", key=k, user=v["user"]) for i, (k, v) in enumerate(uniq.items(), 1)]
        json.dump(dict(system=next(iter(uniq.values()))["system"] if uniq else "", items=items), open(ROOT / "llm_log/in/gen_after.json", "w"), ensure_ascii=False, indent=1)
        print("prompts to generate:", len(items), "of", len(tests)); return
    llm = ReplayLLM(E.GEN_MODEL, cache_dir=CACHE)
    before = run_set(RAG(llm, graph=GraphContextBuilder(), log=False), tests, fx)
    after = run_set(CleanRAG(llm, graph=GraphContextBuilder(), log=False, absorbed=absorbed), tests, fx, reg, absorbed)
    for name, res in (("before", before), ("after", after)): json.dump(res, open(ROOT / f"eval/results_{name}.json", "w"), ensure_ascii=False, indent=1)
    ch = [t["id"] for t, b, a in zip(tests, before, after) if b["answer"] != a["answer"] or b["context_ids"] != a["context_ids"]]
    print("status_ok before/after", sum(m["status_ok"] for m in before), sum(m["status_ok"] for m in after), "| tests with changed context or answer:", ch)
if __name__ == "__main__": main(sys.argv[1])
