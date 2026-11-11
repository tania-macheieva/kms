# Human-in-the-loop for proposed facts (lab 15, R5)

Code: `agent/propose_fact.py` (validation, risk, queue, decision, audit, metrics); demo: `python scripts/demo_hitl.py` → `proposals/*.jsonl`, `eval/hitl_demo.json`; tests: `tests/test_hitl.py`.

**Important disclosure.** The human decisions in the demo (`decision_simulated=true` in every record) were made by the **LLM assistant**, not by the student/Hub owner. The approval *mechanism* is real and tested; the approval *latency* below is the 1-second pause of the script and says nothing about a real reviewer.

## 1. Flow

```
agent tool call propose_fact(subject, predicate, value, source[, target])
  → permission (role analyst/clinician)  → schema/subject known?  → source present?
  → SHACL (hub/shapes.ttl: S03 numeric threshold, S11/S12 claim status + provenance)
  → risk classification (deterministic rules)
       low    → staging register (NOT the Hub), audit
       medium → queue 'pending_approval' → human decide(approve|reject) → approved_facts.jsonl with provenance
       high   → rejected, reasons returned
every step → proposals/audit.jsonl (hash chain)
```

Figure 1. Proposal flow (text diagram).

## 2. Validation and risk classes (R5 C1)

| Check | Rule | Rejection stage |
|---|---|---|
| permission | only `analyst` and `clinician` may propose; `reader` may not | permission |
| subject | threshold id / gene / procedure / panel must exist in the graph snapshot | validation |
| provenance | `source` mandatory | validation |
| SHACL | candidate Claim + candidate Threshold built in RDF and validated against `hub/shapes.ttl` (pySHACL) | shacl |
| source kind | corpus chunk/doc id or allow-listed URL = verifiable; `local:` = self-reported; anything else = unverifiable | risk (high) |

| Risk | Rule | Action |
|---|---|---|
| **low** | alias/note about a known public entity, SHACL conforms, verifiable source | auto-accept into *staging* (not the Hub) |
| **medium** | a new *alternative* value for an existing (safety-relevant) threshold — it can never replace the active claim; or a local/self-reported source | human approval required |
| **high** | touches Person/Diagnosis/"patient"; value outside a plausible range (e.g. QD −3); instruction-like text; unverifiable source; any relation proposal | rejected, no queue |

Table 1. Risk classes. The rules are deterministic code, not an LLM judgement, so they cannot be talked out of a decision by the text of a proposal.

## 3. Three scenarios (R5 C3)

| Scenario | Proposal | Outcome | Why |
|---|---|---|---|
| L1 | alias RNF53 for BRCA1 | auto-accepted → staging | alias/note for a known public entity with a verifiable source |
| L2 | note for HF-01 (allow-listed URL) | auto-accepted → staging | alias/note for a known public entity with a verifiable source |
| M1 | QD alt 1.5 (local SOP) | approved by human (simulated) | new alternative value for an existing safety-relevant threshold (never replaces the active claim) — human: matches Lab SOP v3; scope local; keep as alternative |
| M2 | FS alt 45 (clinic protocol) | approved by human (simulated) | new alternative value for an existing safety-relevant threshold (never replaces the active claim) — human: matches clinic protocol; alternative only |
| M3 | SOR alt 9 | rejected by human (simulated) | new alternative value for an existing safety-relevant threshold (never replaces the active claim) — human: no evidence in the source; SOR 9 is implausible for a hard filter |
| H1 | note about Olena (restricted) | rejected by policy | touches restricted data (person/diagnosis) |
| H2 | QD alt -3 (implausible) | rejected by policy | value outside plausible range 0.1..50 for QD |
| H3 | note with instruction text | rejected by policy | instruction-like text in the proposal |
| H4 | relation on a person | rejected by policy | touches restricted data (person/diagnosis); relations are never auto-written; needs owner change request |

Table 2. Low (auto), medium (approval) and high (rejected) scenarios. Plus invalid proposals V1–V5 (no source, unknown subject, non-numeric value → SHACL S03, reader role, unverifiable source), all rejected before any write.

The agent cannot approve: `decide(..., approver='agent')` raises `PermissionError` and is audit-logged (`decision_refused`). An approved fact is written to `proposals/approved_facts.jsonl` with `provenance` (proposal id, source, source kind, proposer role, approver, SHACL result, risk) and `review_after` = +180 days. **Nothing is merged into `hub/`**: merging approved facts into the graph/register is a separate, owner-run step (not implemented, to keep the agent's write path minimal).

## 4. Audit log and metrics (R5 C4)

`proposals/audit.jsonl`: append-only, each record carries `prev` and `hash` (sha256 over the record and the previous hash); `verify_audit()` = **True**; a modified record breaks the chain (`test_audit_chain_detects_tampering`). It is tamper-*evident*, not tamper-proof (whoever can rewrite the whole file can rebuild the chain).

| Metric | Value |
|---|---|
| proposals in the demo | 14 |
| by risk (low / medium / high) | 2 / 3 / 5 |
| rejected before risk classification (permission/validation/SHACL) | 4 |
| auto-accepted into staging | 2 |
| medium proposals decided by the human | 3 |
| **approved share of decided medium proposals** | **67%** (2 of 3) |
| approval wait: median / max | 1.03 s / 1.04 s (**simulated**, script pause) |

Table 3. HITL metrics from `eval/hitl_demo.json` (`agent.propose_fact.metrics()`). The demo set is hand-made (14 proposals), so the shares illustrate the mechanism; they are not estimates of real-world approval rates.

## 5. Limits

* The proposer is an LLM-driven agent but the demo proposals were scripted; whether a real agent would phrase safe proposals was not measured.
* `local:` sources are self-reported and never verified against a document — they are only allowed at medium risk, so a human must look.
* The approver list is a constant (`owner:student`); a real deployment needs authentication of the approver.
* The plausible-range table covers six annotations only.
