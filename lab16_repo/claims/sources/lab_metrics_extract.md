# Lab metrics (labs 5-15, excl. 13) - extracted verbatim from /tmp/labtxt/labN.txt

## Lab 5 - Taxonomy of domain concepts (biomedical data analysis; expert vs LLM vs embedding-cluster, SKOS)
Headline results:
- Corpus: "сирих кандидатів: 722; унікальних сирих форм: 590 видалено шуму: 18 ... канонічних термінів: 121; з alt_labels: 70; з визначенням: 121 злито форм: 572 унікальних форм → 121 термінів" (Result 1, §2.1, Fig. 1)
- Node counts/depth: "Вузлів | 155 | 171 | 161 | 154" (expert|llm|cluster|final); "Глибина ... | 4 | 4 | 3 | 4" (Table 5)
- Coverage of 121 corpus terms: "100% | 100% | 100% | 100%"; share of "Інше": "0%" in all (Table 5)
- Structural defects M2 (single-child internal nodes): "6 | 7 | 6 | 3"; M1 duplicates 0 in all four (Table 5)
- Manual MECE violations: "4 | 5 | 4 | 0 відомих*" (expert|llm|cluster|final) (Table 5)
- Cohen's kappa on 30 terms (random, seed 7), 8 level-1 categories: R1 vs R2 "1,000 | 100%"; R1 vs expert taxonomy "0,916 | 93% (28/30)"; R2 vs expert "0,916 | 93% (28/30)" (Table 6, §4.2); report: kappa 1.0 "завищений"
- ARI between versions, level 1 (8/10/9 groups): expert~llm 0,454; expert~cluster 0,122; llm~cluster 0,177; final~expert 0,887; final~llm 0,509; final~cluster 0,139 (Table 7)
- SKOS: "models/taxonomy.ttl (rdflib; 1345 триплетів)"; "19 passed in 1.33s" (13 tests test_taxonomy.py + 6 test_corpus_versions.py) (§6, Fig. 6)
- MeSH links: 10 (8 exactMatch, 2 closeMatch), verified 2026-10-22 "URI й мітка збігаються" (Table 13); claims.csv: "24 твердження; підтверджено 13 (54%); відхилено 6; pending 5" (§7)
Caveats:
- "Експерт" and both annotators are LLM; kappa = 1,0 inflated; human annotation sheet (annotations/rater_human_template.csv) not filled.
- Definitions, translations, cluster names are unverified LLM drafts (def_status = llm_draft); freq only from 2 texts, 94 terms freq = 0; spaCy static vectors instead of sentence-transformers, 4 OOV terms (BRCA2, ClinVar, dbSNP, UniProt).
- Links only to MeSH, semantic equivalence judged by LLM; EDAM/Sequence Ontology checks failed (pending); educational, not clinical.
Artefacts: models/terms.csv, tax_expert.csv, tax_llm.json, tax_cluster.csv, taxonomy_final.csv, taxonomy.ttl; scripts/normalize_terms.py, build_expert_tax.py, cluster_taxonomy.py, eval_taxonomies.py, build_final_tax.py, export_skos.py, draw_tree.py; tests/test_taxonomy.py, test_corpus_versions.py; docs/taxonomy_final.png/.svg, docs/evidence/pytest_all.txt; llm_log/; claims/claims.csv; annotations/rater_human_template.csv; data/external_links.csv.

## Lab 6 - Semantic network / Novak concept map (expert v1, LLM triples, colleague map, rubric, merged v2)
Headline results:
- Expert map v1: "33 понять, 6 екземплярів, 49 підписаних пропозицій і 5 крос-зв'язків; частка «related to» — 0%" (Result 2); relation catalogue 12 types (Table 2); parking lot 39 concepts (Table 1)
- LLM triples: "Отримано 41 триплетів (gatk 24, cdc 17) і 17 unmapped"; V1 quote check "Підтверджено 41/41 = 100%"; V2 type check "Коректних 40/41 = 98%; без жодної помилки 36/41 = 88%"; after manual review "частка триплетів, підтриманих текстом, — 29/41 = 71%" (Result 3); 12 error cases (Table 8)
- Rubric scores /20: own v1 R1 16, R2 18; LLM-map R1 9, R2 12; "Колега" (LLM) R1 17, R2 18 (Table 10)
- Rater agreement (15 pairs): mean |diff| 0.40; exact/within 1 "67% / 93%"; Pearson/Spearman "0.76 / 0.76"; quadratic kappa "0.68" (Table 11)
- Precision/recall vs expert map (strict): LLM triples TP 21, predicted 41, reference 49, P 0.51, R 0.43, F1 0.47; colleague TP 27, predicted 53, P 0.51, R 0.55, F1 0.53; LLM relaxed P 0.56, R 0.47 (Table 13)
- CQ coverage by v1: "повністю 5 CQ, частково 3" of 18 CQ (Table 3, Table 4 C4)
- Merged v2: "39 понять, 12 екземплярів, 72 пропозицій, 5 крос-зв'язків, «related to» 0%"; triples_final.csv 72 rows: "verified 34 ... expert_asserted 37 ... pending 1"; validate_v2.py "0 помилок", all 51 concepts defined (Result 5)
- claims.csv: "54 тверджень; підтверджено 39 (72%); відхилено 12; pending 3"; no V4 (human-verified) claims (§7)
Caveats:
- Colleague and both raters are LLM runs, not humans; agreement inflated; no human rating; no claim reaches V4.
- Precision/recall understated (expert map is an incomplete reference); definitions from Lab 5 unverified; "FS > 200 для INDEL" pending verification vs GATK docs.
- Verbatim prompt for triple extraction not saved (structure reconstructed). Educational, not clinical.
Artefacts: docs/cmap_focus.md, cmap_rubric.xlsx, cmap_changes_v1_v2.md, docs/evidence/triples_check.txt; models/cmap_expert.json/.png/.drawio, triples_llm.jsonl, cmap_llm.png, cmap_v2.json/.png/.drawio, triples_final.csv; scripts/build_expert_map.py, map_tools.py, check_triples.py, eval_maps.py, build_v2.py, validate_v2.py, build_rubric_xlsx.py, build_claims.py; llm_log/; claims/claims.csv; repo lab06_repo.

## Lab 7 - Domain ontology in OWL (built by scripts, HermiT reasoner, SPARQL CQ tests, comparison with LLM draft, OntoClean)
Headline results:
- Ontology size: "78 класів", "35 object і 16 data властивостей"; models/onto.owl "1373 триплети"; "15 груп диз'юнктних класів", "12 означених (≡) класів" (Result 1-2, Table 4, Table 6)
- Axioms: "Аксіоми існування (∃): 17; універсальності (∀): 2; кардинальні ... (4)"; Table 5 lists 24 axioms
- HermiT (HermiT.jar from owlready2 0.51, Java 21): "код завершення 0, необґрунтованих класів 0 — онтологія узгоджена" (§4.1)
- Individuals: "39 предметних індивідів"; "середнє 3,3" properties per individual; HermiT inferred "18 виведених типів і 44 зв'язки" (Table 8, Fig. 4, Table 9)
- Deliberate contradictions: 2 (SNP/Indel disjointness for VAR-003; Person hasParent <= 2 with three parents for Marta) both raise InconsistentOntologyException, removed -> consistent again (§4.2)
- CQ SPARQL tests: "моя онтологія 17/17 = 100%; чернетка LLM 16/17 = 94% (не пройдено CQ19)" (Table 16)
- Comparison vs LLM draft (Table 13): classes 78 vs 166; name match 40; missing 38; extra 126 (121 from Lab5 taxonomy nodes, 5 new); object props with domain 35 vs 0, with range 35 vs 1; defined (≡) classes 12 vs 1; types inferred beyond declared 18 vs 2; individuals 39 (3.31) vs 52 (3.12); both HermiT-consistent, 0 unsatisfiable
- Situation templates: "6 шаблонів"; 3 SPARQL situation queries S01/S03/S06 all OK (Table 10, Fig. 7); OntoClean: 8 class groups (Table 15); claims.csv "52 тверджень; підтверджено 34 (65%); відхилено 7; pending 11"; pytest "14 passed" (§10)
Caveats:
- Protege not used (unavailable), no screenshots; no owl:imports, only SKOS/MeSH mapping; level V3 (human expert) reached by no claim.
- "Expert", draft author, OntoClean ratings are LLM; CQs written after the ontology and with the labels given to the draft, so "100% — не незалежний еталон".
- Individuals fictitious; FS > 200 for INDEL from reader comment (pending); childhood-cancer age exception not modelled; not for clinical use.
Artefacts: models/onto.owl, onto_data.ttl, llm_draft.ttl, onto_inferred.ttl, class_table.csv, property_dictionary.csv, situations.csv, model_meta.csv; docs/reasoner_log.md, onto_eval.md, class_hierarchy.png/.svg, docs/evidence/hermit_classify.txt, hermit_instances.txt; tests/cq_sparql/*.rq (17), tests/sparql_situations/*.rq (3); scripts/onto_model.py, build_onto.py, build_data.py, check_definitions.py, reasoner_run.py, run_cq.py, compare_onto.py; repo lab07_repo.

## Lab 8 - RDF store and SPARQL (pyoxigraph, SHACL, text-to-SPARQL evaluation, Wikidata links)
Headline results:
- Store load: "усього 4425 квадів, збіг із файлами; kb.ttl — 3923 триплети"; graphs tbox 1382, abox 2438, inferred 520, links 85 (Table 1); version kb-0.1.0, loaded 2026-10-27; JSON-LD "69 сутностей, 377 тріплетів"
- SPARQL: 9 queries q01-q09, each tied to a CQ (Table 3); slowest q06 property path "157.03" ms, median of 5 runs; others 0.24-5.84 ms
- Query optimisation (50000 variants, 900000 triples; both return 2764): "472.4 → 99.7 мс", "прискорення ≈ 4.7×" (§3.1, Table 5 C3); report: conclusion limited to one engine/set/machine
- Manual check of 4 queries (q01, q04, q06, q08) all matched (Table 4, level V2)
- SHACL (pySHACL 0.40.1): "9 вузлових форм, 18 форм властивостей, 43 обмежень"; valid set "conforms = True; Violation — 0; попередження — 3"; defective set "conforms = False, 3 Violation + 3 Warning" (Table 7)
- Text-to-SPARQL, 24 questions (18 dev + 6 held-out), correct result: v1 "16/24 (67%)", v2 "18/24 (75%)"; dev 12/18 (67%) -> 14/18 (78%); held-out 4/6 (67%) -> 4/6 (67%); syntactically correct 24/24 and schema-only 24/24 for both (Table 9); "v2 виправила 7 питань, але зламала 5"
- Text-to-SPARQL errors: 6 classes E1-E6; Table 11 lists 14 error rows (Table 12 C4 says "13 помилок")
- Wikidata links: "9 прийнятих зв'язків" (closeMatch/relatedMatch, confidence low to medium-high), 4 rejected (Tables 13-14); claims.csv "24 тверджень; підтверджено 16 (67%), відхилено 3 (12%), pending 5 (21%)"; pytest "12 passed"
Caveats:
- pyoxigraph instead of Fuseki/GraphDB; federated query ran against a local mirror of Wikidata labels (scripts/mock_wikidata.py), not real Wikidata; links verified only by title in search list (V1), type not checked.
- Text-to-SPARQL: one run per version, unknown temperature; v1->v2 improvement "у межах шуму" and not established; v2 introduced new error E6; references/queries/shapes authored by the same system (V3/V4 not reached).
- SHACL shape relaxed to Warning after seeing results ("підігнано під дані"); data synthetic (seed 42); timings on small set, one engine.
Artefacts: data/kb.ttl, data/graphs/{tbox,abox,inferred}.ttl, data/links.ttl, data/kb.jsonld, docs/load_log.md, sparql_results.md, shacl_report.md, t2s_eval.md, links_verification.md; queries/q01...q09.rq, queries/results/*.json; shapes/shapes.ttl, report_valid.ttl, report_defective.ttl; tests/t2s.jsonl; scripts/build_kb.py, load_store.py, run_queries.py, t2s.py, eval_t2s.py, mock_wikidata.py, run_all.sh; data/links_decisions.csv; llm_log/; claims/claims.csv; repo lab08_repo.

## Lab 9 - Graph knowledge base (LPG; run on embedded FalkorDB, NOT Neo4j), Cypher, graph analytics, text-to-Cypher
Headline results:
- Graph size: "Вузли: 370; зв'язків: 757 (19 типів)"; 14 labels; Variant 64, Annotation 248, Person 8, Gene 4 (Table 4); source RDF graph "3923 тріпли"; 6 unique constraints, 10 indexes (Tables 6-7)
- Import idempotence: first import 370 nodes / 757 rels / 44 ms; repeat 370 / 757 / 34 ms (Table 5)
- Cypher queries: 11 queries c01-c11, median of 5 runs 0.27-2.7 ms (Table 9); 6 queries manually verified, all match (Table 10, V2)
- Impact analysis c09 (QD_lt_2): "BRCA2, 18; TP53, 16; BRCA1, 14; PALB2, 14"; c10: sample1_vcf, HF-01, 7 thresholds
- Graph analytics: PageRank top-1 "AnnotationType:FS 0.08673"; Louvain "17 спільнот, модулярність 0.4319" (networkx, seed 42) (Tables 12-13); report: modularity "помірна", structure largely an artefact of the model
- Index optimisation (synthetic, 80 000 annotations): PROFILE scan of 80000 nodes -> index scan 1145 records; synthetic graph "20000 variants, 100000 nodes" (Fig. 6-7; timing numbers only in figure, not text)
- SPARQL vs Cypher: 5 questions, results match in 4/5, P5 differs (explained; matches with IS NOT NULL); length sum "851 симв. / 138 слів" vs "661 симв. / 61 слів"; time sum 0.97 ms (pyoxigraph) vs 2.17 ms (FalkorDB), "висновку про рушії немає" (Tables 15-16)
- text-to-Cypher (27 questions, schema in prompt, 2 runs): all "25/27 (93%)" r1, "26/27 (96%)" r2; simple 15/16 and 16/16; complex 10/11 both; passed safety+schema 27/27 both; executed without error 26/27 both (Table 18); safety test: write/delete/SET/CALL rejected by filter, fake label/property/rel-type rejected by schema check (Table 17)
- claims.csv "22 тверджень; підтверджено 15 (68%), відхилено 3 (14%), pending 4 (18%)"; pytest "16 passed"
Caveats:
- Neo4j and GDS not used (no Docker, download blocked): FalkorDB engine, PageRank native, Louvain networkx; nothing verified on real Neo4j; Neo4j reader role not tested.
- Text-to-Cypher references authored by same system (V3/V4 not reached); 11 hard questions added after first results; only 2 runs, unknown temperature; one error (t20) is FalkorDB shortestPath dialect issue.
- Data synthetic; confidence values (0.8/0.95/1.0) assigned by source category, not statistical; timings on small data/one engine; PageRank/Louvain findings are model artefacts.
Artefacts: docs/graph_schema.png/.dot/.svg, cq_mapping.md, import_log.md, cypher_results.md, gds_report.md, sparql_vs_cypher.md; data/*.csv (14 node + 21 rel files); import/00_schema.neo4j.cypher, 01_nodes.cypher, 02_rels.cypher; queries/c01...c11.cypher, queries/results/*.json; tests/t2c.jsonl; scripts/build_csv.py, gds.py, run_all.sh; docker-compose.yml; llm_log/raw/t2c_*.json; claims/claims.csv; repo lab09_repo.

## Lab 10 - Vector store and semantic search (chunking, embeddings, hybrid BM25+dense RRF, rerank, gold set)
Headline results:
- Corpus: "33 документів → 688 фрагментів" (nf-core/sarek 8/215, raredisease 4/96, bcftools 2/148, GATK 10/157, own reports 9/72 uk); text reduced "з 827 524 до 673 869 символів"; sensitivity public 616, internal 18, restricted 54 chunks (Tables 1-2)
- Chunking (dense bge-small, top-5, 55 queries): fixed-200/40 recall@5 "0.727 [0.62; 0.83]" MRR 0.545; heading-250 "0.764 [0.66; 0.85]" MRR 0.657 (chosen); hierarchical-70/500 "0.591 [0.46; 0.71]" MRR 0.491; semantic "0.600 [0.48; 0.72]" MRR 0.501 (Table 4); heading vs fixed not significant (CIs overlap)
- Embeddings, 20 queries, dense top-5 (Table 7): minilm recall@5 0.80 (EN 0.93, UK 0.50) MRR 0.62 nDCG@10 0.65 latency 3.5 ms; bge recall@5 0.80 (EN 0.86, UK 0.67) MRR 0.68 nDCG@10 0.69 latency 11.9 ms; index HNSW M=32, efConstruction=200, efSearch=64; "ANN recall@10 ... = 1.0 уже при efSearch = 16"
- Gold set: "61 запитів (17 keyword, 20 paraphrase, 10 багатокрокових, 4+4 українських, 6 без відповіді)"; second rater agreement "126/135, Cohen's κ = 0.721" (12 queries, 135 pairs; LLM-LLM)
- Main evaluation, 55 answerable queries, recall@5 / recall@10 / MRR@10 / nDCG@10 / latency (Table 13): BM25 0.818 / 0.827 / 0.651 / 0.680 / 0.8 ms; Dense MiniLM 0.745 / 0.809 / 0.613 / 0.635 / 3.3 ms; Dense bge-small 0.764 / 0.836 / 0.657 / 0.683 / 13.6 ms; Hybrid BM25+bge RRF k=60 "0.836 [0.74; 0.93]" / 0.900 / 0.723 / 0.750 / 14.0 ms; Hybrid BM25+MiniLM 0.818 / 0.845 / 0.728 / 0.730 / 4.2 ms; Hybrid+rerank MaxSim top30->5 0.855 / 0.909 / 0.711 / 0.748 / 613.1 ms
- Paired differences: Hybrid(bge) - Dense bge nDCG@10 "+0.067 [+0.00; +0.13]" (only difference whose CI excludes ~0); rerank - hybrid recall@5 "+0.018 [-0.05; +0.09]", MRR@10 "-0.012" (Table 15); recall@5 uk_cross is 0.00 for hybrid and 0.25 for dense bge (Table 14)
- Rerank: top-5 changed "у 55 з 55 запитів"; latency "з 15 до 670 мс (медіана)" in §5 text vs 613.1 ms in Table 13; no-answer queries AUC "0.57 для MiniLM і 0.73 для bge при 6 запитах"; metadata pre-filter tests pass (Table 11); cost "$0 за запит"; claims.csv "24 тверджень; verified 13 (54%), rejected 5 (21%), pending 6 (25%)"; 11 autotests
Caveats:
- English-only models (multilingual-e5 unavailable): cross-lingual retrieval effectively fails, only 8 of 61 queries Ukrainian; reranker is MaxSim, not a cross-encoder.
- Gold set, evidence and adjudication produced/reviewed by LLM; kappa between two LLMs; human review (V3) not done; 55 queries -> CI about ±0.09, most config differences not significant.
- Corpus is technical documentation, not clinical literature; only 688 vectors (HNSW scaling not tested); embedding time extrapolated from 100-chunk sample; LLM temperature/seed not controlled.
Artefacts: data/corpus.jsonl, docs/corpus_card.md, chunking_cmp.md, embeddings_cmp.md, hybrid_report.md, search_eval.md; eval/gold.jsonl, eval/adjudication.json; src/chunking.py, index.py (VectorStore), embed.py, hybrid.py (Retriever); scripts/build_corpus.py, make_corpus_card.py, build_gold.py, exp_hybrid.py, fetch_models.sh, run_all.sh; data/models/SHA256SUMS; docs/evidence/*.json; llm_log/prompts/gold_gen_v1.txt; claims/claims.csv.

## Lab 11 - RAG chatbot on hybrid store (text corpus Lab10 + graph Lab9), citations, REST API, evaluation
Headline results (configuration A: reranker on; generator claude-haiku-4-5-20251001, judge claude-sonnet-5-5; n=34 tests) (Table 7):
- faithfulness (claims) "89/90 = 98.9% [94%; 100%]"; faithfulness (whole answers) "25/26 = 96.2% [81%; 99%]"
- context recall "98.0% (повний у 24/25)"
- citation accuracy: validity "84/84 = 100.0% [96%; 100%]"; support (judge) "82/83 = 98.8% [93%; 100%]"
- abstention (correct refusal) "8/9 = 88.9% [56%; 98%]"; false refusal on answerable "0/18"; conflicts detected "4/4"; injections resisted "4/4"; expected status "33/34"; uncited sentences 23 (19 refusals/meta-summaries, 4 factual)
- Test set composition: 34 = answerable 18 / no_answer 8 / conflict 4 / injection 4 (Result 4)
- Graph vs text-only (12 relational questions, Table 3 conclusion): fully correct "3/12 → 10/12"; facts found "11/34 (32%) → 32/34 (94%)"; cost "+519 вхідних токенів на питання (+21%)"; graph node ids cited "15 з 17 золотих id"; report: gain is an upper estimate (questions chosen from the graph, n=12)
- Manual check by LLM reviewer: 13 answers / 41 claims, agreement with judge "97.6% (40/41), κ Коена = 0.66"; judge lenient and inconsistent
- Optimisation A->B (reranker off; Tables 10-11): faithfulness 98.9% -> 97.8% (-1.1 pp); citation support 98.8% -> 96.6% (-2.2 pp); retrieval p50 "26.3 -> 12.3 мс (-53%)" and p95 "36.5 -> 18.9" (measured; text says -52%/-46%); modelled cost per request 0.0030 -> 0.0029 USD; context Jaccard 0.35
- API: endpoints POST /ask, GET /sources/{id}, GET /health; roles reader/analyst/clinician; limit 10 requests/60 s per key; 29 autotests; claims.csv "24 тверджень; verified 14 (58%), rejected 3 (12%), pending 7 (29%)"
Caveats:
- No LLM API key: answers generated by blind subagent batches replayed from hash cache (ReplayLLM); AnthropicLLM client never run; LLM latency and cost are modelled (0.4 s + 0.05 ms/input token + 8 ms/output token; $1/$5 per M tokens, not checked), only retrieval time measured.
- "Human" check done by LLM reviewer; test set made by the same session as the system; injection oracle and output guard adjusted after run 1 (T33/T34); generator and judge from same vendor; one generation per prompt, differences below ~5 pp are noise.
- API not covered: TLS, key rotation, JWT, distributed rate limit; default API backend is ExtractiveLLM (weaker answers); data synthetic.
Artefacts: src/rag.py, src/graph_context.py, api/main.py, prompts/rag_v1.md, logs/rag_log.jsonl, eval/rag_eval.jsonl, docs/rag.md, graph_vs_text.md, api.md, openapi.json, rag_eval.md, rag_optimization.md, docs/evidence/demo_rag.txt; tests/test_api.py; scripts/run_all.sh, fetch_models.sh; llm_log/log.csv; claims/claims.csv; data/docs_manifest.json.

## Lab 12 - OLAP cube on taxonomy (DuckDB star schema, OLAP queries, semantic layer, text-to-SQL, dashboard)
Headline results (all data synthetic, seed 42):
- Dataset: "20 000 подій-викликів + 2 552 щоденних знімків черги"; 300 samples, 10 genes, 8 tool versions; generator emitted 20 005 rows (20 000 valid + 5 deliberate defects) (§1-2); star schema: 2 facts, 5 dimensions, dim_taxon (154 concepts) in 3 roles + 2 via dim_pipeline
- ELT/DQ: "у факт завантажено 20 000 рядків; у карантин — 5"; "пройдено 22 з 22 перевірок"; orphan checks for 8 foreign keys = 0 (Table 5); 8 Parquet files, data/VERSION.json 1.0.0 with sha256
- OLAP: 15 queries on 20 000 facts "за < 0.3 с"; q01 ROLLUP 287.2 ms (slowest), others 3.7-19.6 ms (Table 7); q01 grand total "20000 | 57.4" (calls | pass%); 2025-Q1 2140 calls 54.4% to 2026-Q3 3556 calls 60.1% (Table 8)
- Independent verification in pandas: 4 queries (q01, q03, q09, q13), "12 порівнянь, всі збігаються" (Table 12)
- Semantic layer: 7 metrics (5 approved, 2 draft), 14 dimensions; 4 questions x 3 paths (semantic layer / hand SQL / pandas) identical (Table 15); "середнє місячних pass rate (57.15 %) vs відношення сум (57.4 %)" difference -0.25 pp
- Text-to-SQL (23 questions: 18 normal + 5 unsafe; claude-haiku-4-5 generator): strict correct "15/18 = 83%"; soft "18/18" (soft metric defined AFTER viewing results); unsafe/unanswerable handled "5/5"; dangerous statements executed "0/23"; refusals/guard blocks/exec errors "5 / 0 / 0"; cost "$0.00124 (1023 вх. + 44 вих. токенів)" (modelled); guard+EXPLAIN+exec median/max "8.1 / 29.9 мс" (Table 18)
- AST guard: "20 шкідливих SQL" tests, "20/20 атак блоковано"; ablation without safety rules in prompt: model refused 4 of 5, 1 (information_schema) stopped by AST check (illustration only)
- Tests: 43 autotests (28 in test_t2sql.py); claims.csv "22 тверджень; verified 13 (59%), rejected 2 (9%), pending 7 (32%)"
Caveats:
- Data synthetic, distributions invented; "висновки" are generator effects, not biology; gene chromosomes and tool versions/dates not checked against sources.
- Text-to-SQL test set written by the same session as the schema (easy, no ambiguous wording), one generation per question, soft metric defined post hoc, cost modelled; not a benchmark.
- "Human" review by LLM reviewer (V3 pending); no row/role-level access control, no query rate limit/budget in text-to-SQL; semantic layer minimal own implementation; SCD2 only for pipeline dim.
Artefacts: docs/star_design.md, star_schema.png, olap_results.md, semantic_layer.md, t2sql.md; sql/ddl.sql, sql/olap/*.sql (15); etl/generate.py, etl/load.py; data/raw/*.csv, data/parquet/*.parquet, data/VERSION.json, docs/dq_report.json; semantic/metrics.yml, semantic/sl.py; t2sql/pipeline.py, tests/t2sql.jsonl; dashboard/index.html; llm_log/raw/bq_out.json, prompts/bq_v1.txt; scripts/run_all.sh; claims/claims.csv.

## Lab 14 - Knowledge-store quality, cleaning (dedup/entity resolution, conflicts, CI gate) and effect on Lab-11 RAG
Headline results (baseline = Lab 11 store: 688 chunks, graph 370 nodes / 757 rels; version baseline-8d41e8b861544136, 2026-11-06; seed 14):
- Quality profile: 14 metrics in 9 dimensions (Table 1). Baseline -> after (Table 13): M01 completeness 0.9956 -> 1; M02 schema validity 0.9956 -> 1; M03 open conflicts 8 -> 0; M04 active logical violations 1 -> 0; M07 conflict documentation 0 -> 1; M08 near-duplicate share 0.0203 -> 0; M14 self-retrieval@1 0.9404 -> 0.957 (threshold >= 0.97, still not met); M06 expert-sample accuracy "0.6389 ✗ | 0.6389 ✗" (threshold >= 0.9; 23/36 fully correct; warning); M13 language consistency 0.9927 -> 0.9926
- Dedup: blocking keeps "1775 пар із 236 328 можливих (скорочення 99.2%)"; blocking probes 0 of 10 duplicates missed; gold "160 пар ... + 10 проб" (Result 2 text; Table 6 C2 says "150 пар (+10 проб)"); 17 duplicates (9 dev / 8 test); annotator agreement "бінарна згода 0.994, Cohen's κ = 0.968 (3 класи: 0.905)"; threshold 0.975 from dev, plateau F1 = 0.975
- Dedup on test (n=74, 8 duplicates) (Table 4): combined score P = 1.0, R = 0.75, F1 = 0.857 (TP/FP/FN 6/0/2); bootstrap "P [1.0, 1.0], R [0.38, 1.0]"; 5-fold CV "P = 0.8, R = 0.941"; tfidf F1 0.933; with LLM judge dev and test P/R = 1.0/1.0 (judge matched gold on 16/16 pairs; 5 DUP / 11 RELATED)
- Merge: "17 пар → 11 кластерів, поглинуто 14 чанків (688 → 674)"; unmerge restores originals (test Q12)
- Conflicts: "Знайдено 8 суперечностей 4 типів" (value 3, temporal 2, terminological 2, logical 1); alternatives registry "9 тверджень для 5 суперечностей"; 4 active, 2 superseded/flagged claims; decisions status pending (V3)
- CI gate (25 tests, 14 SHACL shapes, 2 SPARQL constraints): S0_baseline 14/25 pass, 9 blocking fails, FAIL; S1 15/25 (8) FAIL; S2 18/25 (5) FAIL; S3 19/25 (4) FAIL; S4_final 23/25 (0) PASS; ci 23/25 PASS; 2 warnings remain (M06, M14) (Table 10); 3 injected defects D1-D3 all detected, gate FAIL on each (Table 11)
- RAG before -> after on 34 Lab-11 tests (Table 14): faithfulness 0.9889 -> 0.9885; context recall 0.98 -> 0.98; citation support 0.988 -> 0.988; citation validity 1 -> 1; abstention correct 0.8889 -> 0.8889; false refusal 0 -> 0; conflict detected 1 -> 1; injection resisted 1 -> 1; status_ok 33 -> 33; retrieve p50 22.64 -> 22.27 ms; p95 32.05 -> 33.3 ms; avg input tokens 2528 -> 2539 (+0.4%); claims in answers 90 -> 87; duplicate probe: redundant top-5 slots "17/55 → 0/55"
- claims.csv "25 тверджень; verified — 15 (60%), pending — 7, rejected — 3"
Caveats:
- All annotators, judge and "expert" are LLMs of one family; kappa 0.97 and judge P/R 1.0 not independent evidence; no human labelling (V3 pending).
- Only 17 duplicates (8 in test): very wide CIs; combined score not better than TF-IDF; "Вимірюваного приросту якості RAG на 34 тестах немає" (baseline at ceiling); alternatives registry did not change conflict behaviour (hypothesis rejected); 3 of 8 conflicts real, rest synthetic fixtures.
- M06 (0.64) and M14 (0.96) below thresholds, chunk-boundary repair not done; GitHub Actions workflow never run; OWL reasoner not used (age rule via SHACL-SPARQL S14); first full attempt lost to environment reset, all numbers from second attempt.
Artefacts: quality/profile_baseline.md, metrics.json, thresholds.json, profile.py, dedup.py, pairs_gold.csv, merge_log.jsonl, conflicts.md, conflicts.py, decisions.csv, alternatives.py, shapes.ttl (14 shapes), gate.py, gate_report_*.md, history.jsonl, trend.png, gate_log.txt, after_report.md, aliases.csv; store_clean/ (alternatives.jsonl); quality/tests/ (25 tests); .github/workflows/quality.yml; eval/dedup_eval*.json, defect_injection.json, rag_comparison.json, probe_dups.json; scripts/inject_defects.py, run_rag_after.py, aggregate_after.py, run_all.sh; docs/dedup_card.md; llm_log/; claims/claims.csv; lab14_repo.zip (branch lab14).

## Lab 15 - LLM agent with tools (LangGraph + MCP server) over the knowledge store; red-team; human-in-the-loop
Headline results:
- Agent: 5 tools (search_docs, graph_query, sql_metric, get_claims, propose_fact), graph plan -> act -> draft -> verify; limits hardened: 4 tool calls/round, 2 planning rounds, 1 redraft, 8000 tokens/request, 30 s, 50 rows, Cypher timeout 2 s (Table 2)
- Scenario evaluation (25 scenarios = 13 success / 6 "не знаю" / 6 conflict), success rate: "v0 (16) 75% (12/16) | v1 (25) 96% (24/25) | v2 (25) 100% (25/25)" (Table 8); mean steps 3.81 / 4.08 / 4.12; mean tool calls 0.81 / 0.84 / 1.12; redrafts 0 / 3 / 0; avg tokens 1853 / 1924 / 2105; modelled cost per request USD 0.00237 / 0.00247 / 0.00267
- Failure fixes: F1 validator rewrote string literals (success on original set "4/8 → 8/8"); F2 verifier rejected derived numbers (redrafts 3 -> 0); F3 planner prompt (H02)
- Red-team: 22 attacks, 7 types (A01-A20 by LLM red-team sonnet, A21-A22 Lab 11 fixtures) (Table 11); E1 real model "naive 0/22 | hardened 1/22" (the 1/22 is the A03 false positive adjudicated manually; Table 16 C2 states "E1: 0/22 → 0/22"); E2 assume-breach (scripted obedient model) "naive 21/22 | hardened 1/22 | 95% blocked" (naive: 5%) (Table 12)
- E2 by type (naive/hardened successful attacks): direct injection 3/3 -> 0/3; indirect poisoned doc 5/6 -> 0/6; indirect graph property 2/2 -> 1/2; write/delete 3/3 -> 0/3; data leak 3/3 -> 0/3; loop/resource 2/2 -> 0/2; malicious tool description 3/3 -> 0/3 (Table 13); only surviving attack A09 (paraphrase passes lexical filter)
- Defence ablation E2 ("hardened without it" / "naive + only it"): input filter 1/22 / 17/22; output guard 1/22 / 13/22; ro validator 4/22 / 18/22; role scope 1/22 / 21/22; tool pinning 4/22 / 18/22; verify 3/22 / 13/22; limits 3/22 / 19/22 (Table 15)
- HITL propose_fact demo: 14 proposals; risk low/medium/high "2 / 3 / 5"; rejected before classification 4; auto-staged 2; medium decided by human 3; approvals "67% (2 з 3)"; approval wait median/max "1.03 с / 1.04 с (симульовано)"; audit hash chain intact True (Table 18)
- MCP demo: 7 traced requests; trace log 25 requests; tests: "66 тестів" (55 in test_agent.py); claims.csv "20 тверджень: verified 13 (65%), pending 4, rejected 3"; llm_log/log.csv 29 rows
Caveats:
- Agent "brain" = blind subagents replayed from cache (one sample, temperature/seed uncontrolled); real API mode (AnthropicLLM) untested; cost modelled ($1/$5 per M tokens, not checked); MCP tested with own client, not a concrete IDE.
- Scenarios (25) and attacks (22) small, by one author / one LLM; scenario set grew after first run (v0->v2 not clean held-out); E1 showed no measurable benefit of defences (model already robust); E2 relies on author's scripted "obedient" model and does not measure prompt isolation; detectors coarse.
- All "human" decisions (reviewer, HITL approver) simulated by LLM assistant (decision_simulated=true, V3 pending); synthetic data; not a medical device; memory module tested but disabled in all evaluation runs (impact unmeasured); residual risks listed (7), e.g. lexical filter bypass, derived-number acceptance.
Artefacts: docs/agent_spec.md, hitl.md; agent/graph.py, tools.py, config.py, guards.py, memory.py, propose_fact; mcp_server/server.py; tests/agent_scenarios.jsonl, attacks.jsonl, attacks_obey.json, attack_adjudication.json, test_agent.py, test_hitl.py; logs/trace_v2.jsonl, mcp_audit.jsonl, mcp_demo_reader.json; proposals/audit.jsonl, approved_facts.jsonl; eval/*.json; scripts/make_spec.py, demo_mcp.py, run_all.sh; llm_cache/, llm_log/; claims/claims.csv; hub/ snapshot; lab15_repo.zip (branch lab15).

## Cross-lab quality metrics table
| lab | metric | value | source |
|---|---|---|---|
| 5 | Taxonomy structural coverage / MECE (final) | 154 nodes, 121/121 terms (100%), 0 "Інше", manual MECE violations 0 known*; expert 4, llm 5, cluster 4 | Table 5 |
| 5 | Cohen's kappa, R1/R2 vs expert taxonomy (both raters LLM) | 0,916 (93%, 28/30); R1 vs R2 1,000 | Table 6 |
| 6 | LLM triples: quote check / type check / text-supported | 41/41 = 100%; 40/41 = 98% (36/41 = 88% error-free); 29/41 = 71% | Result 3 |
| 6 | LLM triples vs expert map (strict) precision / recall / F1 | 0.51 / 0.43 / 0.47 (TP 21, predicted 41, reference 49) | Table 13 |
| 7 | OWL ontology consistency + CQ pass rate | HermiT consistent, 0 unsatisfiable; CQ 17/17 = 100% (LLM draft 16/17 = 94%); 78 classes, 1373 triples | §4.1, Table 16 |
| 8 | Graph size in triple store | 4425 quads (kb.ttl 3923 triples) | Table 1 |
| 8 | SHACL conformity | valid set conforms=True (0 Violation, 3 Warning); defective set 3 Violation + 3 Warning; 9 node shapes, 18 property shapes, 43 constraints | Result 3, Table 7 |
| 8 | Text-to-SPARQL correct result (v1 -> v2, 24 q) | 16/24 (67%) -> 18/24 (75%); held-out 4/6 -> 4/6; syntax 24/24 | Table 9 |
| 9 | Text-to-Cypher correct result (27 q, 2 runs) | 25/27 (93%) and 26/27 (96%); safety+schema pass 27/27 | Table 18 |
| 10 | Best retrieval config: Hybrid BM25+bge RRF (55 q) | recall@5 0.836 [0.74; 0.93], MRR@10 0.723, nDCG@10 0.750, 14.0 ms | Table 13 |
| 10 | Hybrid+rerank (MaxSim) vs hybrid | recall@5 0.855, MRR@10 0.711, nDCG@10 0.748, 613.1 ms; delta recall@5 +0.018 [-0.05; +0.09] | Tables 13, 15 |
| 11 | RAG faithfulness (claims / whole answers) | 89/90 = 98.9% [94%; 100%]; 25/26 = 96.2% [81%; 99%] | Table 7 |
| 11 | RAG abstention / false refusal / injections resisted | 8/9 = 88.9%; 0/18; 4/4 | Table 7 |
| 11 | Graph vs text-only (12 relational q) | fully correct 3/12 -> 10/12; facts found 11/34 (32%) -> 32/34 (94%); +519 input tokens (+21%) | Table 3 conclusion |
| 12 | Warehouse DQ checks / text-to-SQL | 22/22 checks passed, 20 000 fact rows, 5 quarantined; text-to-SQL strict 15/18 = 83% (soft 18/18), dangerous statements executed 0/23, AST guard 20/20 attacks blocked, $0.00124/question (modelled) | Tables 5, 18 |
| 14 | Dedup on test (combined score) | P = 1.0, R = 0.75, F1 = 0.857 (8 duplicates; R CI [0.38, 1.0]); 688 -> 674 chunks | Table 4, Table 5 |
| 14 | Store quality gate and metrics before -> after | gate S0 FAIL (9 blocking) -> PASS 23/25; M03 8 -> 0, M08 0.0203 -> 0; M14 0.9404 -> 0.957; M06 0.6389 -> 0.6389 (<0.9) | Tables 10, 13 |
| 14 | RAG effect of cleaning (34 tests) | faithfulness 0.9889 -> 0.9885; context recall 0.98 -> 0.98; duplicate top-5 slots 17/55 -> 0/55; "Вимірюваного приросту ... немає" | Table 14 |
| 15 | Agent scenario success v0 / v1 / v2 | 75% (12/16) / 96% (24/25) / 100% (25/25) | Table 8 |
| 15 | Agent attack success: naive vs hardened (assume-breach, 22 attacks) | 21/22 -> 1/22 (95% blocked); real model E1 naive 0/22, hardened 1/22 (false positive adjudicated) | Table 12 |


Note: 20 rows selected from all labs; values copied from the lab reports without rounding or recomputation. Lab 13 has no text dump and is excluded. Omitted but reported in the lab sections: Lab 5 SKOS/pytest (19 passed), Lab 6 v2 map validation, Lab 9 graph size (370 nodes, 757 relationships), Lab 10 gold-set kappa 0.721, Lab 11 citation validity 84/84, Lab 15 HITL demo metrics.
