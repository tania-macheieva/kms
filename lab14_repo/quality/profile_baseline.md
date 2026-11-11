# Quality profile of the knowledge store (baseline = lab-11 hybrid store)

Snapshot: `store/` — 688 chunks, graph (370 nodes / 757 relationships), 4 fixture notes. Metrics: `quality/profile.py`; thresholds: `quality/thresholds.json`.

| id | dimension | metric | threshold | severity | baseline | verdict |
|---|---|---|---|---|---|---|
| M01 | completeness | share of chunks with all 10 required fields non-empty | >= 1.0 | blocking | 0.9956 | **FAIL** |
| M02 | validity | share of chunks valid against schema/chunk.schema.json | >= 1.0 | blocking | 0.9956 | **FAIL** |
| M03 | consistency | detected conflicts without a recorded resolution | <= 0 | blocking | 8 | **FAIL** |
| M04 | consistency | active graph edges violating a rule (minTestingAge) | <= 0 | blocking | 1 | **FAIL** |
| M07 | consistency | share of detected conflicts that have a decision-log entry and (value/temporal) a claim in the register | >= 1.0 | blocking | 0 | **FAIL** |
| M05 | traceability | share of chunks whose source span (start:end) is contained in the chunk text | >= 1.0 | blocking | 1 | ok |
| M08 | uniqueness | share of chunks that the dedup rule would absorb (exact text, score>=th+band or judged DUP) | <= 0.0 | blocking | 0.0203 | **FAIL** |
| M09 | timeliness | share of chunks with an ISO date not older than 365 days (relative to 2026-11-06) | >= 1.0 | blocking | 1 | ok |
| M10 | uniqueness | share of chunk_id values that are unique | >= 1.0 | blocking | 1 | ok |
| M11 | integrity | share of graph relationships whose both endpoints exist as nodes | >= 1.0 | blocking | 1 | ok |
| M12 | validity | share of chunks with sensitivity in {public, internal, restricted} | >= 1.0 | blocking | 1 | ok |
| M13 | consistency | share of chunks whose lang label agrees with the script of the text (Cyrillic share >0.3 <=> uk) | >= 0.99 | blocking | 0.9927 | ok |
| M14 | retrievability | share of chunks retrieved as top-1 by a TF-IDF query built from their own middle 200 characters (absorbed chunks count via their canonical) | >= 0.97 | warning | 0.9404 | **FAIL** |
| M06 | accuracy | share of expert-reviewed records with meta_ok and text_ok (36-record sample, LLM expert) | >= 0.9 | warning | 0.6389 | **FAIL** |

Severity: *blocking* failures fail the CI gate; *warning* failures are reported and tracked in the backlog (M06, M14).

## Top-3 priorities by impact on RAG answers

1. **Conflicting statements (M03 = 8, M04 = 1).** The model sees two values for the same fact (QD/FS/SOR thresholds, Java version) or a graph edge that breaks a rule; the answer is wrong, arbitrary or needlessly hedged. Impact is on correctness, so it is first.
2. **Near-duplicate chunks (M08 = 2.03%).** Duplicates fill top-k with the same text (retrieval probe: 17 of 55 top-5 slots redundant) and waste prompt tokens; on the 34 gold questions they do not occur in the contexts (see quality/after_report.md).
3. **Metadata and boundary defects in chunks (M06 = 0.64, M01/M02 = 0.9956).** Wrong document titles (4 documents), empty section names (3 chunks), chunks cut mid-sentence. They hurt citation quality and user trust; effect on automatic metrics is small.
