"""Writes docs/graph_vs_text.md from eval/results_R2.json (numbers are generated, comments are hand-written)."""
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
rows = json.load(open(ROOT / "eval/results_R2.json")); S = json.load(open(ROOT / "eval/summary_R2.json")); T, G = S["text"], S["graph"]
note = {"G02": "Answer is correct (7 thresholds listed), but gold alias '7' is not matched by the word 'Seven' -> metric artefact, counted as 1/2 by the automatic rule.",
        "G12": "Real graph limit: the budget (max_edges=40, fan-out 6) cut one HAS_THRESHOLD neighbour (SOR); the answer honestly says the list may be incomplete.",
        "G07": "Text alone already contains the facts.", "G08": "Text alone already contains the facts.", "G11": "Text alone already contains the facts.",
        "G09": "Role clinician (restricted allowed): the diagnosis exists only in the graph; text gives the class and probability.",
        "G01": "Gold node :AnnotationType FS in context but the answer cites the Threshold nodes (more specific) -> 0 gold-node citations, facts correct."}
L = ["# Graph vs text: what the sub-graph adds (R2)", "",
     "Setup: 12 relational questions (`eval/graph_questions.jsonl`, gold facts verified by Cypher on the graph `dkh`). Same retriever, same generator (haiku, rag_v1 prompt), only the factor `use_graph` differs: **text** = hybrid top-5 chunks; **text+graph** = the same chunks + linearised sub-graph (entity linking, ≤2 hops, ≤24 nodes / ≤40 edges). Correct = all gold facts occur in the answer (alias match). Reproduce: `python3 scripts/run_r2.py`.", "",
     "| id | question | text only: facts | text only: status | text+graph: facts | text+graph: status | gold node ids cited | input tokens text → graph | comment |", "|---|---|---|---|---|---|---|---|---|"]
for r in rows:
    L.append(f"| {r['id']} | {r['question']} | {r['text']['facts_hit']}/{r['text']['facts_total']} | {r['text']['status']} | {r['graph']['facts_hit']}/{r['graph']['facts_total']} | {r['graph']['status']} | {r['graph']['gold_nodes_cited']}/{r['graph']['gold_nodes']} | {r['text']['in_tokens']} → {r['graph']['in_tokens']} | {note.get(r['id'], '')} |")
dt = G["in_tokens"] - T["in_tokens"]
L += ["", "## Totals", "", "| metric | text only | text + sub-graph |", "|---|---|---|",
      f"| questions fully correct | {T['correct']}/12 ({T['correct']/12:.0%}) | {G['correct']}/12 ({G['correct']/12:.0%}) |",
      f"| gold facts found | {T['facts']}/{T['facts_total']} ({T['facts']/T['facts_total']:.0%}) | {G['facts']}/{G['facts_total']} ({G['facts']/G['facts_total']:.0%}) |",
      f"| answers `NO_ANSWER` | {T['abstain']}/12 | {G['abstain']}/12 |",
      f"| gold node ids in the context | 0/{G['gold_nodes']} | {G['gold_ctx']}/{G['gold_nodes']} |",
      f"| gold node ids cited in the answer (traceability) | 0/{G['gold_nodes']} | {G['gold_cited']}/{G['gold_nodes']} ({G['gold_cited']/G['gold_nodes']:.0%}) |",
      f"| mean input tokens | {T['in_tokens']:.0f} | {G['in_tokens']:.0f} (+{dt:.0f}, +{dt/T['in_tokens']:.0%}) |",
      f"| mean output tokens | {T['out_tokens']:.0f} | {G['out_tokens']:.0f} |",
      f"| input tokens per correct answer | {12*T['in_tokens']/max(T['correct'],1):.0f} | {12*G['in_tokens']/max(G['correct'],1):.0f} |", "",
      "## Conclusion", "",
      f"- Quality: fully correct answers {T['correct']}/12 → {G['correct']}/12 (11/12 if the G02 alias artefact is corrected); gold facts {T['facts']/T['facts_total']:.0%} → {G['facts']/G['facts_total']:.0%}. Without the graph the model (correctly, by the rag_v1 policy) abstained on {T['abstain']} of 12 questions because relations such as `HAS_THRESHOLD`, `DERIVED_FROM`, `GENERATED_BY` are not stated in the text chunks; it never hallucinated them.",
      f"- Cost: +{dt:.0f} input tokens per question (+{dt/T['in_tokens']:.0%}) and +{G['out_tokens']-T['out_tokens']:.0f} output tokens; graph building takes a few ms (see `graph_ms` in the log). Per correct answer the graph variant is cheaper in tokens (the text variant spends tokens on 9 wrong/empty answers).",
      "- Explainability: in the graph variant the answers cite node ids `[G:Label:key]`, 15 of 17 gold nodes are cited.",
      "- Where the graph did not help: G07, G08, G11 (facts already in text) – there it only added tokens. Failure: G12 (budget truncation). Because the 12 questions were chosen *from* the graph (they are relational by design), the gain is an upper bound for the real mix of questions; on the 18 answerable tests of `rag_eval.jsonl` text-only vs graph can be compared with config flag `use_graph`.",
      "- Limits: n=12, one generator model, alias-match scoring, not a human grading."]
(ROOT / "docs/graph_vs_text.md").write_text("\n".join(L) + "\n", encoding="utf-8")
