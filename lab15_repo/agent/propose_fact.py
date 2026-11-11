"""R5: the only write-like path of the agent. A proposal is (1) validated (schema, subject exists, source verifiable, SHACL), (2) risk-classified low|medium|high,
(3) low -> staging (never the Hub), medium -> waits for a human decision, high -> rejected. Only a human decision (approver != agent) writes an approved fact, with provenance.
Every step is appended to a hash-chained audit log. State: proposals/{queue,audit,staging,approved_facts}.jsonl (override dir with env DKH_PROPOSALS)."""
from __future__ import annotations
import json, os, re, time, uuid, hashlib, pathlib, datetime as dt
from .config import ROOT
HUB = ROOT / "hub"
PROPOSERS = {"analyst", "clinician"}                       # reader cannot propose
APPROVERS = {"owner:student"}                              # the human Hub owner; the agent can never approve (see decide)
SAFETY_ANNOTATIONS = {"QD", "FS", "SOR", "MQ", "MQRankSum", "ReadPosRankSum"}
PLAUSIBLE = {"QD": (0.1, 50), "FS": (1, 400), "SOR": (0.5, 20), "MQ": (1, 80), "MQRankSum": (-30, 0), "ReadPosRankSum": (-30, 0)}
URL_ALLOW = re.compile(r"^https://(github\.com|gatk\.broadinstitute\.org|nf-co\.re|www\.htslib\.org|samtools\.github\.io|doi\.org|pubmed\.ncbi\.nlm\.nih\.gov)/")
INJ = re.compile(r"ignore (all )?previous|system notice|reveal|api[ _-]?key|curl |wget |DELETE|DROP", re.I)
def _dir() -> pathlib.Path: d = pathlib.Path(os.environ.get("DKH_PROPOSALS", ROOT / "proposals")); d.mkdir(parents=True, exist_ok=True); return d
def _now() -> float: return time.time()
def _iso(t=None) -> str: return dt.datetime.fromtimestamp(t or _now(), dt.timezone.utc).isoformat(timespec="seconds")
def _read(name): f = _dir() / f"{name}.jsonl"; return [json.loads(l) for l in f.read_text(encoding="utf-8").splitlines() if l.strip()] if f.exists() else []
def _append(name, rec): open(_dir() / f"{name}.jsonl", "a", encoding="utf-8").write(json.dumps(rec, ensure_ascii=False, default=str) + "\n")
def _rewrite(name, rows): (_dir() / f"{name}.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False, default=str) + "\n" for r in rows), encoding="utf-8")
# ---- audit log: append-only, hash-chained ----
def audit(event, pid, **kw):
    rows = _read("audit"); prev = rows[-1]["hash"] if rows else "0" * 16; rec = dict(ts=_now(), iso=_iso(), event=event, proposal=pid, **kw, prev=prev)
    rec["hash"] = hashlib.sha256((prev + json.dumps({k: v for k, v in rec.items() if k != "hash"}, sort_keys=True, default=str)).encode()).hexdigest()[:16]; _append("audit", rec); return rec
def verify_audit():
    prev = "0" * 16
    for r in _read("audit"):
        h = hashlib.sha256((r["prev"] + json.dumps({k: v for k, v in r.items() if k != "hash"}, sort_keys=True, default=str)).encode()).hexdigest()[:16]
        if r["prev"] != prev or r["hash"] != h: return False
        prev = r["hash"]
    return True
# ---- knowledge for validation ----
_CACHE = {}
def _known():
    if not _CACHE:
        import csv
        th = {r["id"]: r for r in csv.DictReader(open(HUB / "graph/nodes_Threshold.csv", encoding="utf-8"))}
        ent = {r["symbol"] for r in csv.DictReader(open(HUB / "graph/nodes_Gene.csv", encoding="utf-8"))} | {r["id"] for r in csv.DictReader(open(HUB / "graph/nodes_Procedure.csv", encoding="utf-8"))} | {r["name"] for r in csv.DictReader(open(HUB / "graph/nodes_GenePanel.csv", encoding="utf-8"))}
        restricted = {r[list(r)[0]] for lab in ("Person", "Diagnosis") for r in csv.DictReader(open(HUB / f"graph/nodes_{lab}.csv", encoding="utf-8"))}
        l11 = pathlib.Path(os.environ.get("LAB11_REPO", ROOT.parent / "lab11_repo")); chunks = set()
        f = l11 / "data/corpus.jsonl"
        if f.exists():
            for l in open(f, encoding="utf-8"): j = json.loads(l); chunks |= {j["chunk_id"], j["doc_id"]}
        _CACHE.update(thr=th, ent=ent, restricted=restricted, chunks=chunks)
    return _CACHE
def source_check(src: str):
    k = _known()
    if src in k["chunks"]: return "corpus", True
    if URL_ALLOW.match(src): return "url_allowlisted", True
    if src.startswith("local:") and len(src) > 8: return "local_self_reported", False
    return "unverifiable", False
def shacl_validate(p: dict):
    """candidate claim (+ candidate Threshold for threshold_value) as RDF -> pyshacl against hub/shapes.ttl; returns (conforms, messages)"""
    from rdflib import Graph, Literal, Namespace, RDF, XSD; from pyshacl import validate
    D = Namespace("http://dkh.example/"); g = Graph(); c = D["proposal/" + p["id"]]
    g.add((c, RDF.type, D.Claim)); g.add((c, D.status, Literal("alternative" if p["predicate"] == "threshold_value" else "active"))); g.add((c, D.source, Literal(p["source"]))); g.add((c, D.decided_by, Literal("proposed by agent; approver pending")))
    if p["predicate"] == "threshold_value":
        t = D["threshold/" + p["id"]]; g.add((t, RDF.type, D.Threshold)); th = _known()["thr"].get(p["subject"])
        g.add((t, D.op, Literal(th["op"] if th else "<")))
        try: g.add((t, D.value, Literal(float(p["value"]), datatype=XSD.double)))
        except (TypeError, ValueError): g.add((t, D.value, Literal(str(p["value"]))))
    ok, _, txt = validate(g, shacl_graph=str(HUB / "shapes.ttl"), inference="none"); msgs = re.findall(r"Message: (S\d+: [^\n]+)", txt)
    return ok, msgs
# ---- classification ----
def classify(p: dict, src_kind: str, src_ok: bool):
    """-> (risk, reasons). Deterministic rules, no LLM."""
    k = _known(); r = []; txt = " ".join(str(p.get(x, "")) for x in ("subject", "value", "target", "source"))
    if p["subject"] in k["restricted"] or str(p.get("target", "")) in k["restricted"] or re.search(r"\b(Person|Diagnosis|patient)\b", txt, re.I): r.append("touches restricted data (person/diagnosis)")
    if INJ.search(txt): r.append("instruction-like text in the proposal")
    if src_kind == "unverifiable": r.append("source not verifiable")
    if p["predicate"] == "relation": r.append("relations are never auto-written; needs owner change request")
    if p["predicate"] == "threshold_value":
        th = k["thr"].get(p["subject"]); ann = th["annotation"] if th else ""; lo, hi = PLAUSIBLE.get(ann, (-1e9, 1e9))
        try:
            if not lo <= float(p["value"]) <= hi: r.append(f"value outside plausible range {lo}..{hi} for {ann}")
        except (TypeError, ValueError): r.append("non-numeric value")
    if r: return "high", r
    if p["predicate"] == "threshold_value": return "medium", ["new alternative value for an existing safety-relevant threshold (never replaces the active claim)"]
    if src_kind == "local_self_reported": return "medium", ["local/self-reported source"]
    return "low", ["alias/note for a known public entity with a verifiable source"]
# ---- public API ----
def propose(role: str, subject: str, predicate: str, value, source: str, target: str | None = None) -> dict:
    pid = "P" + uuid.uuid4().hex[:8]; p = dict(id=pid, role=role, subject=subject, predicate=predicate, value=value, source=source, target=target); t0 = _now()
    audit("proposed", pid, role=role, subject=subject, predicate=predicate)
    def reject(reason, stage, **extra):
        rec = dict(p, status="rejected", stage=stage, reasons=[reason], created=t0, decided_at=_now(), decided_by="validator", **extra); _append("queue", rec); audit("rejected", pid, stage=stage, reasons=[reason]); return dict(proposal_id=pid, status="rejected", stage=stage, reasons=[reason], **extra)
    if role not in PROPOSERS: return reject(f"role '{role}' may not propose facts", "permission")
    if predicate not in ("threshold_value", "alias", "note", "relation"): return reject("unknown predicate", "schema")
    k = _known(); known = (subject in k["thr"]) if predicate == "threshold_value" else (subject in k["ent"] or subject in k["restricted"])
    if not known: return reject(f"subject '{subject}' is not a known {'threshold' if predicate == 'threshold_value' else 'entity'}", "validation")
    if not source or not str(source).strip(): return reject("no source: provenance is mandatory", "validation")
    src_kind, src_ok = source_check(str(source)); conforms, msgs = shacl_validate(p); audit("validated", pid, shacl=conforms, shacl_messages=msgs, source_kind=src_kind)
    if not conforms: return reject("; ".join(msgs) or "SHACL violation", "shacl", shacl=msgs)
    risk, reasons = classify(p, src_kind, src_ok); audit("classified", pid, risk=risk, reasons=reasons); base = dict(p, risk=risk, reasons=reasons, source_kind=src_kind, shacl="conforms", created=t0)
    if risk == "high": rec = dict(base, status="rejected", stage="risk", decided_at=_now(), decided_by="policy"); _append("queue", rec); audit("rejected", pid, stage="risk", reasons=reasons); return dict(proposal_id=pid, status="rejected", stage="risk", risk=risk, reasons=reasons)
    if risk == "low":
        rec = dict(base, status="auto_accepted", decided_at=_now(), decided_by="policy:low-risk"); _append("queue", rec); _append("staging", dict(proposal=pid, subject=subject, predicate=predicate, value=value, source=source, accepted_at=_iso(), note="staging only, not merged into the Hub")); audit("auto_accepted_to_staging", pid); return dict(proposal_id=pid, status="auto_accepted", risk=risk, reasons=reasons, note="written to staging only")
    _append("queue", dict(base, status="pending_approval")); audit("queued_for_approval", pid, risk=risk); return dict(proposal_id=pid, status="pending_approval", risk=risk, reasons=reasons)
def pending(): return [q for q in _latest() if q["status"] == "pending_approval"]
def _latest():
    out = {}
    for q in _read("queue"): out[q["id"]] = q
    return list(out.values())
def decide(proposal_id: str, approver: str, decision: str, comment: str = "", simulated: bool = False) -> dict:
    """Human decision. The agent identity can never decide; approved facts are written to approved_facts.jsonl with provenance."""
    if approver not in APPROVERS: audit("decision_refused", proposal_id, approver=approver); raise PermissionError(f"'{approver}' is not an authorised approver")
    q = next((x for x in _latest() if x["id"] == proposal_id), None)
    if q is None or q["status"] != "pending_approval": raise ValueError("no such pending proposal")
    if decision not in ("approve", "reject"): raise ValueError("decision must be approve|reject")
    now = _now(); rec = dict(q, status="approved" if decision == "approve" else "rejected", decided_at=now, decided_by=approver, comment=comment, stage="human", decision_simulated=simulated); _append("queue", rec)
    audit("approved" if decision == "approve" else "rejected", proposal_id, approver=approver, comment=comment, simulated=simulated, wait_s=round(now - q["created"], 3))
    if decision == "approve":
        _append("approved_facts", dict(fact=dict(subject=q["subject"], predicate=q["predicate"], value=q["value"], target=q.get("target")), status="alternative" if q["predicate"] == "threshold_value" else "active", provenance=dict(proposal=proposal_id, source=q["source"], source_kind=q["source_kind"], proposed_by_role=q["role"], approved_by=approver, decision_simulated=simulated, approved_at=_iso(now), shacl=q["shacl"], risk=q["risk"]), review_after=_iso(now + 180 * 86400)))
    return rec
def metrics() -> dict:
    L = _latest(); n = len(L); by = {s: sum(q["status"] == s for q in L) for s in ("auto_accepted", "approved", "rejected", "pending_approval")}
    need = [q for q in L if q.get("risk") in ("medium",) and q["status"] in ("approved", "rejected") and q.get("stage") == "human"]; waits = sorted(q["decided_at"] - q["created"] for q in need)
    risks = {r: sum(q.get("risk") == r for q in L) for r in ("low", "medium", "high")}
    return dict(proposals=n, by_status=by, by_risk=risks, rejected_before_risk=sum(q["status"] == "rejected" and "risk" not in q for q in L), medium_decided=len(need), approved_share_of_decided=round(sum(q["status"] == "approved" for q in need) / len(need), 3) if need else None,
                median_wait_s=round(waits[len(waits) // 2], 2) if waits else None, max_wait_s=round(waits[-1], 2) if waits else None, audit_chain_ok=verify_audit())
