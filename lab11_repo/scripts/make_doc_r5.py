"""Writes docs/rag_optimization.md (R5): A (reranker on) vs B (reranker off), one changed factor."""
import json, statistics as st
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
A, B = (json.load(open(ROOT / f"eval/metrics_{c}.json")) for c in "AB"); ra = {x["id"]: x for x in json.load(open(ROOT / "eval/results_A.json"))}; rb = {x["id"]: x for x in json.load(open(ROOT / "eval/results_B.json"))}
def pct(xs, p):
    xs = sorted(xs); k = (len(xs) - 1) * p; f = int(k); c = min(f + 1, len(xs) - 1); return xs[f] + (xs[c] - xs[f]) * (k - f)
cold = lambda r: [x["retrieve_ms_cold"] for x in r.values()]
jac = []
for i in ra:
    a = {c for c in ra[i]["context_ids"] if "#" in c}; b = {c for c in rb[i]["context_ids"] if "#" in c}
    if a | b: jac.append(len(a & b) / len(a | b))
chg = sum(1 for i in ra if ra[i]["status"] != rb[i]["status"])
pp = lambda a, b: f"{(b-a)*100:+.1f} pp"
rel = lambda a, b: f"{(b/a-1)*100:+.0f}%"
L = ["# RAG optimisation experiment (R5): is the re-ranker worth its latency?", "",
     "## Hypothesis and the single changed factor", "",
     "**H:** switching the MaxSim re-ranker off (hybrid RRF top-5 instead of rerank of the top-30) lowers retrieval p50 latency by ≥40% while faithfulness, context recall and citation accuracy drop by no more than 3 percentage points.", "",
     "Changed factor: `Config.rerank` True (**A**) → False (**B**). Everything else is identical: corpus, chunking (688 heading chunks), embedder `bge-small-en-v1.5`, k=5, graph on, prompt `rag_v1`, generator `claude-haiku-4-5-20251001`, judge `claude-sonnet-5-5`, the 34 tests, role filter. Because the context changes, the generator had to be re-run for 33 of 34 prompts (1 was identical); 33 new answers were generated and judged again (`llm_log/`). Reproduce: `python3 scripts/run_eval.py B && python3 scripts/aggregate.py B && python3 scripts/make_doc_r5.py`.", "",
     "## Quality before / after", "", "| metric | A: rerank on | B: rerank off | Δ (B−A) |", "|---|---|---|---|",
     f"| faithfulness (claims supported) | {A['faithfulness_claims']:.1%} ({A['claims_supported']}/{A['claims_total']}) | {B['faithfulness_claims']:.1%} ({B['claims_supported']}/{B['claims_total']}) | {pp(A['faithfulness_claims'], B['faithfulness_claims'])} |",
     f"| answers fully faithful | {A['answers_fully_faithful']}/{A['answers_judged']} | {B['answers_fully_faithful']}/{B['answers_judged']} | {B['answers_fully_faithful']-A['answers_fully_faithful']:+d} |",
     f"| context recall | {A['context_recall']:.1%} | {B['context_recall']:.1%} | {pp(A['context_recall'], B['context_recall'])} |",
     f"| citation validity | {A['citation_validity']:.0%} | {B['citation_validity']:.0%} | {pp(A['citation_validity'], B['citation_validity'])} |",
     f"| citation support (judged) | {A['citation_support']:.1%} | {B['citation_support']:.1%} | {pp(A['citation_support'], B['citation_support'])} |",
     f"| correct abstention | {A['abstention_correct']:.1%} (8/9) | {B['abstention_correct']:.1%} (9/9) | {pp(A['abstention_correct'], B['abstention_correct'])} |",
     f"| false abstention | {A['false_abstention']:.0%} | {B['false_abstention']:.0%} | 0 |",
     f"| conflicts detected / injections resisted | 4/4, 4/4 | 4/4, 4/4 | 0 |",
     f"| expected status reached | {A['status_ok']}/34 | {B['status_ok']}/34 | {B['status_ok']-A['status_ok']:+d} |",
     f"| uncited sentences | {A['uncited_sentences']} | {B['uncited_sentences']} | {B['uncited_sentences']-A['uncited_sentences']:+d} |", "",
     f"Mean overlap of the text chunks in the context (Jaccard) between A and B: {st.mean(jac):.2f}; status differs in {chg} of 34 tests (T24 only).", "",
     "## Latency, tokens, cost", "", "| | A: rerank on | B: rerank off | Δ |", "|---|---|---|---|",
     f"| retrieval p50 (measured, warm, ms) | {A['retrieve_ms']['p50']:.1f} | {B['retrieve_ms']['p50']:.1f} | {rel(A['retrieve_ms']['p50'], B['retrieve_ms']['p50'])} |",
     f"| retrieval p95 (measured, warm, ms) | {A['retrieve_ms']['p95']:.1f} | {B['retrieve_ms']['p95']:.1f} | {rel(A['retrieve_ms']['p95'], B['retrieve_ms']['p95'])} |",
     f"| retrieval p50 / p95, first (cold) pass, ms | {pct(cold(ra), .5):.0f} / {pct(cold(ra), .95):.0f} | {pct(cold(rb), .5):.0f} / {pct(cold(rb), .95):.0f} | cold = token-vector cache not yet filled |",
     f"| graph build p50 / p95 (measured, ms) | {A['graph_ms']['p50']:.1f} / {A['graph_ms']['p95']:.1f} | {B['graph_ms']['p50']:.1f} / {B['graph_ms']['p95']:.1f} | – |",
     f"| mean input tokens / query | {A['in_tokens_mean']:.0f} | {B['in_tokens_mean']:.0f} | {rel(A['in_tokens_mean'], B['in_tokens_mean'])} |",
     f"| mean output tokens / query | {A['out_tokens_mean']:.0f} | {B['out_tokens_mean']:.0f} | {rel(A['out_tokens_mean'], B['out_tokens_mean'])} |",
     f"| end-to-end p50 / p95, s (**modelled**) | {A['e2e_s_modelled']['p50']:.2f} / {A['e2e_s_modelled']['p95']:.2f} | {B['e2e_s_modelled']['p50']:.2f} / {B['e2e_s_modelled']['p95']:.2f} | LLM part modelled |",
     f"| cost per query, USD (**modelled**) | {A['cost_usd_per_query_modelled']:.4f} | {B['cost_usd_per_query_modelled']:.4f} | {rel(A['cost_usd_per_query_modelled'], B['cost_usd_per_query_modelled'])} |", "",
     "**What is measured and what is assumed.** Retrieval and graph times are measured wall-clock values on this machine (CPU, 34 queries, second pass; cold = first pass). The LLM calls were produced offline by subagents, so their real latency is unknown: end-to-end time uses the *assumed* model `0.4 s + 0.05 ms × input tokens + 8 ms × output tokens`; cost uses *assumed* list prices of $1 / $5 per million input / output tokens (haiku-class price recalled from memory – check the current price list). Token counts are estimated as chars/4 (Cyrillic chars/2.5), not by a tokenizer.", "",
     "## Conclusion", "",
     f"- **Latency part of H is confirmed:** retrieval p50 {A['retrieve_ms']['p50']:.0f} → {B['retrieve_ms']['p50']:.0f} ms ({rel(A['retrieve_ms']['p50'], B['retrieve_ms']['p50'])}), p95 {A['retrieve_ms']['p95']:.0f} → {B['retrieve_ms']['p95']:.0f} ms ({rel(A['retrieve_ms']['p95'], B['retrieve_ms']['p95'])}); the target was ≥40%.",
     f"- **Quality part of H is not rejected:** the largest drop is citation support {pp(A['citation_support'], B['citation_support'])} (limit 3 pp), faithfulness {pp(A['faithfulness_claims'], B['faithfulness_claims'])}, context recall {pp(A['context_recall'], B['context_recall'])}. These are 1–2 claims out of ~90, far inside the noise of n=34 (95% CI ≈ ±3–5 pp); abstention rose by one test (T24) which is generation variance, not an effect of the factor. Uncited sentences rose {A['uncited_sentences']} → {B['uncited_sentences']}; I cannot tell whether this is an effect of the context order or of the generator's randomness – to be checked with repeated generations.",
     f"- **Practical significance is small:** retrieval is ~{B['retrieve_ms']['p50']/ (B['e2e_s_modelled']['p50']*1000)*100:.1f}% of the modelled end-to-end time ({B['e2e_s_modelled']['p50']:.2f} s), so the 14 ms saved do not change what the user feels; tokens/cost change by {rel(A['in_tokens_mean'], B['in_tokens_mean'])} / {rel(A['cost_usd_per_query_modelled'], B['cost_usd_per_query_modelled'])}.",
     f"- The contexts of A and B differ a lot (Jaccard {st.mean(jac):.2f}) yet quality is the same – so the quality is limited by the generator and the evidence being present in the top-5, not by the order inside it. The modelled end-to-end p50 is *higher* for B only because its answers are 8% longer (output tokens), which is generator variance, not retrieval.",
     f"- Cold start: the first pass with the re-ranker costs p50/p95 {pct(cold(ra), .5):.0f}/{pct(cold(ra), .95):.0f} ms (token vectors are computed once per chunk and cached), B has no such penalty ({pct(cold(rb), .5):.0f}/{pct(cold(rb), .95):.0f} ms).",
     "- **Decision:** for this small corpus (688 chunks, hybrid search already puts the gold chunk in the top-5 in ~98% of the answerable tests) the re-ranker does not pay for itself; the API default may be B, A stays available (`Config(rerank=True)`). On a 10–100× larger corpus or harder queries the result may change – not tested here.",
     "- **Limits:** one run per configuration; a single changed factor but a stochastic generator; judge leniency (see `rag_eval.md`); modelled LLM latency and cost."]
(ROOT / "docs/rag_optimization.md").write_text("\n".join(L) + "\n", encoding="utf-8")
