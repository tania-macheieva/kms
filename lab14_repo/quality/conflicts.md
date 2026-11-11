# Conflicts: detection, resolution and decision log

Detection: `quality/conflicts.py` (rules over graph thresholds, fixture notes, corpus text, graph rules). Register of alternatives: `store_clean/alternatives.jsonl` (+ `quality/alternatives.cypher`, loaded into embedded FalkorDB in `scripts/demo_alternatives.py`).

| id | type | strategy | resolution | status |
|---|---|---|---|---|
| CF-QD | value | owner decision + source trust | graph value QD<2.0 (GATK, trust 1.0) stays the default; note value QD<1.5 kept as a scoped alternative (local lab SOP v3) | pending (V3) |
| CF-FS | value | owner decision + source trust | graph value FS>60 (SNP) stays default; clinic note FS>45 kept as scoped alternative | pending (V3) |
| CF-SOR | value | owner decision + source trust | graph value SOR>3 stays default; memo SOR>4 kept as scoped alternative | pending (V3) |
| CF-JAVA | temporal | date / version | README (Java 17, current) wins; legacy note (Java 8, GATK v4.2) is marked superseded with validTo | pending (V3) |
| CF-JAVA-TUT | temporal | date / version | Funcotator tutorial 'Java 1.8' is flagged outdated in the register; README Java 17 is authoritative (tutorial text itself is not edited) | pending (V3) |
| CF-ASM-GRCh37 | terminological | dictionary consensus | hg19 / b37 / GRCh37 are linked as skos:closeMatch (NOT exactMatch) because gatk_funco_refdiff states they are not interchangeable | pending (V3) |
| CF-ASM-GATK | terminological | dictionary consensus | canonical key GATK.GRCh38 (used in quickstart and config); GRCh38.GATK registered as a variant spelling of the same key | pending (V3) |
| CF-AGE-Sofiia | logical | rule wins | edge CT-01 APPLIES_TO Sofiia removed from the active graph and stored as DEFERRED_FOR with eligibleAtAge=18 | pending (V3) |

Origin of the data: CF-QD/FS/SOR and CF-JAVA compare real graph/README values with the **synthetic fixture notes** of lab 11 (constructed conflicts); CF-JAVA-TUT, CF-ASM-GRCh37 and CF-ASM-GATK come from the real documents; CF-AGE-Sofiia comes from the lab-9 graph (a synthetic Person).

Decision log fields: conflict, type, strategy, resolution, fix, **decided_by**, **decided_at**, rationale, status. `decided_by` is *proposed by Claude (LLM expert); approver: student* — the student has not approved the decisions yet (status *pending (V3)*).

FalkorDB query example — alternatives of CF-QD: `[1.5, 'alternative', 'local SOP / clinic protocol; not the vendor default', 'fx_sop_qd', 'proposed by Claude (LLM expert); approver: student (owner of the Hub)', '2026-11-06', 2.0]`; active claims: 4; superseded/outdated: 2.
