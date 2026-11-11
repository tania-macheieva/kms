"""Trace log: one JSON line per query with every node/tool event (R2 C4). No API keys or restricted payloads: tool results are stored as ids + length + first 160 chars."""
from __future__ import annotations
import json, time, datetime as dt, pathlib
from .config import ROOT
class Trace:
    def __init__(self, qid, question, role, policy, path=None):
        self.rec = dict(qid=qid, ts=dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"), role=role, policy=policy, question=question, events=[]); self.t0 = time.perf_counter(); self.path = pathlib.Path(path) if path else None
    def ev(self, node, **kw): self.rec["events"].append(dict(node=node, t_ms=round((time.perf_counter() - self.t0) * 1000, 1), **kw))
    def close(self, **final):
        self.rec["final"] = final; self.rec["total_ms"] = round((time.perf_counter() - self.t0) * 1000, 1)
        if self.path: self.path.parent.mkdir(exist_ok=True); open(self.path, "a", encoding="utf-8").write(json.dumps(self.rec, ensure_ascii=False, default=str) + "\n")
        return self.rec
