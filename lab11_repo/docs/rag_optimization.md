# RAG optimisation experiment (R5): is the re-ranker worth its latency?

## Hypothesis and the single changed factor

**H:** switching the MaxSim re-ranker off (hybrid RRF top-5 instead of rerank of the top-30) lowers retrieval p50 latency by ≥40% while faithfulness, context recall and citation accuracy drop by no more than 3 percentage points.

Changed factor: `Config.rerank` True (**A**) → False (**B**). Everything else is identical: corpus, chunking (688 heading chunks), embedder `bge-small-en-v1.5`, k=5, graph on, prompt `rag_v1`, generator `claude-haiku-4-5-20251001`, judge `claude-sonnet-5-5`, the 34 tests, role filter. Because the context changes, the generator had to be re-run for 33 of 34 prompts (1 was identical); 33 new answers were generated and judged again (`llm_log/`). Reproduce: `python3 scripts/run_eval.py B && python3 scripts/aggregate.py B && python3 scripts/make_doc_r5.py`.

## Quality before / after

| metric | A: rerank on | B: rerank off | Δ (B−A) |
|---|---|---|---|
| faithfulness (claims supported) | 98.9% (89/90) | 97.8% (90/92) | -1.1 pp |
| answers fully faithful | 25/26 | 23/25 | -2 |
| context recall | 98.0% | 98.0% | +0.0 pp |
| citation validity | 100% | 100% | +0.0 pp |
| citation support (judged) | 98.8% | 96.6% | -2.2 pp |
| correct abstention | 88.9% (8/9) | 100.0% (9/9) | +11.1 pp |
| false abstention | 0% | 0% | 0 |
| conflicts detected / injections resisted | 4/4, 4/4 | 4/4, 4/4 | 0 |
| expected status reached | 33/34 | 34/34 | +1 |
| uncited sentences | 23 | 38 | +15 |

Mean overlap of the text chunks in the context (Jaccard) between A and B: 0.35; status differs in 1 of 34 tests (T24 only).

## Latency, tokens, cost

| | A: rerank on | B: rerank off | Δ |
|---|---|---|---|
| retrieval p50 (measured, warm, ms) | 26.3 | 12.3 | -53% |
| retrieval p95 (measured, warm, ms) | 36.5 | 18.9 | -48% |
| retrieval p50 / p95, first (cold) pass, ms | 1093 / 2740 | 12 / 16 | cold = token-vector cache not yet filled |
| graph build p50 / p95 (measured, ms) | 1.0 / 7.7 | 1.1 / 8.7 | – |
| mean input tokens / query | 2528 | 2438 | -4% |
| mean output tokens / query | 85 | 92 | +8% |
| end-to-end p50 / p95, s (**modelled**) | 1.08 / 1.84 | 1.21 / 2.06 | LLM part modelled |
| cost per query, USD (**modelled**) | 0.0030 | 0.0029 | -2% |

**What is measured and what is assumed.** Retrieval and graph times are measured wall-clock values on this machine (CPU, 34 queries, second pass; cold = first pass). The LLM calls were produced offline by subagents, so their real latency is unknown: end-to-end time uses the *assumed* model `0.4 s + 0.05 ms × input tokens + 8 ms × output tokens`; cost uses *assumed* list prices of $1 / $5 per million input / output tokens (haiku-class price recalled from memory – check the current price list). Token counts are estimated as chars/4 (Cyrillic chars/2.5), not by a tokenizer.

## Conclusion

- **Latency part of H is confirmed:** retrieval p50 26 → 12 ms (-53%), p95 36 → 19 ms (-48%); the target was ≥40%.
- **Quality part of H is not rejected:** the largest drop is citation support -2.2 pp (limit 3 pp), faithfulness -1.1 pp, context recall +0.0 pp. These are 1–2 claims out of ~90, far inside the noise of n=34 (95% CI ≈ ±3–5 pp); abstention rose by one test (T24) which is generation variance, not an effect of the factor. Uncited sentences rose 23 → 38; I cannot tell whether this is an effect of the context order or of the generator's randomness – to be checked with repeated generations.
- **Practical significance is small:** retrieval is ~1.0% of the modelled end-to-end time (1.21 s), so the 14 ms saved do not change what the user feels; tokens/cost change by -4% / -2%.
- The contexts of A and B differ a lot (Jaccard 0.35) yet quality is the same – so the quality is limited by the generator and the evidence being present in the top-5, not by the order inside it. The modelled end-to-end p50 is *higher* for B only because its answers are 8% longer (output tokens), which is generator variance, not retrieval.
- Cold start: the first pass with the re-ranker costs p50/p95 1093/2740 ms (token vectors are computed once per chunk and cached), B has no such penalty (12/16 ms).
- **Decision:** for this small corpus (688 chunks, hybrid search already puts the gold chunk in the top-5 in ~98% of the answerable tests) the re-ranker does not pay for itself; the API default may be B, A stays available (`Config(rerank=True)`). On a 10–100× larger corpus or harder queries the result may change – not tested here.
- **Limits:** one run per configuration; a single changed factor but a stochastic generator; judge leniency (see `rag_eval.md`); modelled LLM latency and cost.
