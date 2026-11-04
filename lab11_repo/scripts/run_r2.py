"""R2: 12 relational questions, 'text only' (use_graph=False) vs 'text + sub-graph' -> eval/results_R2.json + docs table fragment."""
import json, sys, statistics as st
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT))
from src.rag import RAG, Config
from src.graph_context import GraphContextBuilder
from src.llm import ReplayLLM
from src import evalrag as E

rag = RAG(ReplayLLM(E.GEN_MODEL), graph=GraphContextBuilder(), log=False); rows = []
for g in E.load_gq():
    row = dict(id=g["id"], question=g["question"])
    for mode, use in (("text", False), ("graph", True)):
        r = rag.ask(g["question"], g["role"], Config(name="R2-" + mode, use_graph=use), qid=g["id"] + "-" + mode)
        h, n = E.fact_hits(r.answer, g)
        gid = set(g.get("gold_node_ids", [])); cited_gold = len(gid & set(r.cited)); in_ctx = len(gid & set(r.context_ids))
        row[mode] = dict(status=r.status, facts_hit=h, facts_total=n, correct=(h == n), in_tokens=r.in_tokens, out_tokens=r.out_tokens, gold_nodes=len(gid), gold_nodes_in_context=in_ctx, gold_nodes_cited=cited_gold, cited=r.cited, answer=r.answer,
                         graph_ms=r.latency.get("graph_ms"), n_nodes=(r.graph or {}).get("n_nodes") if isinstance(r.graph, dict) else None)
    rows.append(row)
json.dump(rows, open(ROOT / "eval/results_R2.json", "w"), ensure_ascii=False, indent=1)
S = {}
for m in ("text", "graph"):
    S[m] = dict(correct=sum(r[m]["correct"] for r in rows), facts=sum(r[m]["facts_hit"] for r in rows), facts_total=sum(r[m]["facts_total"] for r in rows),
                in_tokens=st.mean(r[m]["in_tokens"] for r in rows), out_tokens=st.mean(r[m]["out_tokens"] for r in rows),
                abstain=sum(r[m]["status"] == "NO_ANSWER" for r in rows), gold_cited=sum(r[m]["gold_nodes_cited"] for r in rows), gold_nodes=sum(r[m]["gold_nodes"] for r in rows),
                gold_ctx=sum(r[m]["gold_nodes_in_context"] for r in rows))
json.dump(S, open(ROOT / "eval/summary_R2.json", "w"), indent=1); print(json.dumps(S, indent=1))
for r in rows: print(r["id"], "text", r["text"]["status"], r["text"]["facts_hit"], "/", r["text"]["facts_total"], r["text"]["in_tokens"], "| graph", r["graph"]["status"], r["graph"]["facts_hit"], "/", r["graph"]["facts_total"], r["graph"]["in_tokens"], "gold cited", r["graph"]["gold_nodes_cited"], "/", r["graph"]["gold_nodes"], "ctx", r["graph"]["gold_nodes_in_context"])
