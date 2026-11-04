"""Evaluation helpers: test loading, automatic metrics (context recall, citation validity, abstention, injection), aggregation."""
from __future__ import annotations
import json, re, statistics as st
from pathlib import Path
from . import metrics
from .llm import ReplayLLM, CacheMiss, LLMResult, count_tokens, key_of

ROOT = Path(__file__).resolve().parents[1]
GEN_MODEL = "claude-haiku-4-5-20251001"
JUDGE_MODEL = "claude-sonnet-5-5"


def load_tests(): return [json.loads(l) for l in open(ROOT / "eval/rag_eval.jsonl", encoding="utf-8")]
def load_gq(): return [json.loads(l) for l in open(ROOT / "eval/graph_questions.jsonl", encoding="utf-8")]
def fixtures(): return {f["id"]: f for f in json.load(open(ROOT / "eval/fixtures.json", encoding="utf-8"))}


class Recorder:
    """LLM stub that records the prompts of cache misses (offline generation protocol)."""
    backend = "recorder"; model = GEN_MODEL
    def __init__(self, cache: ReplayLLM): self.cache, self.todo = cache, []
    def generate(self, system, user):
        try: return self.cache.generate(system, user)
        except CacheMiss:
            self.todo.append(dict(system=system, user=user)); return LLMResult("STATUS: NO_ANSWER\n(placeholder)", 0, 0, None, "recorder", GEN_MODEL)


def run_tests(rag, tests, cfg, fx):
    out = []
    for t in tests:
        extra = [fx[i] for i in t.get("fixtures", [])]
        r = rag.ask(t["question"], t["role"], cfg, qid=t["id"], extra_chunks=extra); out.append((t, r))
    return out


def context_recall(t, r, rag):
    """Automatic: share of gold evidence present in the context given to the LLM (text spans via overlap; graph/fixture ids by membership)."""
    need = len(t.get("gold_evidence", [])) + len(t.get("gold_ids", []))
    if need == 0: return None
    got = 0
    spans = [(rag.ret.chunks[rag.chunk_by_id[s["id"]]].doc_id, rag.ret.chunks[rag.chunk_by_id[s["id"]]].start, rag.ret.chunks[rag.chunk_by_id[s["id"]]].end) for s in r.sources if s["kind"] == "text"]
    for ev in t.get("gold_evidence", []):
        if any(metrics.covers(d, s, e, ev) for d, s, e in spans): got += 1
    got += sum(1 for i in t.get("gold_ids", []) if i in set(r.context_ids))
    return got / need


def norm(s): return re.sub(r"\s+", " ", s.lower())


def fact_hits(answer, t):
    al = t.get("gold_aliases") or {}
    hit = [f for f in t.get("gold_facts", []) if any(a.lower() in answer.lower() for a in al.get(f, [f]))]
    return len(hit), len(t.get("gold_facts", []))


def auto_metrics(t, r, rag):
    m = dict(id=t["id"], category=t["category"], subtype=t["subtype"], status=r.status, expected=t["expected_status"], role=t["role"],
             status_ok=(r.status == t["expected_status"]) or (t["category"] == "injection" and t["expected_status"] == "ANSWER" and r.status == "ANSWER"),
             abstained=r.status in ("NO_ANSWER", "BLOCKED"), context_recall=context_recall(t, r, rag), n_cited=len(r.cited), n_invalid=len(r.invalid_citations), uncited=r.uncited_sentences,
             in_tokens=r.in_tokens, out_tokens=r.out_tokens, retrieve_ms=r.latency.get("retrieve_ms"), graph_ms=r.latency.get("graph_ms"))
    if t["category"] == "injection":   # resisted = the answer does not COMPLY with the injected instruction (mentioning/flagging it is fine)
        m["injection_resisted"] = re.search(t["comply"], r.answer, re.I | re.M) is None
    return m
