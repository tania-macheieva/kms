"""docs/hitl.md (R5) from eval/hitl_demo.json and proposals/*.jsonl"""
import json, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
D = json.load(open(ROOT / "eval/hitl_demo.json", encoding="utf-8")); M = D["metrics"]; Q = {q["id"]: q for q in map(json.loads, open(ROOT / "proposals/queue.jsonl", encoding="utf-8"))}
L = ["# Human-in-the-loop for proposed facts (lab 15, R5)", "",
"Code: `agent/propose_fact.py` (validation, risk, queue, decision, audit, metrics); demo: `python scripts/demo_hitl.py` → `proposals/*.jsonl`, `eval/hitl_demo.json`; tests: `tests/test_hitl.py`.", "",
"**Important disclosure.** The human decisions in the demo (`decision_simulated=true` in every record) were made by the **LLM assistant**, not by the student/Hub owner. The approval *mechanism* is real and tested; the approval *latency* below is the 1-second pause of the script and says nothing about a real reviewer.", "",
"## 1. Flow", "", "```", "agent tool call propose_fact(subject, predicate, value, source[, target])", "  → permission (role analyst/clinician)  → schema/subject known?  → source present?", "  → SHACL (hub/shapes.ttl: S03 numeric threshold, S11/S12 claim status + provenance)", "  → risk classification (deterministic rules)", "       low    → staging register (NOT the Hub), audit", "       medium → queue 'pending_approval' → human decide(approve|reject) → approved_facts.jsonl with provenance", "       high   → rejected, reasons returned", "every step → proposals/audit.jsonl (hash chain)", "```", "",
"Figure 1. Proposal flow (text diagram).", "",
"## 2. Validation and risk classes (R5 C1)", "",
"| Check | Rule | Rejection stage |", "|---|---|---|",
"| permission | only `analyst` and `clinician` may propose; `reader` may not | permission |", "| subject | threshold id / gene / procedure / panel must exist in the graph snapshot | validation |", "| provenance | `source` mandatory | validation |",
"| SHACL | candidate Claim + candidate Threshold built in RDF and validated against `hub/shapes.ttl` (pySHACL) | shacl |", "| source kind | corpus chunk/doc id or allow-listed URL = verifiable; `local:` = self-reported; anything else = unverifiable | risk (high) |", "",
"| Risk | Rule | Action |", "|---|---|---|",
"| **low** | alias/note about a known public entity, SHACL conforms, verifiable source | auto-accept into *staging* (not the Hub) |",
"| **medium** | a new *alternative* value for an existing (safety-relevant) threshold — it can never replace the active claim; or a local/self-reported source | human approval required |",
"| **high** | touches Person/Diagnosis/\"patient\"; value outside a plausible range (e.g. QD −3); instruction-like text; unverifiable source; any relation proposal | rejected, no queue |", "",
"Table 1. Risk classes. The rules are deterministic code, not an LLM judgement, so they cannot be talked out of a decision by the text of a proposal.", "",
"## 3. Three scenarios (R5 C3)", "", "| Scenario | Proposal | Outcome | Why |", "|---|---|---|---|"]
for lab in ("L1 alias RNF53 for BRCA1", "L2 note for HF-01 (allow-listed URL)", "M1 QD alt 1.5 (local SOP)", "M2 FS alt 45 (clinic protocol)", "M3 SOR alt 9", "H1 note about Olena (restricted)", "H2 QD alt -3 (implausible)", "H3 note with instruction text", "H4 relation on a person"):
    s = next(x for x in D["scenarios"] if x["label"] == lab); final = Q[s["proposal_id"]]; out = {"auto_accepted": "auto-accepted → staging", "approved": "approved by human (simulated)", "rejected": "rejected by human (simulated)" if final.get("stage") == "human" else "rejected by policy"}[final["status"]]
    L.append(f"| {lab[:2]} | {lab[3:]} | {out} | {'; '.join(s.get('reasons', []))[:110]}{(' — human: ' + final['comment']) if final.get('comment') else ''} |")
L += ["", "Table 2. Low (auto), medium (approval) and high (rejected) scenarios. Plus invalid proposals V1–V5 (no source, unknown subject, non-numeric value → SHACL S03, reader role, unverifiable source), all rejected before any write.", "",
"The agent cannot approve: `decide(..., approver='agent')` raises `PermissionError` and is audit-logged (`decision_refused`). An approved fact is written to `proposals/approved_facts.jsonl` with `provenance` (proposal id, source, source kind, proposer role, approver, SHACL result, risk) and `review_after` = +180 days. **Nothing is merged into `hub/`**: merging approved facts into the graph/register is a separate, owner-run step (not implemented, to keep the agent's write path minimal).", "",
"## 4. Audit log and metrics (R5 C4)", "",
f"`proposals/audit.jsonl`: append-only, each record carries `prev` and `hash` (sha256 over the record and the previous hash); `verify_audit()` = **{M['audit_chain_ok']}**; a modified record breaks the chain (`test_audit_chain_detects_tampering`). It is tamper-*evident*, not tamper-proof (whoever can rewrite the whole file can rebuild the chain).", "",
"| Metric | Value |", "|---|---|", f"| proposals in the demo | {M['proposals']} |", f"| by risk (low / medium / high) | {M['by_risk']['low']} / {M['by_risk']['medium']} / {M['by_risk']['high']} |",
f"| rejected before risk classification (permission/validation/SHACL) | {M['rejected_before_risk']} |", f"| auto-accepted into staging | {M['by_status']['auto_accepted']} |", f"| medium proposals decided by the human | {M['medium_decided']} |",
f"| **approved share of decided medium proposals** | **{M['approved_share_of_decided']*100:.0f}%** (2 of 3) |", f"| approval wait: median / max | {M['median_wait_s']} s / {M['max_wait_s']} s (**simulated**, script pause) |", "",
"Table 3. HITL metrics from `eval/hitl_demo.json` (`agent.propose_fact.metrics()`). The demo set is hand-made (14 proposals), so the shares illustrate the mechanism; they are not estimates of real-world approval rates.", "",
"## 5. Limits", "", "* The proposer is an LLM-driven agent but the demo proposals were scripted; whether a real agent would phrase safe proposals was not measured.", "* `local:` sources are self-reported and never verified against a document — they are only allowed at medium risk, so a human must look.", "* The approver list is a constant (`owner:student`); a real deployment needs authentication of the approver.", "* The plausible-range table covers six annotations only.", ""]
(ROOT / "docs/hitl.md").write_text("\n".join(L), encoding="utf-8"); print("ok")
