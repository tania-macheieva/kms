# Entity resolution (de-duplication) of chunks — method card

**Gold set.** 160 pairs (stratified by score band) + 10 blocking-recall probes; two blind LLM annotators (labels DUP / RELATED / DISTINCT), binary agreement 0.994, Cohen's kappa 0.968 (3-class 0.905); 1 disagreement adjudicated by the assistant. Duplicates: 9 dev / 8 test. Split: dev 76 / test 74 (stratified by label, seed 14).
**Blocking.** Inverted index on word 5-shingles, pair if >= 2 shared: 1775 candidate pairs out of 236328 (99.2% reduction). Probes (highest-embedding-similarity pairs not produced by blocking): 0 of 10 are duplicates, i.e. no blocking miss was found.
**Comparison types.** string (rapidfuzz token_set_ratio, ratio), sparse (TF-IDF cosine), dense (bge embedding cosine), attributes (same doc, section tail, length ratio, sensitivity). Score = .35 tfidf + .25 emb + .25 fuzz + .15 ratio, x0.85 if length ratio < 0.5.
**Threshold** tuned on dev: centre of the F1 plateau = **0.975** (plateau 0.975–0.975). Test (n=74, 8 duplicates): P = 1.0, R = 0.75, F1 = 0.857; bootstrap 95% CI P [1.0, 1.0], R [0.38, 1.0] — wide, because there are only 8 positives. 5-fold CV over all pairs: P 0.8, R 0.941.

| feature (threshold tuned on dev) | test P | test R | test F1 |
|---|---|---|---|
| score (0.975) | 1.0 | 0.75 | 0.857 |
| tfidf (0.968) | 1.0 | 0.875 | 0.933 |
| emb (0.95) | 0.333 | 0.5 | 0.4 |
| fuzz (0.998) | 0.636 | 0.875 | 0.737 |
| ratio (0.975) | 1.0 | 1.0 | 1.0 |

The combined score is **not better** than the best single feature on this small test set; it is kept because it is more stable in the CV and uses all comparison types.

**Errors at the score threshold:** PR016 FP (score 0.9932, gold RELATED, dev); PR091 FN (score 0.9741, gold DUP, test); PR128 FN (score 0.9649, gold DUP, test).
**Borderline zone** (|score − th| <= 0.08): all candidate pairs of the store that fall into it and are not identical after normalisation (16 pairs) were judged by a third LLM call that returned a label and an explanation (5 DUP / 11 RELATED). The judge agrees with the gold labels on 16 of 16 judged pairs that are in the gold set (the judge was blind to the gold; annotators and judge are the same model family, so this is not independent evidence).
**Full rule on the gold set** (identical text → DUP; score >= th + band → DUP; borderline → judge; different sensitivity → never): dev P/R = 1.0/1.0, test P/R = 1.0/1.0; without the judge test R = 0.75.
**Merge.** 17 pairs → 11 clusters, 14 chunks absorbed (688 → 674); rule split {'exact_text': 12, 'judge': 5}. Canonical choice: public > internal > restricted, then longest, then smallest id. The canonical chunk keeps the full records of absorbed chunks in `merged_from` (doc, offsets, text, metadata); `quality/merge_log.jsonl` records cluster, rule and minimal pair score. **Unmerge** (`dedup.unmerge`) restores the exact original records: one cluster — True, all clusters — True (tested, Q12).
**Caveat.** Most merged clusters are boilerplate shared by nf-core/sarek and nf-core/raredisease pages; after the merge a sarek question is answered from the canonical raredisease chunk (provenance of the sarek span stays in `merged_from`). If a pipeline-specific answer is required, run `unmerge` for that cluster.
