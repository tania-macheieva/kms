"""The five tools (R1 C1). Tools 1-4 are read-only; propose_fact (agent/propose_fact.py) is the only write path and is gated by validation + human approval.
Each tool returns {ok, obs:[{id, text}], error}; `obs` entries are the citable sources of the answer."""
from __future__ import annotations
import json, time, re
from .config import Policy, ROLE_RANK, LABEL_MIN_ROLE, ROOT
from . import guards

TOOL_SPECS = [
 dict(name="search_docs", description="Hybrid (BM25 + dense) search with reranking over the documentation corpus (GATK/Sarek/bcftools manuals, lab notes). Returns up to k text chunks with ids to cite. Read-only. Only chunks whose sensitivity is allowed for the caller's role are returned.",
      input_schema={"type": "object", "properties": {"query": {"type": "string", "minLength": 3, "maxLength": 300}, "k": {"type": "integer", "minimum": 1, "maximum": 5, "default": 4}}, "required": ["query"], "additionalProperties": False},
      constraints="read-only; k<=5; role filter on sensitivity; chunk text truncated to 700 chars"),
 dict(name="graph_query", description="Read-only Cypher over the knowledge graph (labels/relationships are listed in the schema). Single MATCH...RETURN statement, every node pattern must carry a label, LIMIT <= 50. Labels Person and Diagnosis need role clinician; Variant, Annotation, Sample need analyst.",
      input_schema={"type": "object", "properties": {"cypher": {"type": "string", "minLength": 8, "maxLength": 600}}, "required": ["cypher"], "additionalProperties": False},
      constraints="read-only (validator + ro_query); one statement; labelled nodes; <=50 rows; label access by role; timeout 2 s"),
 dict(name="sql_metric", description="Computes a governed metric from the DuckDB warehouse through the semantic layer (never free SQL). Optional grouping by dimensions and equality filters.",
      input_schema={"type": "object", "properties": {"metric": {"type": "string", "enum": ["call_count", "pass_rate", "avg_qual", "review_min_per_call", "pathogenic_share", "cpu_hours", "avg_daily_backlog"]},
                     "by": {"type": "array", "items": {"type": "string"}, "maxItems": 2}, "where": {"type": "object", "additionalProperties": {"type": ["string", "number", "array"]}}, "limit": {"type": "integer", "minimum": 1, "maximum": 50}},
                     "required": ["metric"], "additionalProperties": False},
      constraints="read-only DuckDB views; metric from the semantic layer (7); dimensions validated; <=2 group-by; <=50 rows"),
 dict(name="get_claims", description="Returns the register of alternative claims for a conflict (e.g. different QD/FS/SOR thresholds, Java version) with scope, source, status (active/alternative/superseded) and decision state. Use when sources disagree.",
      input_schema={"type": "object", "properties": {"conflict_id": {"type": "string", "pattern": "^CF-[A-Z]+$"}, "subject": {"type": "string", "maxLength": 80}}, "additionalProperties": False},
      constraints="read-only; no arguments = list of conflicts"),
 dict(name="propose_fact", description="Proposes a new fact/claim for the Hub. Does NOT write: the proposal is validated (SHACL + source), classified low/medium/high risk, and queued for human approval; only approved proposals with provenance are ever written.",
      input_schema={"type": "object", "properties": {"subject": {"type": "string", "maxLength": 80}, "predicate": {"type": "string", "enum": ["threshold_value", "alias", "note", "relation"]}, "value": {"type": ["string", "number"]}, "source": {"type": "string", "maxLength": 200}, "target": {"type": "string", "maxLength": 80}},
                     "required": ["subject", "predicate", "value", "source"], "additionalProperties": False},
      constraints="no direct write; human approval for risk >= medium; audit log; provenance mandatory"),
]
for s in TOOL_SPECS: s["pin"] = guards.desc_hash(s)
READ_ONLY = {"search_docs", "graph_query", "sql_metric", "get_claims"}

def _jsonable(v):
    if hasattr(v, "properties") and hasattr(v, "labels"): return {"_node": list(v.labels), **v.properties}
    if hasattr(v, "properties") and hasattr(v, "relation"): return {"_rel": v.relation, **v.properties}
    if isinstance(v, (list, tuple)): return [_jsonable(x) for x in v]
    return v

class Tools:
    def __init__(self, kb, pol: Policy, role: str, extra_tools: list | None = None, poison: list | None = None, propose=None):
        self.kb, self.pol, self.role = kb, pol, role; self.n = 0; self.exfil = []; self.poison = poison or []; self.extra = {t["name"]: t for t in (extra_tools or [])}; self.propose = propose
        self.denied = []
    # ---- registry (what the planner sees) ----
    def registry(self):
        specs = [dict(name=s["name"], description=s["description"], input_schema=s["input_schema"]) for s in TOOL_SPECS if s["name"] != "propose_fact"] + [dict(name=t["name"], description=t["description"], input_schema=t.get("input_schema", {"type": "object"})) for t in self.extra.values()]
        if self.pol.tool_pinning:
            pins = {s["name"]: s["pin"] for s in TOOL_SPECS}; specs, bad = guards.pin_check(specs, pins); self.denied += [dict(tool=n, reason=r) for n, r in bad]
        return specs
    def call(self, name: str, args: dict) -> dict:
        self.n += 1; args = args if isinstance(args, dict) else {}
        if self.pol.tool_pinning and name not in {s["name"] for s in TOOL_SPECS}: self.denied.append(dict(tool=name, reason="not_in_allowlist")); return dict(ok=False, obs=[], error=f"tool '{name}' is not allowed")
        if name in self.extra and not self.pol.tool_pinning: return self._extra(name, args)
        fn = getattr(self, "t_" + name, None)
        if fn is None: return dict(ok=False, obs=[], error=f"unknown tool '{name}'")
        try: return fn(**args)
        except TypeError as e: return dict(ok=False, obs=[], error=f"bad arguments: {e}")
        except Exception as e: return dict(ok=False, obs=[], error=f"{type(e).__name__}: {str(e)[:200]}")
    def _extra(self, name, args): self.exfil.append(dict(tool=name, args=args)); return dict(ok=True, obs=[dict(id=f"{name}#{self.n}", text="done")], error=None)
    def _role(self): return self.role if self.pol.role_scope else "clinician"
    # ---- tools ----
    def t_search_docs(self, query: str, k: int = 4):
        k = max(1, min(int(k), 5)); hits = self.kb.search(query, self._role(), k); obs = [dict(id=h["id"], text=h["text"][: self.pol.max_chars_obs]) for h in hits]
        for p in self.poison:                                    # a poisoned document that the index would return (indirect injection scenario)
            if p.get("via", "search_docs") == "search_docs" and (p.get("when") is None or re.search(p["when"], query, re.I)): obs.insert(0, dict(id=p["id"], text=p["text"]))
        return dict(ok=True, obs=obs, error=None)
    def t_graph_query(self, cypher: str):
        if self.pol.ro_validator:
            ok, q, why = guards.validate_cypher(cypher, self._role() if self.pol.role_scope else "clinician", self.pol.max_rows)
            if not ok: self.denied.append(dict(tool="graph_query", reason=why)); return dict(ok=False, obs=[], error=f"query rejected: {why}")
            rs = self.kb.graph.ro_query(q, timeout=2000)
        else:
            q = cypher; rs = self.kb.graph.query(q)              # naive: any statement, writes allowed (scratch graph)
        rows = [[_jsonable(c) for c in r] for r in rs.result_set[: self.pol.max_rows]]
        head = [h[1] if isinstance(h, (list, tuple)) else h for h in rs.header]; txt = json.dumps(dict(columns=head, rows=rows, rows_returned=len(rows), write_stats=dict(nodes_deleted=getattr(rs, "nodes_deleted", 0), nodes_created=getattr(rs, "nodes_created", 0), properties_set=getattr(rs, "properties_set", 0))), ensure_ascii=False, default=str)
        obs = [dict(id=f"graph#{self.n}", text=txt[: 1500])]
        for p in self.poison:
            if p.get("via") == "graph_query": obs.append(dict(id=p["id"], text=p["text"]))
        return dict(ok=True, obs=obs, error=None)
    def t_sql_metric(self, metric: str, by=(), where=None, limit=None):
        from hub.semantic import sl
        if len(by or []) > 2: return dict(ok=False, obs=[], error="at most 2 group-by dimensions")
        df = sl.run(self.kb.con, metric, by=list(by or []), where=where, limit=min(int(limit or 50), self.pol.max_rows))
        txt = f"metric={metric}; by={list(by or [])}; where={where}\n" + df.round(4).to_csv(index=False)
        return dict(ok=True, obs=[dict(id=f"sql#{self.n}", text=txt[:1500])], error=None)
    def t_get_claims(self, conflict_id: str | None = None, subject: str | None = None):
        cl = self.kb.claims()
        if conflict_id: cl = [c for c in cl if c["conflict_id"] == conflict_id]
        elif subject: cl = [c for c in cl if subject.lower() in c["subject"].lower()]
        if not conflict_id and not subject: return dict(ok=True, obs=[dict(id=f"claims#{self.n}", text="conflicts: " + "; ".join(sorted({f"{c['conflict_id']} ({c['subject']})" for c in cl})))], error=None)
        obs = [dict(id=c["claim_id"], text=f"{c['subject']}: {c.get('op', '')}{c['value']} [{c['status']}] scope={c['scope']}; source={c['source']}; valid {c['validFrom']}..{c.get('validTo') or 'open'}; decision {c['decision_status']}") for c in cl[:12]]
        return dict(ok=True, obs=obs, error=None)
    def t_propose_fact(self, **kw):
        if self.propose is None: return dict(ok=False, obs=[], error="propose_fact is not enabled in this session")
        r = self.propose(self.role, **kw); return dict(ok=True, obs=[dict(id=f"proposal#{self.n}", text=json.dumps(r, ensure_ascii=False, default=str))], error=None)
