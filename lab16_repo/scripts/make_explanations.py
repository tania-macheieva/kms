"""python scripts/make_explanations.py todo   -> eval/explain_todo.json (prompts missing from the replay cache)
   python scripts/make_explanations.py final  -> eval/explanations.json (+ share of explanations consistent with the path, negative controls)"""
import sys, json, pathlib, collections
ROOT = pathlib.Path(__file__).resolve().parent.parent; sys.path.insert(0, str(ROOT))
from reco.eval import World, split, CUTOFF, DAYS
from reco.models import Popularity, GraphReco, KNNReco, Hybrid, recommend
from reco.explain import explain, verify_path, tamper_test, check, template
from reco.llm import ReplayLLM
def run(phase, n_users=20, k=5):
    W = World(0); cfg = json.load(open(ROOT / "reco/config.json")); items = W.items
    us, hist, roles, seen, pos = split(W.rows, items, CUTOFF, DAYS); pop = Popularity(items, [r for r in W.rows if r[3] < CUTOFF]); G = GraphReco(W.G, items, **cfg["graph"]); K = KNNReco(W.E, items, **cfg["knn"]); H = Hybrid(dict(graph=G, knn=K, popularity=pop), cfg["hyb_w"], "weighted")
    llm = ReplayLLM(); out = []
    for u in us[:n_users]:
        for c in recommend(H, items, roles[u], hist[u], CUTOFF, seen[u], k=k):
            p = G.explain_path(c, hist[u], CUTOFF); src = "graph"
            if p is None: p = K.explain_path(c, hist[u], CUTOFF); src = "embedding"
            e = explain(items, c, p, llm); e.update(user=u, role=roles[u], path_source=src, path_exists=verify_path(W.G, W.E, items, e["facts"]), hit=c in pos[u]); out.append(e)
    if phase == "todo":
        json.dump(llm.todo, open(ROOT / "eval/explain_todo.json", "w"), ensure_ascii=False); print(len(llm.todo), "prompts missing"); return
    n = len(out); share_t = sum(e["template_ok"] and e["path_exists"] for e in out) / n; para = [e for e in out if e["paraphrase"] is not None]
    summ = dict(n=n, path_source=dict(collections.Counter(e["path_source"] for e in out)), kinds=dict(collections.Counter(e["facts"]["kind"] for e in out)), template_consistent=sum(e["template_ok"] for e in out), path_exists=sum(e["path_exists"] for e in out), share_template_ok_and_path_exists=share_t,
                paraphrased=len(para), paraphrase_accepted=sum(e["paraphrase_ok"] for e in para), share_paraphrase_ok=(sum(e["paraphrase_ok"] for e in para) / len(para)) if para else None, final_used=dict(collections.Counter(e["used"] for e in out)),
                rejected_examples=[dict(text=e["paraphrase"], why=e["why"]) for e in para if not e["paraphrase_ok"]][:8], negative_controls=tamper_test([e["facts"] for e in out]))
    for e in out: e["facts"] = {k: v for k, v in e["facts"].items()}
    json.dump(dict(summary=summ, items=out), open(ROOT / "eval/explanations.json", "w"), ensure_ascii=False, indent=1); print(json.dumps(summ, ensure_ascii=False, indent=1)[:2500])
if __name__ == "__main__": run(sys.argv[1])
