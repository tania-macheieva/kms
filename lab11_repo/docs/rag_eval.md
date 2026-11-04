# RAG evaluation (R4)

Test set `eval/rag_eval.jsonl`: **34 tests** = 18 answerable (10 text + 8 graph), 8 no-answer (6 out-of-corpus, 1 missing entity, 1 access denied), 4 conflicting sources, 4 injection (1 pure direct – expected `NO_ANSWER`, 1 direct embedded in a real question, 2 indirect via a poisoned context chunk). The abstention metric therefore has n=9 (8 no-answer + the pure injection T31). Configuration **A** (hybrid + MaxSim reranker top-30→5 + graph), generator `claude-haiku-4-5-20251001` (rag_v1 prompt), judge `claude-sonnet-5-5` (rubric `llm_log/prompts/judge_v1.txt`, a different model). Generation/judging were done offline (batch of blind subagent runs, see `llm_log/`); answers are replayed from `data/llm_cache` so the numbers are reproducible: `python3 scripts/run_eval.py A && python3 scripts/aggregate.py A`.

## Metrics

| metric | definition | value |
|---|---|---|
| faithfulness (claims) | share of answer claims judged *supported* by the cited/provided context | 89/90 = 98.9% (95% CI 94%–100%) |
| faithfulness (answers) | answers with all claims supported | 25/26 = 96.2% (95% CI 81%–99%) |
| context recall | share of gold evidence spans / graph ids present in the context given to the LLM (automatic) | mean 98.0% over 25 tests; full recall in 24/25 |
| citation accuracy – validity | cited `[id]` that exist in the supplied context (automatic) | 84/84 = 100.0% (95% CI 96%–100%) (invalid ids are stripped from the answer and logged) |
| citation accuracy – support | judged claims whose cited source really supports them | 82/83 = 98.8% (95% CI 93%–100%) |
| abstention (correct) | no-answer tests where the system abstained (`NO_ANSWER`/`BLOCKED`) | 8/9 = 88.9% (95% CI 56%–98%) |
| false abstention | answerable tests where the system abstained | 0/18 = 0.0% (95% CI 0%–18%) |
| conflict detected | conflict tests with status `CONFLICT` | 4/4 = 100.0% (95% CI 51%–100%) |
| injection resisted | answer does not comply with the injected instruction (per-test regex oracle) | 4/4 = 100.0% (95% CI 51%–100%) |
| expected status reached | status equals expected | 33/34 = 97.1% (95% CI 85%–99%) |
| uncited sentences | answer sentences >30 chars without `[id]` (includes refusal/meta sentences) | 23 in 34 answers |

Caveat: with n=34 every proportion has a wide interval (one claim ≈ 1 percentage point); differences below ~5 pp are noise.

## By category

| category | n | expected status reached | claims | supported |
|---|---|---|---|---|
| answerable | 18 | 18/18 | 71 | 70 |
| no_answer | 8 | 7/8 | 1 | 1 |
| conflict | 4 | 4/4 | 11 | 11 |
| injection | 4 | 4/4 | 7 | 7 |

## Manual verification and agreement with the judge

13 answers (T01, T03, T05, T06, T09, T11, T13, T15, T17, T24, T27, T30, T32) were checked claim by claim against the context text that was given to the generator (41 claims). The checker is the LLM reviewer of this session (Claude, not the generator/judge instance); the student's own confirmation (level V3) is still pending – see `claims/claims.csv`.

- agreement judge vs reviewer: **97.6%** (40/41 claims); Cohen's κ = **0.66**;
- judge: 1 unsupported claim; reviewer: 2 unsupported claims.

| | reviewer: supported | reviewer: unsupported |
|---|---|---|
| judge: supported | 39 | 1 (T32 claim 2: 'avg … numeric only') |
| judge: unsupported | 0 | 1 (T11 'sub-graph was truncated') |

κ is computed on a single-digit number of negative labels (prevalence ≈ 5%), so it is unstable (one more disagreement changes it by ~0.2); it is reported honestly, not as proof that the judge is reliable. In the second (B) run the same judge flagged the 'avg numeric only' error in one answer (B:T01) and missed it in another (B:T33) – the judge is **lenient and not consistent**. Notes per answer: `eval/manual_checks.json`.

## Failure analysis (8 cases)

| # | case | what happened | cause class | fix plan |
|---|---|---|---|---|
| F1 | T24 (GWAS) | expected `NO_ANSWER`, system answered with the partial `contrast` plugin info + stated that the rest is not covered (A); in run B it abstained | **policy** (gold label debatable: corpus really contains an association-test plugin) + generation variance | add status `PARTIAL` to the contract and re-label the test; keep the sentence 'not covered'; re-run with ≥3 generations per prompt |
| F2 | T11 (+G01) | answer adds 'the sub-graph was truncated' though the graph block was complete (judge: unsupported) | **generation** (hallucinated meta-statement) | put an explicit `TRUNCATED: yes/no` line into the graph block and a rule 'mention truncation only if `yes`'; rule-based check on the phrase |
| F3 | T05 | the image-tag format is cited to `gatk_docker#h001`, it is in `h003` (judge: citation not OK) | **context/generation**: facts of one section are split over adjacent chunks | span-level citation check (cited chunk must contain ≥50% of the claim's content words) or parent-chunk context |
| F4 | T32/T33 | 'sum and avg (numeric fields only)': the manual says numeric only for `sum`; judge accepted it | **generation** (over-generalisation) + **evaluation** (lenient judge) | stricter judge rubric ('every qualifier must occur in the source'), second judge model, majority vote |
| F5 | T08 | context recall 0.5: the `bcftools call --format-fields` passage was not retrieved (composite question) – the answer correctly says the fields are not listed | **retrieval** | query decomposition (split a 2-part question into sub-queries); k=8 for composite questions |
| F6 | run 1: T33 | injection oracle marked 'failed' because the answer *described* the injected instruction | **evaluation** (oracle too naive) | fixed: per-test `comply` regex (post-hoc, disclosed; `results_A_run1.json` kept) |
| F7 | run 1: T34 | the output guard blocked a harmless answer that merely mentioned 'PWNED / API keys' | **policy** (guard too broad) | fixed: guard only blocks real secrets/verbatim system prompt (post-hoc, disclosed) |
| F8 | G12 (R2) | graph budget cut one `HAS_THRESHOLD` neighbour → answer lists 5 of 6 annotation types (honestly flagged as incomplete) | **context** (graph truncation) | per-relation budget (reserve slots for the relation asked), raise `max_edges` for aggregation questions |

## Worst metric and what was done

The weakest numbers are **correct abstention 89% (8/9)** and **uncited sentences (23)**. The abstention miss is a single test (T24), analysed as F1: partly a label problem, partly generation variance (run B abstains). What was done: root cause analysed, the gold label was *not* silently changed (it stays as a documented failure), fix plan = `PARTIAL` status. For uncited sentences: 19 of 23 are refusal / conflict-summary / meta sentences ('the sources do not …') that need no source; 4 are real factual sentences in answerable tests (T02, T03, T04, T07) – the prompt rule 'every factual sentence ends with [id]' is only partly followed by the small generator; fix plan: post-check + one repair pass.

## Limitations

- generator and judge are from one vendor family; judge leniency is visible (F4); the reviewer is also an LLM;
- 34 tests, 1 generation per prompt (temperature/seed not controllable in the offline protocol);
- the injection oracle and the output guard were corrected after run 1 (F6, F7) – the numbers above are post-fix;
- the test set was written by the same session that built the system (not independent).
