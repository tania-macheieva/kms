"""Builds claims/claims.csv: V1 (reproducible check against project files / lab report extracts) is computed here; V2/V3/V4 are recorded by hand (see claims/README.md).
python scripts/verify_claims.py"""
import json, csv, pathlib, re
ROOT = pathlib.Path(__file__).resolve().parent.parent
S = json.load(open(ROOT / "eval/summary.json")); A = json.load(open(ROOT / "eval/ablation.json")); C = json.load(open(ROOT / "eval/cold_summary.json")); X = json.load(open(ROOT / "eval/explanations.json"))["summary"]
lab = lambda n: open(ROOT / f"claims/sources/lab{n}.txt", encoding="utf-8").read()
sm = S["summary"]; near = lambda a, b, t=6e-4: abs(a - b) < t
inl = lambda n, *subs: all(s in lab(n) for s in subs)
SRC_AI = "https://ai-act-service-desk.ec.europa.eu/en/ai-act/timeline/timeline-implementation-eu-ai-act ; https://artificialintelligenceact.eu/high-level-summary/"
SRC_OM = "https://www.gibsondunn.com/eu-ai-act-omnibus-agreement-postponed-high-risk-deadlines-and-other-key-changes/ ; https://datamatters.sidley.com/2026/06/22/eu-lawmakers-reach-provisional-agreement-to-delay-key-eu-ai-act-obligations/"
# id, claim, type, source, V1 check (callable or None), V2, V4, status, comment
R = [
("c01", "Weighted hybrid has mean nDCG@10 = 0.129 over 5 generator seeds (synthetic data)", "fact", "eval/summary.json", lambda: near(sm["hybrid-weighted"]["ndcg10"]["mean"], 0.129), "tests: split/leakage", "pass", "verified", "synthetic interactions"),
("c02", "Popularity baseline has mean nDCG@10 = 0.093", "fact", "eval/summary.json", lambda: near(sm["popularity"]["ndcg10"]["mean"], 0.093), "tests", "pass", "verified", ""),
("c03", "Coverage@5: hybrid 0.195 vs popularity 0.020", "fact", "eval/summary.json", lambda: near(sm["hybrid-weighted"]["coverage"]["mean"], 0.195) and near(sm["popularity"]["coverage"]["mean"], 0.020), "n/a", "pass", "verified", "coverage CI = range over seeds"),
("c04", "Hybrid beats popularity on nDCG@10 by +0.036, paired bootstrap 95% CI excludes 0", "fact", "eval/summary.json paired_ndcg_hybrid_minus", lambda: S["paired_ndcg_hybrid_minus"]["popularity"]["lo"] > 0 and near(S["paired_ndcg_hybrid_minus"]["popularity"]["mean_diff"], 0.036), "n/a", "pass", "verified", "300 user-seed pairs, users repeat across seeds with different data"),
("c05", "The graph component improves the tuned hybrid", "hypothesis", "eval/ablation.json", lambda: A["mean"]["tuned"]["ndcg10"] > A["mean"]["without_graph"]["ndcg10"], "n/a", "fail", "rejected", "ablation: without graph 0.133 >= tuned 0.129; the graph weight was tuned to 0 in 4/5 seeds"),
("c06", "Validation tuning set w_graph = 0 in 4 of 5 seeds", "fact", "eval/summary.json tuned", lambda: sum(S["tuned"][s]["hyb_w"]["graph"] == 0 for s in S["tuned"]) == 4, "n/a", "pass", "verified", ""),
("c07", "kNN is significantly better than graph on nDCG@10", "hypothesis", "eval/summary.json", lambda: (sm["knn"]["ndcg10"]["mean"] - sm["graph"]["ndcg10"]["mean"]) > 2 * max(sm["knn"]["ndcg10"]["sd"], sm["graph"]["ndcg10"]["sd"]), "n/a", "fail", "rejected", "0.087 vs 0.081 is smaller than the between-seed SD (0.011-0.021): no significance claim"),
("c08", "All 100 template explanations match a real graph/embedding path and pass the consistency check", "fact", "eval/explanations.json", lambda: X["share_template_ok_and_path_exists"] == 1.0 and X["n"] == 100, "tests/test_explain.py", "pass", "verified", "checker covers dictionary entities, quoted titles, numbers only; was loosened after false positives (c09)"),
("c09", "The explanation checker was loosened after the first runs (81% -> 100% template acceptance) because of false positives, not because explanations changed", "fact", "docs/cold_start.md", None, "n/a", "n/a", "pending", "initial pass rates were observed on the console and not stored; V1 not reproducible"),
("c10", "All 100 LLM paraphrases passed the automatic check (share_paraphrase_ok = 1.0)", "fact", "eval/explanations.json", lambda: X["paraphrased"] == 100 and X["paraphrase_accepted"] == 100, "n/a", "pass", "verified", "does not prove absence of un-dictionaried claims"),
("c11", "Four kinds of corrupted explanations are always rejected (negative controls)", "fact", "eval/explanations.json negative_controls", lambda: all(v["rejected"] == v["total"] and v["total"] > 0 for v in X["negative_controls"].values()), "tests/test_explain.py", "pass", "verified", ""),
("c12", "New user, no history: topic-popularity nDCG@10 0.108 > global popularity 0.065", "fact", "eval/cold_summary.json", lambda: near(C["new_user"]["0"]["topic-popularity"]["ndcg10"], 0.108, 1e-3) and near(C["new_user"]["0"]["popularity"]["ndcg10"], 0.065, 1e-3), "n/a", "pass", "verified", "declared topics are taken from latent preferences (idealised)"),
("c13", "New sections get 0 graph score before add_item and a non-zero hit-rate after it", "fact", "eval/cold_summary.json", lambda: C["new_item"]["new_section"]["before_insert"]["graph"] == 0 and C["new_item"]["new_section"]["after_insert"]["graph"] > 0, "tests/test_cold.py", "pass", "verified", "hit-rate@10 <= 0.073"),
("c14", "Readers never receive internal/restricted items; unverified items are filtered when verified_only", "rule", "docs/filters_demo.txt; reco/data.py", lambda: "by sensitivity {'public'" in open(ROOT / "docs/filters_demo.txt").read(), "tests/test_reco.py::test_filters, tests/test_app.py", "n/a", "verified", ""),
("c15", "Lab 10: hybrid BM25+bge (RRF) recall@5 = 0.836 on 55 questions", "fact", "Lab10 report Table 13", lambda: inl(10, "0.836"), "n/a", "n/a", "verified", "re-read from report extract; not re-run"),
("c16", "Lab 11: RAG faithfulness 89/90 claims = 98.9%", "fact", "Lab11 report Table 7", lambda: inl(11, "89/90"), "n/a", "n/a", "verified", "not re-run"),
("c17", "Lab 14: deduplication reduced 688 chunks to 674", "fact", "Lab14 report Table 5", lambda: inl(14, "688") and inl(14, "674"), "n/a", "n/a", "verified", "not re-run"),
("c18", "Lab 15: attack success naive 21/22 vs hardened 1/22 (assume-breach)", "fact", "Lab15 report Table 12", lambda: inl(15, "21/22"), "n/a", "n/a", "verified", "simulated compromised brain"),
("c19", "Lab 8: triple store holds 4425 quads; SHACL valid set conforms", "fact", "Lab8 report Table 1/7", lambda: inl(8, "4425"), "n/a", "n/a", "verified", ""),
("c20", "Lab 12: 22/22 warehouse DQ checks passed", "fact", "Lab12 report (result text: «пройдено 22 з 22 перевірок»)", lambda: inl(12, "22 з 22"), "n/a", "n/a", "verified", ""),
("c21", "Lab 7: ontology consistent (HermiT), 17/17 competency questions pass", "fact", "Lab7 report 4.1", lambda: inl(7, "17/17"), "n/a", "n/a", "verified", ""),
("c22", "Lab 9: text-to-Cypher 25/27 and 26/27 correct over two runs", "fact", "Lab9 report Table 18", lambda: inl(9, "25/27") and inl(9, "26/27"), "n/a", "n/a", "verified", ""),
("c23", "Lab 6: LLM triple extraction vs expert map P/R/F1 = 0.51/0.43/0.47", "fact", "Lab6 report Table 13", lambda: inl(6, "0.47") or inl(6, "0,47"), "n/a", "n/a", "verified", ""),
("c24", "Lab 5: Cohen's kappa between rater runs and expert taxonomy 0,916", "fact", "Lab5 report Table 6", lambda: inl(5, "0,916"), "n/a", "n/a", "verified", "both raters are LLM"),
("c25", "The EU AI Act (Reg. 2024/1689) entered into force on 1 Aug 2024; prohibitions and AI literacy applied from 2 Feb 2025", "fact", SRC_AI, None, "two sources agree (service desk timeline, artificialintelligenceact.eu)", "n/a", "verified", "accessed 2026-11-08"),
("c26", "GPAI model obligations apply from 2 Aug 2025", "fact", SRC_AI, None, "service desk timeline", "n/a", "verified", ""),
("c27", "Article 50 transparency obligations apply from 2 Aug 2026; grace period to 2 Dec 2026 for Art. 50(2) for systems already on the market", "fact", SRC_AI + " ; " + SRC_OM, None, "three sources agree", "n/a", "verified", ""),
("c28", "After the Digital Omnibus on AI, Annex III high-risk obligations apply from 2 Dec 2027 and Annex I from 2 Aug 2028", "fact", SRC_AI + " ; " + SRC_OM, None, "service desk timeline reflects the amendment; two law-firm notes", "n/a", "verified", "final OJ publication step not checked by the author"),
("c29", "Annex III high-risk obligations apply from 2 Aug 2026", "fact", "LLM memory (draft)", None, "contradicted by c28", "n/a", "rejected", "outdated statement from the LLM's own knowledge; replaced after web check"),
("c30", "NIST AI RMF 1.0 (NIST AI 100-1, 26 Jan 2023) has four functions: GOVERN, MAP, MEASURE, MANAGE", "fact", "https://clearpointstrategy.com/blog/nist-ai-rmf-explained-govern-map-measure-manage (secondary); NIST AI 100-1", None, "one secondary source + NIST document title", "n/a", "verified", "primary PDF not reachable from the sandbox; V3 should check against NIST AI 100-1"),
("c31", "NIST AI 600-1 (Generative AI Profile) was released on 26 Jul 2024", "fact", "https://clearpointstrategy.com/blog/nist-ai-rmf-explained-govern-map-measure-manage (secondary)", None, "one secondary source", "n/a", "pending", "needs primary-source confirmation"),
("c32", "The Hub recommender and Q&A are not high-risk systems under Annex III (documentation/learning-support use, no decisions about persons)", "hypothesis", "author analysis of Annex III categories", None, "n/a", "n/a", "pending", "legal review needed; clinical use would change the classification"),
("c33", "An LLM paraphrase never changes the facts of the graph path", "hypothesis", "eval/explanations.json", lambda: X["paraphrase_accepted"] == X["paraphrased"], "n/a", "partial", "pending", "supported only for dictionary entities, titles, numbers; V3 spot-check required"),
]
rows = []
for id_, claim, typ, src, chk, v2, v4, st, com in R:
    v1 = "n/a" if chk is None else ("pass" if chk() else "fail")
    if v1 == "fail" and st == "verified": raise SystemExit(f"{id_}: V1 failed for a claim marked verified")
    rows.append(dict(id=id_, claim=claim, type=typ, source=src, V1=v1, V2=v2, V3="pending (human reviewer)", V4=v4, status=st, comment=com))
with open(ROOT / "claims/claims.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
n = len(rows); print(n, "claims;", {s: sum(r["status"] == s for r in rows) for s in ("verified", "rejected", "pending")}, "share verified = %.0f%%" % (100 * sum(r["status"] == "verified" for r in rows) / n))
