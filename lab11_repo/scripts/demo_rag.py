"""R1 demo: 7 queries through the full pipeline (replayed generator answers), logged to logs/rag_log.jsonl."""
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT))
from src.rag import RAG, Config, LOG_FILE
from src.graph_context import GraphContextBuilder
from src.llm import ReplayLLM
from src import evalrag as E
LOG_FILE.unlink(missing_ok=True)
rag = RAG(ReplayLLM(E.GEN_MODEL), graph=GraphContextBuilder(), log=True); fx = E.fixtures(); T = {t["id"]: t for t in E.load_tests()}
for tid in ["T01", "T11", "T19", "T25", "T27", "T32", "T33"]:
    t = T[tid]; r = rag.ask(t["question"], t["role"], Config(name="A"), qid="demo-" + tid, extra_chunks=[fx[i] for i in t.get("fixtures", [])])
    print(f"\n[{tid}] role={t['role']} Q: {t['question']}\n  STATUS={r.status} cited={r.cited} invalid={r.invalid_citations} guard={r.guard!r} tokens={r.in_tokens}/{r.out_tokens} retrieve={r.latency['retrieve_ms']:.0f}ms graph={r.latency.get('graph_ms',0):.1f}ms\n  A: {r.answer[:260]}")
print("\nlog lines:", sum(1 for _ in open(LOG_FILE)))
