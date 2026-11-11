# After-repair report

## 1. Quality profile before / after

| metric | threshold | baseline | after |
|---|---|---|---|
| M01_completeness (completeness, blocking) | >= 1.0 | 0.9956 ✗ | 1 |
| M02_schema_validity (validity, blocking) | >= 1.0 | 0.9956 ✗ | 1 |
| M03_open_conflicts (consistency, blocking) | <= 0 | 8 ✗ | 0 |
| M04_active_logical_violations (consistency, blocking) | <= 0 | 1 ✗ | 0 |
| M07_conflict_documentation (consistency, blocking) | >= 1.0 | 0 ✗ | 1 |
| M05_provenance_fidelity (traceability, blocking) | >= 1.0 | 1 | 1 |
| M08_near_duplicate_share (uniqueness, blocking) | <= 0.0 | 0.0203 ✗ | 0 |
| M09_freshness (timeliness, blocking) | >= 1.0 | 1 | 1 |
| M10_id_uniqueness (uniqueness, blocking) | >= 1.0 | 1 | 1 |
| M11_graph_referential_integrity (integrity, blocking) | >= 1.0 | 1 | 1 |
| M12_sensitivity_valid (validity, blocking) | >= 1.0 | 1 | 1 |
| M13_language_consistency (consistency, blocking) | >= 0.99 | 0.9927 | 0.9926 |
| M14_self_retrieval_at1 (retrievability, warning) | >= 0.97 | 0.9404 ✗ | 0.957 ✗ |
| M06_expert_sample_accuracy (accuracy, warning) | >= 0.9 | 0.6389 ✗ | 0.6389 ✗ |

## 2. RAG on the 34 lab-11 tests (config A: hybrid + reranker + graph)

| metric | before | after |
|---|---|---|
| faithfulness_claims | 0.9889 | 0.9885 |
| context_recall | 0.98 | 0.98 |
| citation_support | 0.988 | 0.988 |
| citation_validity | 1 | 1 |
| abstention_correct | 0.8889 | 0.8889 |
| false_abstention | 0 | 0 |
| conflict_detected | 1 | 1 |
| injection_resisted | 1 | 1 |
| status_ok | 33 | 33 |
| retrieve_ms_p50 | 22.64 | 22.27 |
| retrieve_ms_p95 | 32.05 | 33.3 |
| in_tokens_mean | 2528 | 2539 |
| claims_total | 90 | 87 |

Tests whose context or answer changed: T20, T27, T28, T29, T30 (all other 29 answers are identical replays). Faithfulness and citation support of changed answers were re-judged by a separate LLM call; the rest reuse the lab-11 judge verdicts.

## 3. Retrieval probe on duplicate topics (not part of the 34 tests)

11 queries (first ~18 words of each merged cluster's canonical chunk, no LLM): redundant top-5 slots 17/55 → 0/55; distinct chunks in top-5 38 → 55; cluster still found 11 → 11. The queries are verbatim snippets of the chunks, so this demonstrates redundancy removal, not a realistic recall estimate.

## 4. CI defect injection

| defect | gate | caught by |
|---|---|---|
| D1_duplicate_chunk | FAIL | Q11_metric_threshold[M08_near_duplicate_share] |
| D2_age_rule_violation | FAIL | Q01_shacl_conforms; Q11_metric_threshold[M03_open_conflicts]; Q11_metric_threshold[M04_active_logical_violations]; Q11_metric_threshold[M07_conflict_documentation] |
| D3_relationship_without_provenance | FAIL | Q10_sql_relationship_provenance |
| ALL_THREE | FAIL | Q01_shacl_conforms; Q10_sql_relationship_provenance; Q11_metric_threshold[M03_open_conflicts]; Q11_metric_threshold[M04_active_logical_violations]; Q11_metric_threshold[M07_conflict_documentation]; Q11_metric_threshold[M08_near_duplicate_share] |

## 5. Analysis

* The 34-question RAG set was already at the ceiling in lab 11 (faithfulness ≈ 0.99, context recall 0.98), and none of its contexts contained a duplicate cluster, so de-duplication changes the contexts of only one test (T20, an abstention) and does not change any metric. Honest conclusion: **no measurable RAG gain on this set**; the gain is in the store (profile) and in the probe.
* Conflict tests T27–T30 now receive a claim-register chunk (active value + scoped alternative / superseded value). In this run the generator still answered `CONFLICT` for all four, so conflict_detected stays 1.0. A first attempt before the environment was reset produced `ANSWER` for the Java question; generation is not deterministic (temperature/seed are not controllable), so a single run cannot separate the register's effect from noise. A gold set that expects `CONFLICT` also contradicts the idea of a resolved default; it should be revised (decision for the owner).
* Latency: retrieve p50/p95 are within measurement noise (over-fetch of 10 chunks to skip absorbed ids); both runs were measured in the same process on the same machine.
* Remaining failures: M06 (expert-sample accuracy 0.64, warning) — the repair fixed wrong titles and empty sections, but the expert review also found chunk-boundary cuts and stray section names that are not repaired; M14 (self-retrieval@1, warning) improved by removing duplicates but remains below 0.97 because of template-like chunks.
* The expert and all annotators are LLMs of the same family; V3 (human approval) is pending.

## 6. Maintenance process (how the store stays clean)

1. Every change to `store/` or the graph opens a branch; CI (`.github/workflows/quality.yml`) runs unit tests and `quality/gate.py`; any blocking failure blocks the merge; warnings are listed in the PR.
2. New documents go through `make_pairs`-style blocking against the existing store; borderline pairs are judged and logged; accepted merges are written to `merge_log.jsonl` (reversible).
3. New conflicts are detected by `conflicts.py` or reported by users; each gets a decision-log row (who/when/why) and a claim in the register before it can be released.
4. Monthly: re-draw the 36-record expert sample, update the gold pairs with new disagreements, track `quality/history.jsonl` for trends; owner reviews pending decisions.
5. Backlog: fix chunk boundaries (M06), improve M14, extend the gold set to ≥ 40 duplicate pairs, replace LLM annotators by a human reviewer for a sample.
