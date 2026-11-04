# Graph vs text: what the sub-graph adds (R2)

Setup: 12 relational questions (`eval/graph_questions.jsonl`, gold facts verified by Cypher on the graph `dkh`). Same retriever, same generator (haiku, rag_v1 prompt), only the factor `use_graph` differs: **text** = hybrid top-5 chunks; **text+graph** = the same chunks + linearised sub-graph (entity linking, ≤2 hops, ≤24 nodes / ≤40 edges). Correct = all gold facts occur in the answer (alias match). Reproduce: `python3 scripts/run_r2.py`.

| id | question | text only: facts | text only: status | text+graph: facts | text+graph: status | gold node ids cited | input tokens text → graph | comment |
|---|---|---|---|---|---|---|---|---|
| G01 | Which thresholds are checked for the annotation FS? | 0/2 | NO_ANSWER | 2/2 | ANSWER | 0/1 | 2394 → 2568 | Gold node :AnnotationType FS in context but the answer cites the Threshold nodes (more specific) -> 0 gold-node citations, facts correct. |
| G02 | Which procedure uses the threshold SOR_gt_3, and how many thresholds does it use in total? | 0/2 | NO_ANSWER | 1/2 | ANSWER | 2/2 | 2983 → 3439 | Answer is correct (7 thresholds listed), but gold alias '7' is not matched by the word 'Seven' -> metric artefact, counted as 1/2 by the automatic rule. |
| G03 | Which genes belong to the HBOC panel? | 0/4 | NO_ANSWER | 4/4 | ANSWER | 1/1 | 2453 → 2599 |  |
| G04 | Which file was sample1.vcf derived from, and which instrument generated it? | 0/2 | NO_ANSWER | 2/2 | ANSWER | 1/1 | 1859 → 2315 |  |
| G05 | In which gene is variant VAR-001 located, and which panel includes that gene? | 0/2 | NO_ANSWER | 2/2 | ANSWER | 2/2 | 2437 → 2881 |  |
| G06 | If sample1.bam is replaced, which downstream data files and procedures are affected? | 0/2 | NO_ANSWER | 2/2 | ANSWER | 1/2 | 2324 → 2466 |  |
| G07 | Who are the parents and the sibling of Olena? | 3/3 | ANSWER | 3/3 | ANSWER | 1/1 | 2148 → 2831 | Text alone already contains the facts. |
| G08 | Which variant does Olena carry, and in which gene is it located? | 2/2 | ANSWER | 2/2 | ANSWER | 2/2 | 2898 → 3581 | Text alone already contains the facts. |
| G09 | What diagnosis does Iryna have, and which relationship class does she belong to relative to the proband, with what inheritance probability? | 2/3 | ANSWER | 3/3 | ANSWER | 1/1 | 2633 → 3645 | Role clinician (restricted allowed): the diagnosis exists only in the graph; text gives the class and probability. |
| G10 | Which procedure requires variant VAR-001, and what is its minimum testing age? | 0/2 | NO_ANSWER | 2/2 | ANSWER | 2/2 | 2375 → 3196 |  |
| G11 | To which persons does the cascade testing procedure CT-01 apply? | 4/4 | ANSWER | 4/4 | ANSWER | 1/1 | 2240 → 2847 | Text alone already contains the facts. |
| G12 | Which annotation types have thresholds in the hard filtering procedure HF-01? | 0/6 | NO_ANSWER | 5/6 | ANSWER | 1/1 | 2624 → 3233 | Real graph limit: the budget (max_edges=40, fan-out 6) cut one HAS_THRESHOLD neighbour (SOR); the answer honestly says the list may be incomplete. |

## Totals

| metric | text only | text + sub-graph |
|---|---|---|
| questions fully correct | 3/12 (25%) | 10/12 (83%) |
| gold facts found | 11/34 (32%) | 32/34 (94%) |
| answers `NO_ANSWER` | 8/12 | 0/12 |
| gold node ids in the context | 0/17 | 17/17 |
| gold node ids cited in the answer (traceability) | 0/17 | 15/17 (88%) |
| mean input tokens | 2447 | 2967 (+519, +21%) |
| mean output tokens | 36 | 61 |
| input tokens per correct answer | 9789 | 3560 |

## Conclusion

- Quality: fully correct answers 3/12 → 10/12 (11/12 if the G02 alias artefact is corrected); gold facts 32% → 94%. Without the graph the model (correctly, by the rag_v1 policy) abstained on 8 of 12 questions because relations such as `HAS_THRESHOLD`, `DERIVED_FROM`, `GENERATED_BY` are not stated in the text chunks; it never hallucinated them.
- Cost: +519 input tokens per question (+21%) and +25 output tokens; graph building takes a few ms (see `graph_ms` in the log). Per correct answer the graph variant is cheaper in tokens (the text variant spends tokens on 9 wrong/empty answers).
- Explainability: in the graph variant the answers cite node ids `[G:Label:key]`, 15 of 17 gold nodes are cited.
- Where the graph did not help: G07, G08, G11 (facts already in text) – there it only added tokens. Failure: G12 (budget truncation). Because the 12 questions were chosen *from* the graph (they are relational by design), the gain is an upper bound for the real mix of questions; on the 18 answerable tests of `rag_eval.jsonl` text-only vs graph can be compared with config flag `use_graph`.
- Limits: n=12, one generator model, alias-match scoring, not a human grading.
