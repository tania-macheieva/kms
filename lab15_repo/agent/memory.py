"""Memory (R1 C4): short-term (state of one run), episodic (what was asked / which tools, TTL 30 d), semantic (approved facts with provenance, review after 180 d).
Storage rules: no restricted values (person names, diagnosis ids), no secrets; entries carry ts+ttl and expired entries are never returned."""
from __future__ import annotations
import json, time, pathlib, re, hashlib
from .config import ROOT
EPISODIC_TTL_D, SEMANTIC_REVIEW_D = 30, 180
class Memory:
    def __init__(self, restricted_values=None, path=None, now=time.time):
        self.dir = pathlib.Path(path or ROOT / "logs" / "memory"); self.restricted = restricted_values or {}; self.now = now; self.short = {}
    def _file(self, kind): self.dir.mkdir(parents=True, exist_ok=True); return self.dir / f"{kind}.jsonl"
    def _clean(self, text): return not any(re.search(r"\b" + re.escape(v) + r"\b", text) for v in self.restricted) and not re.search(r"sk-[A-Za-z0-9_\-]{16,}|api[_ -]?key", text, re.I)
    def remember_episode(self, role, question, tools, status):
        if not self._clean(question): return False                      # rule: restricted values / secrets are never stored
        rec = dict(ts=self.now(), ttl_days=EPISODIC_TTL_D, role=role, q_hash=hashlib.sha1(question.encode()).hexdigest()[:10], question=question[:200], tools=tools, status=status)
        open(self._file("episodic"), "a", encoding="utf-8").write(json.dumps(rec, ensure_ascii=False) + "\n"); return True
    def episodes(self, role=None):
        f = self._file("episodic"); out = []
        for l in f.read_text(encoding="utf-8").splitlines() if f.exists() else []:
            r = json.loads(l)
            if self.now() - r["ts"] <= r["ttl_days"] * 86400 and (role is None or r["role"] == role): out.append(r)
        return out
    def purge(self):
        """physically deletes expired episodic entries (run daily); returns the number removed"""
        f = self._file("episodic")
        if not f.exists(): return 0
        rows = [json.loads(l) for l in f.read_text(encoding="utf-8").splitlines()]; keep = [r for r in rows if self.now() - r["ts"] <= r["ttl_days"] * 86400]
        f.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in keep), encoding="utf-8"); return len(rows) - len(keep)
    def hint(self, role, question):
        """short, role-scoped hint for the planner: the tools used for the most recent similar (same first 3 words) question. Never contains answers."""
        key = " ".join(question.lower().split()[:3])
        for r in reversed(self.episodes(role)):
            if " ".join(r["question"].lower().split()[:3]) == key and r["status"] != "PENDING": return f"previously for a similar question the tools {r['tools']} were used"
        return "none"
