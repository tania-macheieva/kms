# OLAP queries (R3)

15 queries in `sql/olap/*.sql`, run on the star schema in DuckDB (`python3 scripts/run_olap.py`; this file: `python3 scripts/make_doc_olap.py`). Each query has the business question, the SQL, the result and an interpretation. **The data are synthetic** (`etl/generate.py`), so the interpretations describe what the generator built in; they are not medical findings.

Constructs used: ROLLUP (q01, q02, q11), CUBE (q03), GROUPING SETS (q04), slice (q05), dice (q06), PIVOT (q07), window functions – running total (q08), DENSE_RANK (q09), moving average (q10), drill-down class → subclass along the taxonomy (q11, q12, q15), SCD2 (q13, q15), semi-additive measure (q14).

## q01_rollup_time

**Question.** BQ02 How does the number of variant calls and the share of passed calls change by year and quarter (with subtotals)?

**Operation.** ROLLUP (year > quarter)

```sql
-- question: BQ02 How does the number of variant calls and the share of passed calls change by year and quarter (with subtotals)?
-- operation: ROLLUP (year > quarter)
SELECT d.year, d.quarter, count(*) AS calls, sum(f.is_pass) AS passed, round(100.0 * sum(f.is_pass) / count(*), 1) AS pass_pct,
       grouping(d.year) AS g_year, grouping(d.quarter) AS g_quarter
FROM fact_variant_call f JOIN dim_date d USING (date_key)
GROUP BY ROLLUP (d.year, d.quarter) ORDER BY d.year NULLS LAST, d.quarter NULLS LAST;
```

**Result** (10 rows, 287.2 ms on 20 000 facts)

| year | quarter | calls | passed | pass_pct | g_year | g_quarter |
|---|---|---|---|---|---|---|
| 2025 | 1 | 2140 | 1165 | 54.4 | 0 | 0 |
| 2025 | 2 | 2435 | 1349 | 55.4 | 0 | 0 |
| 2025 | 3 | 2649 | 1569 | 59.2 | 0 | 0 |
| 2025 | 4 | 2788 | 1562 | 56 | 0 | 0 |
| 2025 |  | 10012 | 5645 | 56.4 | 0 | 1 |
| 2026 | 1 | 3116 | 1784 | 57.3 | 0 | 0 |
| 2026 | 2 | 3316 | 1906 | 57.5 | 0 | 0 |
| 2026 | 3 | 3556 | 2136 | 60.1 | 0 | 0 |
| 2026 |  | 9988 | 5826 | 58.3 | 0 | 1 |
|  |  | 20000 | 11471 | 57.4 | 1 | 1 |

**Interpretation.** Activity grows: 2 140 calls in 2025-Q1 → 3 556 in 2026-Q3 (the generator ramps volume up over time); 2026 has 9 988 calls in three quarters against 10 012 in four quarters of 2025. Pass rate rises from 56.4% (2025) to 58.3% (2026) – partly the effect of newer tool versions (see q13). ROLLUP gives year subtotals and the grand total (20 000 calls, 57.4% passed) in one pass; `grouping()` marks the subtotal rows.

## q02_rollup_gene_chromosome

**Question.** BQ01 How many calls passed in each gene, and what share of the chromosome / of all calls does each gene give? (hierarchy gene -> chromosome)

**Operation.** ROLLUP (chromosome > gene)

```sql
-- question: BQ01 How many calls passed in each gene, and what share of the chromosome / of all calls does each gene give? (hierarchy gene -> chromosome)
-- operation: ROLLUP (chromosome > gene)
SELECT g.chromosome, g.gene_symbol, count(*) AS calls, sum(f.is_pass) AS passed, round(100.0 * sum(f.is_pass) / count(*), 1) AS pass_pct,
       grouping(g.chromosome) AS g_chr, grouping(g.gene_symbol) AS g_gene
FROM fact_variant_call f JOIN dim_gene g USING (gene_key)
GROUP BY ROLLUP (g.chromosome, g.gene_symbol) ORDER BY try_cast(g.chromosome AS INT) NULLS LAST, grouping(g.gene_symbol), calls DESC;
```

**Result** (20 rows, 8.7 ms on 20 000 facts)

| chromosome | gene_symbol | calls | passed | pass_pct | g_chr | g_gene |
|---|---|---|---|---|---|---|
| 2 | MSH2 | 1161 | 669 | 57.6 | 0 | 0 |
| 2 |  | 1161 | 669 | 57.6 | 0 | 1 |
| 3 | MLH1 | 1217 | 699 | 57.4 | 0 | 0 |
| 3 |  | 1217 | 699 | 57.4 | 0 | 1 |
| 5 | APC | 1410 | 821 | 58.2 | 0 | 0 |
| 5 |  | 1410 | 821 | 58.2 | 0 | 1 |
| 10 | PTEN | 981 | 532 | 54.2 | 0 | 0 |
| 10 |  | 981 | 532 | 54.2 | 0 | 1 |
| 11 | ATM | 2034 | 1182 | 58.1 | 0 | 0 |
| 11 |  | 2034 | 1182 | 58.1 | 0 | 1 |
| 13 | BRCA2 | 3575 | 2033 | 56.9 | 0 | 0 |
| 13 |  | 3575 | 2033 | 56.9 | 0 | 1 |
| 16 | PALB2 | 1586 | 921 | 58.1 | 0 | 0 |
| 16 |  | 1586 | 921 | 58.1 | 0 | 1 |
| 17 | BRCA1 | 3972 | 2267 | 57.1 | 0 | 0 |
| 17 | TP53 | 2446 | 1403 | 57.4 | 0 | 0 |

(first 16 of 20 rows)

**Interpretation.** BRCA1 (3 972) and BRCA2 (3 575) dominate; chromosome 17 holds two genes (BRCA1, TP53) and is the largest chromosome total (6 418 calls). Pass rates per gene are close (54–58%); PTEN is lowest (54.2%) but with only 981 calls the gap is within noise. Rows with `g_gene = 1` are chromosome subtotals – for one-gene chromosomes they repeat the gene row.

## q03_cube_cohort_tissue

**Question.** BQ09 Which cohort / tissue combinations have the highest share of passed calls? (all subtotals)

**Operation.** CUBE (cohort, tissue) with GROUPING()

```sql
-- question: BQ09 Which cohort / tissue combinations have the highest share of passed calls? (all subtotals)
-- operation: CUBE (cohort, tissue) with GROUPING()
SELECT coalesce(s.cohort, 'ALL') AS cohort, coalesce(s.tissue, 'ALL') AS tissue, count(*) AS calls, round(100.0 * sum(f.is_pass) / count(*), 1) AS pass_pct
FROM fact_variant_call f JOIN dim_sample s USING (sample_key)
GROUP BY CUBE (s.cohort, s.tissue) ORDER BY grouping(s.cohort), grouping(s.tissue), s.cohort, s.tissue;
```

**Result** (16 rows, 9.3 ms on 20 000 facts)

| cohort | tissue | calls | pass_pct |
|---|---|---|---|
| Control | blood | 3143 | 57.8 |
| Control | saliva | 823 | 55.9 |
| Control | tumor | 1933 | 55.6 |
| HBOC | blood | 5142 | 57.3 |
| HBOC | saliva | 990 | 57.7 |
| HBOC | tumor | 2985 | 57.4 |
| Lynch | blood | 2378 | 57.8 |
| Lynch | saliva | 955 | 58.6 |
| Lynch | tumor | 1651 | 57.8 |
| Control | ALL | 5899 | 56.8 |
| HBOC | ALL | 9117 | 57.4 |
| Lynch | ALL | 4984 | 57.9 |
| ALL | blood | 10663 | 57.6 |
| ALL | saliva | 2768 | 57.5 |
| ALL | tumor | 6569 | 56.9 |
| ALL | ALL | 20000 | 57.4 |

**Interpretation.** CUBE returns all 3×3 cells, 3+3 margins and the total (16 rows). The largest cell is HBOC/blood (5 142 calls); pass rates differ by less than 3 percentage points between cells (55.6–58.6%), i.e. cohort and tissue do not change call quality in this dataset (the generator does not make them matter).

## q04_grouping_sets

**Question.** What is the pass rate per pipeline family, per variant type, and per family x variant type, in ONE pass over the fact?

**Operation.** GROUPING SETS (taxonomy role-playing: variant_type_key -> dim_taxon)

```sql
-- question: What is the pass rate per pipeline family, per variant type, and per family x variant type, in ONE pass over the fact?
-- operation: GROUPING SETS (taxonomy role-playing: variant_type_key -> dim_taxon)
SELECT coalesce(p.family, 'ALL') AS family, coalesce(t.label, 'ALL') AS variant_type, count(*) AS calls, round(100.0 * sum(f.is_pass) / count(*), 1) AS pass_pct
FROM fact_variant_call f JOIN dim_pipeline p USING (pipeline_key) JOIN dim_taxon t ON t.taxon_key = f.variant_type_key
GROUP BY GROUPING SETS ((p.family), (t.label), (p.family, t.label)) ORDER BY grouping(p.family) , grouping(t.label), 1, 2;
```

**Result** (24 rows, 6.9 ms on 20 000 facts)

| family | variant_type | calls | pass_pct |
|---|---|---|---|
| BCFTOOLS | copy number variation | 118 | 50.8 |
| BCFTOOLS | insertion-deletion | 512 | 51 |
| BCFTOOLS | single nucleotide polymorphism | 3183 | 48.9 |
| BCFTOOLS | structural variant | 192 | 38.5 |
| DEEPVARIANT | copy number variation | 144 | 65.3 |
| DEEPVARIANT | insertion-deletion | 671 | 65.9 |
| DEEPVARIANT | single nucleotide polymorphism | 4006 | 65.4 |
| DEEPVARIANT | structural variant | 206 | 48.1 |
| GATK | copy number variation | 249 | 53.8 |
| GATK | insertion-deletion | 982 | 56.9 |
| GATK | single nucleotide polymorphism | 6339 | 57.5 |
| GATK | structural variant | 349 | 43 |
| STRELKA | copy number variation | 93 | 57 |
| STRELKA | insertion-deletion | 359 | 60.4 |
| STRELKA | single nucleotide polymorphism | 2475 | 58.8 |
| STRELKA | structural variant | 122 | 42.6 |

(first 16 of 24 rows)

**Interpretation.** One scan gives three granularities. The pass rate depends on the pipeline: DeepVariant 64.7% > STRELKA 58.3% > GATK 56.7% > bcftools 48.8%; and on the variant type: structural variants pass far less often (43.2%) than SNPs (58.0%) in every family (e.g. bcftools 38.5%, DeepVariant 48.1%).

## q05_slice_weekend

**Question.** BQ11 In 2026, do weekend calls need more manual review than weekday calls? (slice year = 2026)

**Operation.** SLICE (one value of the date dimension) + group by day of week

```sql
-- question: BQ11 In 2026, do weekend calls need more manual review than weekday calls? (slice year = 2026)
-- operation: SLICE (one value of the date dimension) + group by day of week
SELECT d.day_of_week, d.is_weekend, count(*) AS calls, round(sum(f.review_minutes), 1) AS review_min_total, round(sum(f.review_minutes) / count(*), 2) AS review_min_per_call
FROM fact_variant_call f JOIN dim_date d USING (date_key) WHERE d.year = 2026
GROUP BY d.day_of_week, d.is_weekend ORDER BY d.day_of_week;
```

**Result** (7 rows, 3.7 ms on 20 000 facts)

| day_of_week | is_weekend | calls | review_min_total | review_min_per_call |
|---|---|---|---|---|
| 1 | False | 1379 | 4701 | 3.4 |
| 2 | False | 1464 | 5270 | 3.6 |
| 3 | False | 1413 | 4919.2 | 3.5 |
| 4 | False | 1423 | 5424.9 | 3.8 |
| 5 | False | 1439 | 5332.5 | 3.7 |
| 6 | True | 1478 | 5475.5 | 3.7 |
| 7 | True | 1392 | 5097.1 | 3.7 |

**Interpretation.** Slice on year 2026: review time per call is 3.41–3.81 min on weekdays and 3.70 / 3.66 on Saturday/Sunday – weekends are not systematically slower (the highest value is Thursday, 3.81). With ~1 400 calls per day-of-week the differences are noise.

## q06_dice_pathogenic

**Question.** In the HBOC and Lynch cohorts, blood and tumor samples only: how many pathogenic calls per gene?

**Operation.** DICE (sub-cube on 3 dimensions: sample, taxon role significance, tissue)

```sql
-- question: In the HBOC and Lynch cohorts, blood and tumor samples only: how many pathogenic calls per gene?
-- operation: DICE (sub-cube on 3 dimensions: sample, taxon role significance, tissue)
SELECT g.gene_symbol, count(*) AS pathogenic_calls, count(DISTINCT f.sample_key) AS samples
FROM fact_variant_call f JOIN dim_sample s USING (sample_key) JOIN dim_gene g USING (gene_key) JOIN dim_taxon sg ON sg.taxon_key = f.significance_key
WHERE s.cohort IN ('HBOC', 'Lynch') AND s.tissue IN ('blood', 'tumor') AND sg.label = 'pathogenic variant'
GROUP BY g.gene_symbol ORDER BY pathogenic_calls DESC;
```

**Result** (10 rows, 5.4 ms on 20 000 facts)

| gene_symbol | pathogenic_calls | samples |
|---|---|---|
| BRCA1 | 498 | 172 |
| BRCA2 | 483 | 170 |
| TP53 | 291 | 139 |
| ATM | 247 | 138 |
| CHEK2 | 205 | 125 |
| PALB2 | 199 | 114 |
| APC | 174 | 114 |
| MLH1 | 159 | 110 |
| MSH2 | 127 | 92 |
| PTEN | 115 | 85 |

**Interpretation.** The sub-cube HBOC+Lynch × blood+tumor × pathogenic: BRCA1 has the most pathogenic calls (498 in 172 samples), then BRCA2 (483) and TP53 (291); PTEN is last (115). Several calls fall into the same sample, so calls ≠ samples.

## q07_pivot_significance_type

**Question.** BQ04 How are clinical-significance classes distributed across variant types?

**Operation.** PIVOT (rows = variant type, columns = significance)

```sql
-- question: BQ04 How are clinical-significance classes distributed across variant types?
-- operation: PIVOT (rows = variant type, columns = significance)
PIVOT (SELECT vt.label AS variant_type, sg.label AS significance, f.call_count
       FROM fact_variant_call f JOIN dim_taxon vt ON vt.taxon_key = f.variant_type_key JOIN dim_taxon sg ON sg.taxon_key = f.significance_key)
ON significance USING sum(call_count) GROUP BY variant_type ORDER BY variant_type;
```

**Result** (4 rows, 6.9 ms on 20 000 facts)

| variant_type | benign variant | pathogenic variant | variant of uncertain significance |
|---|---|---|---|
| copy number variation | 326 | 102 | 176 |
| insertion-deletion | 1392 | 390 | 742 |
| single nucleotide polymorphism | 8782 | 2477 | 4744 |
| structural variant | 502 | 123 | 244 |

**Interpretation.** Rows = variant type, columns = significance. Benign dominates every row (e.g. 8 782 of 16 003 SNPs); the share of pathogenic calls is similar across types (15.5% for SNPs and indels, 16.9% for CNV, 14.2% for SVs), so the type does not predict significance in this synthetic dataset.

## q08_window_cumulative

**Question.** How many calls has each pipeline family accumulated by the end of each quarter?

**Operation.** WINDOW running total (SUM() OVER (PARTITION BY family ORDER BY quarter))

```sql
-- question: How many calls has each pipeline family accumulated by the end of each quarter?
-- operation: WINDOW running total (SUM() OVER (PARTITION BY family ORDER BY quarter))
WITH q AS (SELECT p.family, d.year, d.quarter, count(*) AS calls FROM fact_variant_call f JOIN dim_pipeline p USING (pipeline_key) JOIN dim_date d USING (date_key) GROUP BY ALL)
SELECT family, year, quarter, calls, sum(calls) OVER (PARTITION BY family ORDER BY year, quarter) AS cumulative_calls
FROM q ORDER BY family, year, quarter;
```

**Result** (28 rows, 5.5 ms on 20 000 facts)

| family | year | quarter | calls | cumulative_calls |
|---|---|---|---|---|
| BCFTOOLS | 2025 | 1 | 448 | 448 |
| BCFTOOLS | 2025 | 2 | 498 | 946 |
| BCFTOOLS | 2025 | 3 | 509 | 1455 |
| BCFTOOLS | 2025 | 4 | 548 | 2003 |
| BCFTOOLS | 2026 | 1 | 642 | 2645 |
| BCFTOOLS | 2026 | 2 | 678 | 3323 |
| BCFTOOLS | 2026 | 3 | 682 | 4005 |
| DEEPVARIANT | 2025 | 1 | 542 | 542 |
| DEEPVARIANT | 2025 | 2 | 597 | 1139 |
| DEEPVARIANT | 2025 | 3 | 681 | 1820 |
| DEEPVARIANT | 2025 | 4 | 702 | 2522 |
| DEEPVARIANT | 2026 | 1 | 809 | 3331 |
| DEEPVARIANT | 2026 | 2 | 833 | 4164 |
| DEEPVARIANT | 2026 | 3 | 863 | 5027 |
| GATK | 2025 | 1 | 835 | 835 |
| GATK | 2025 | 2 | 974 | 1809 |

(first 16 of 28 rows)

**Interpretation.** Running totals per family at the end of 2026-Q3: GATK 7 919, DeepVariant 5 027, bcftools 4 005, Strelka2 3 049 calls – these add up to the 20 000 total. The curve is steeper in 2026 because call volume grows.

## q09_window_rank_samples

**Question.** BQ05 Which 3 samples consumed the most review minutes inside each QC status group?

**Operation.** WINDOW RANK (DENSE_RANK() OVER (PARTITION BY qc_status ORDER BY minutes DESC))

```sql
-- question: BQ05 Which 3 samples consumed the most review minutes inside each QC status group?
-- operation: WINDOW RANK (DENSE_RANK() OVER (PARTITION BY qc_status ORDER BY minutes DESC))
WITH m AS (SELECT s.qc_status, s.sample_code, s.cohort, round(sum(f.review_minutes), 1) AS review_min, count(*) AS calls FROM fact_variant_call f JOIN dim_sample s USING (sample_key) GROUP BY ALL),
     r AS (SELECT *, dense_rank() OVER (PARTITION BY qc_status ORDER BY review_min DESC) AS rnk FROM m)
SELECT * FROM r WHERE rnk <= 3 ORDER BY qc_status, rnk, sample_code;
```

**Result** (6 rows, 5.2 ms on 20 000 facts)

| qc_status | sample_code | cohort | review_min | calls | rnk |
|---|---|---|---|---|---|
| pass | S0199 | HBOC | 509.1 | 76 | 1 |
| pass | S0050 | HBOC | 495.5 | 79 | 2 |
| pass | S0183 | Lynch | 466.9 | 85 | 3 |
| recheck | S0144 | Lynch | 392.2 | 78 | 1 |
| recheck | S0081 | Lynch | 382 | 82 | 2 |
| recheck | S0284 | HBOC | 361 | 76 | 3 |

**Interpretation.** DENSE_RANK inside the QC groups: in the `pass` group sample S0199 (HBOC) consumed the most review time (509.1 min over 76 calls), in the `recheck` group S0144 (Lynch, 392.2 min). Top-3 lists differ by ranks, ties would share a rank.

## q10_moving_average_qual

**Question.** BQ07-like How does the average call quality move month by month per family (3-month moving average smooths the noise)?

**Operation.** WINDOW moving average (AVG() OVER (ROWS BETWEEN 2 PRECEDING AND CURRENT ROW)); non-additive measure -> avg of calls, not avg of averages

```sql
-- question: BQ07-like How does the average call quality move month by month per family (3-month moving average smooths the noise)?
-- operation: WINDOW moving average (AVG() OVER (ROWS BETWEEN 2 PRECEDING AND CURRENT ROW)); non-additive measure -> avg of calls, not avg of averages
WITH m AS (SELECT p.family, d.year, d.month, round(avg(f.qual), 2) AS avg_qual, count(*) AS calls FROM fact_variant_call f JOIN dim_pipeline p USING (pipeline_key) JOIN dim_date d USING (date_key) GROUP BY ALL)
SELECT family, year, month, avg_qual, round(avg(avg_qual) OVER (PARTITION BY family ORDER BY year, month ROWS BETWEEN 2 PRECEDING AND CURRENT ROW), 2) AS moving_avg_3m
FROM m WHERE family IN ('GATK', 'DEEPVARIANT') ORDER BY family, year, month;
```

**Result** (42 rows, 6.2 ms on 20 000 facts)

| family | year | month | avg_qual | moving_avg_3m |
|---|---|---|---|---|
| DEEPVARIANT | 2025 | 1 | 40.8 | 40.8 |
| DEEPVARIANT | 2025 | 2 | 38.7 | 39.7 |
| DEEPVARIANT | 2025 | 3 | 40.2 | 39.9 |
| DEEPVARIANT | 2025 | 4 | 39.8 | 39.6 |
| DEEPVARIANT | 2025 | 5 | 38.5 | 39.5 |
| DEEPVARIANT | 2025 | 6 | 40 | 39.5 |
| DEEPVARIANT | 2025 | 7 | 38.6 | 39.1 |
| DEEPVARIANT | 2025 | 8 | 40.7 | 39.8 |
| DEEPVARIANT | 2025 | 9 | 39.7 | 39.7 |
| DEEPVARIANT | 2025 | 10 | 40.8 | 40.4 |
| DEEPVARIANT | 2025 | 11 | 39.7 | 40.1 |
| DEEPVARIANT | 2025 | 12 | 39.6 | 40.0 |
| DEEPVARIANT | 2026 | 1 | 40.6 | 40.0 |
| DEEPVARIANT | 2026 | 2 | 38.4 | 39.5 |
| DEEPVARIANT | 2026 | 3 | 38.5 | 39.2 |
| DEEPVARIANT | 2026 | 4 | 38.4 | 38.4 |

(first 16 of 42 rows)

**Interpretation.** Monthly average quality of GATK fluctuates 31.4–39.3, the 3-month moving average (32.9–37.5) shows a steady rise after the 4.5 (2025-07) and 4.6 (2026-03) releases; DeepVariant is flat around 39–41. The average is taken over calls, not as an average of monthly averages, because quality is non-additive.

## q11_drilldown_taxonomy_class

**Question.** BQ10 DRILL-DOWN along the taxonomy path (role = variant type): 'Genetic variation' > 'genetic variant' > leaf concept - calls and pass rate at every level

**Operation.** ROLLUP over the taxonomy hierarchy columns of dim_taxon (top_label > facet_label > label)

```sql
-- question: BQ10 DRILL-DOWN along the taxonomy path (role = variant type): 'Genetic variation' > 'genetic variant' > leaf concept - calls and pass rate at every level
-- operation: ROLLUP over the taxonomy hierarchy columns of dim_taxon (top_label > facet_label > label)
SELECT t.top_label, t.facet_label, t.label, count(*) AS calls, round(100.0 * sum(f.is_pass) / count(*), 1) AS pass_pct,
       grouping(t.top_label) + grouping(t.facet_label) + grouping(t.label) AS rollup_level
FROM fact_variant_call f JOIN dim_taxon t ON t.taxon_key = f.variant_type_key
GROUP BY ROLLUP (t.top_label, t.facet_label, t.label) ORDER BY rollup_level DESC, calls DESC;
```

**Result** (7 rows, 6.2 ms on 20 000 facts)

| top_label | facet_label | label | calls | pass_pct | rollup_level |
|---|---|---|---|---|---|
|  |  |  | 20000 | 57.4 | 3 |
| Genetic variation |  |  | 20000 | 57.4 | 2 |
| Genetic variation | genetic variant |  | 20000 | 57.4 | 1 |
| Genetic variation | genetic variant | single nucleotide polymorphism | 16003 | 58 | 0 |
| Genetic variation | genetic variant | insertion-deletion | 2524 | 58.6 | 0 |
| Genetic variation | genetic variant | structural variant | 869 | 43.2 | 0 |
| Genetic variation | genetic variant | copy number variation | 604 | 56.5 | 0 |

**Interpretation.** Drill-down along the taxonomy path stored in dim_taxon: level 3 = whole fact (20 000), level 2 = 'Genetic variation', level 1 = 'genetic variant', level 0 = leaf concepts. The totals are equal on the way up (all calls have a variant type), SNPs are 80% of calls.

## q12_drilldown_taxonomy_subclass

**Question.** BQ10 DRILL-DOWN step 2 (subclass level): inside the class 'genetic variant', calls and pass rate per leaf concept with its IRI

**Operation.** drill-down class -> subclass (WHERE facet_label = ... , GROUP BY leaf concept)

```sql
-- question: BQ10 DRILL-DOWN step 2 (subclass level): inside the class 'genetic variant', calls and pass rate per leaf concept with its IRI
-- operation: drill-down class -> subclass (WHERE facet_label = ... , GROUP BY leaf concept)
SELECT t.facet_label AS class, t.label AS subclass, t.iri, count(*) AS calls, round(100.0 * sum(f.is_pass) / count(*), 1) AS pass_pct, round(avg(f.qual), 1) AS avg_qual
FROM fact_variant_call f JOIN dim_taxon t ON t.taxon_key = f.variant_type_key WHERE t.facet_label = 'genetic variant'
GROUP BY ALL ORDER BY calls DESC;
```

**Result** (4 rows, 19.6 ms on 20 000 facts)

| class | subclass | iri | calls | pass_pct | avg_qual |
|---|---|---|---|---|---|
| genetic variant | single nucleotide polymorphism | http://example.org/knowledge-hub/biomed/C023 | 16003 | 58 | 36.5 |
| genetic variant | insertion-deletion | http://example.org/knowledge-hub/biomed/C024 | 2524 | 58.6 | 36.3 |
| genetic variant | structural variant | http://example.org/knowledge-hub/biomed/C025 | 869 | 43.2 | 30.7 |
| genetic variant | copy number variation | http://example.org/knowledge-hub/biomed/C026 | 604 | 56.5 | 36.3 |

**Interpretation.** Subclass level with the IRI of every concept (C023–C026) – the business key that links the warehouse to the Lab-5 SKOS taxonomy. Structural variants have the lowest average quality (30.7) and pass rate (43.2%), the other classes are close to 36 and 56–59%.

## q13_scd2_versions

**Question.** BQ06 Did upgrading tool versions change average quality and read depth? (SCD2: every version is its own dim_pipeline row)

**Operation.** group by SCD2 attributes; non-additive measures -> AVG over calls

```sql
-- question: BQ06 Did upgrading tool versions change average quality and read depth? (SCD2: every version is its own dim_pipeline row)
-- operation: group by SCD2 attributes; non-additive measures -> AVG over calls
SELECT p.family, p.version, p.valid_from, p.valid_to, count(*) AS calls, round(avg(f.qual), 1) AS avg_qual, round(avg(f.read_depth), 1) AS avg_depth, round(100.0 * sum(f.is_pass) / count(*), 1) AS pass_pct
FROM fact_variant_call f JOIN dim_pipeline p USING (pipeline_key) GROUP BY ALL ORDER BY p.family, p.valid_from;
```

**Result** (8 rows, 5.7 ms on 20 000 facts)

| family | version | valid_from | valid_to | calls | avg_qual | avg_depth | pass_pct |
|---|---|---|---|---|---|---|---|
| BCFTOOLS | 1.18 | 2025-01-01T00:00:00.000 | 2025-09-30T00:00:00.000 | 1455 | 31.7 | 44.4 | 48.2 |
| BCFTOOLS | 1.20 | 2025-10-01T00:00:00.000 | 9999-12-31T00:00:00.000 | 2550 | 32.6 | 44.4 | 49.1 |
| DEEPVARIANT | 1.6.1 | 2025-01-01T00:00:00.000 | 2026-01-14T00:00:00.000 | 2650 | 39.9 | 44.8 | 65 |
| DEEPVARIANT | 1.8.0 | 2026-01-15T00:00:00.000 | 9999-12-31T00:00:00.000 | 2377 | 39.1 | 44.7 | 64.5 |
| GATK | 4.4.0.0 | 2025-01-01T00:00:00.000 | 2025-06-30T00:00:00.000 | 1809 | 33.3 | 43.9 | 50.5 |
| GATK | 4.5.0.0 | 2025-07-01T00:00:00.000 | 2026-02-28T00:00:00.000 | 2869 | 36.3 | 44.5 | 57.7 |
| GATK | 4.6.0.0 | 2026-03-01T00:00:00.000 | 9999-12-31T00:00:00.000 | 3241 | 37 | 44 | 59.2 |
| STRELKA | 2.9.10 | 2025-01-01T00:00:00.000 | 9999-12-31T00:00:00.000 | 3049 | 36.8 | 44.9 | 58.3 |

**Interpretation.** SCD2 makes tool upgrades visible: GATK average quality 33.3 (4.4.0.0) → 36.3 (4.5.0.0) → 37.0 (4.6.0.0) and pass rate 50.5% → 57.7% → 59.2%; bcftools 1.20 is slightly better than 1.18 (49.1% vs 48.2%); DeepVariant 1.8.0 is not better than 1.6.1 (64.5% vs 65.0%). Each call is attached to the version valid on its date, so a rewrite of history is impossible.

## q14_semi_additive_backlog

**Question.** BQ08 Monthly CPU hours (additive) and queue backlog (semi-additive: summed across families within a day, then AVERAGED over days) per family

**Operation.** correct aggregation of a semi-additive measure from the snapshot fact

```sql
-- question: BQ08 Monthly CPU hours (additive) and queue backlog (semi-additive: summed across families within a day, then AVERAGED over days) per family
-- operation: correct aggregation of a semi-additive measure from the snapshot fact
WITH day_fam AS (SELECT d.year, d.month, p.family, f.date_key, f.cpu_hours, f.queue_backlog FROM fact_pipeline_day f JOIN dim_pipeline p USING (pipeline_key) JOIN dim_date d USING (date_key))
SELECT year, month, round(sum(cpu_hours), 1) AS cpu_hours_all, round(sum(queue_backlog) / count(DISTINCT date_key), 1) AS avg_daily_backlog_all_families
FROM day_fam GROUP BY ALL ORDER BY year, month;
```

**Result** (21 rows, 5.9 ms on 20 000 facts)

| year | month | cpu_hours_all | avg_daily_backlog_all_families |
|---|---|---|---|
| 2025 | 1 | 1636.6 | 174.9 |
| 2025 | 2 | 1338.8 | 191.1 |
| 2025 | 3 | 1496.7 | 198.5 |
| 2025 | 4 | 1583.5 | 210 |
| 2025 | 5 | 1352.6 | 211.5 |
| 2025 | 6 | 1377.6 | 203.6 |
| 2025 | 7 | 1495.2 | 195.3 |
| 2025 | 8 | 1538.4 | 230.6 |
| 2025 | 9 | 1510.8 | 226.3 |
| 2025 | 10 | 1481 | 209.2 |
| 2025 | 11 | 1444.3 | 199 |
| 2025 | 12 | 1646.9 | 229.2 |
| 2026 | 1 | 1573.3 | 236.1 |
| 2026 | 2 | 1295.5 | 216.3 |
| 2026 | 3 | 1462 | 203 |
| 2026 | 4 | 1411.4 | 211.2 |

(first 16 of 21 rows)

**Interpretation.** CPU hours are additive (about 1 300–1 650 h per month for all families). Queue backlog is semi-additive: it is summed across families within a day and then averaged over the days of the month (175–236 across the period); summing it across days would be meaningless.

## q15_drilldown_filter_procedure

**Question.** Drill-down through the taxonomy attached to the PIPELINE dimension: class 'variant filtering' > subclass ('hard filtering' / 'variant quality score recalibration'): which procedure gives a higher pass rate?

**Operation.** drill-down class -> subclass (parent_key self-join of dim_taxon) + SCD2 version detail

```sql
-- question: Drill-down through the taxonomy attached to the PIPELINE dimension: class 'variant filtering' > subclass ('hard filtering' / 'variant quality score recalibration'): which procedure gives a higher pass rate?
-- operation: drill-down class -> subclass (parent_key self-join of dim_taxon) + SCD2 version detail
SELECT c.label AS class, t.label AS subclass, t.iri, p.family, p.version, count(*) AS calls, round(100.0 * sum(f.is_pass) / count(*), 1) AS pass_pct
FROM fact_variant_call f JOIN dim_pipeline p USING (pipeline_key) JOIN dim_taxon t ON t.taxon_key = p.filter_taxon_key JOIN dim_taxon c ON c.taxon_key = t.parent_key
GROUP BY ALL ORDER BY subclass, family, version;
```

**Result** (8 rows, 5.1 ms on 20 000 facts)

| class | subclass | iri | family | version | calls | pass_pct |
|---|---|---|---|---|---|---|
| variant filtering | hard filtering | http://example.org/knowledge-hub/biomed/C063 | BCFTOOLS | 1.18 | 1455 | 48.2 |
| variant filtering | hard filtering | http://example.org/knowledge-hub/biomed/C063 | BCFTOOLS | 1.20 | 2550 | 49.1 |
| variant filtering | hard filtering | http://example.org/knowledge-hub/biomed/C063 | DEEPVARIANT | 1.6.1 | 2650 | 65 |
| variant filtering | hard filtering | http://example.org/knowledge-hub/biomed/C063 | DEEPVARIANT | 1.8.0 | 2377 | 64.5 |
| variant filtering | hard filtering | http://example.org/knowledge-hub/biomed/C063 | GATK | 4.4.0.0 | 1809 | 50.5 |
| variant filtering | hard filtering | http://example.org/knowledge-hub/biomed/C063 | GATK | 4.5.0.0 | 2869 | 57.7 |
| variant filtering | hard filtering | http://example.org/knowledge-hub/biomed/C063 | STRELKA | 2.9.10 | 3049 | 58.3 |
| variant filtering | variant quality score recalibration | http://example.org/knowledge-hub/biomed/C064 | GATK | 4.6.0.0 | 3241 | 59.2 |

**Interpretation.** Class 'variant filtering' → subclass: hard filtering is used by all families up to GATK 4.5; from 2026-03 GATK 4.6 uses variant quality score recalibration (C064) with a pass rate of 59.2% – higher than the earlier GATK versions with hard filtering (50.5% and 57.7%), but the comparison is confounded by the version change itself.

## Independent verification with pandas

`scripts/verify_olap.py` recomputes selected numbers from the Parquet files with pandas (merge + groupby, no SQL):

| check | SQL | pandas | match |
|---|---|---|---|
| q01 2025-Q3 calls | 2649 | 2649 | yes |
| q01 2025-Q3 pass% | 59.2 | 59.2 | yes |
| q01 grand total calls | 20000 | 20000 | yes |
| q01 grand total pass% | 57.4 | 57.4 | yes |
| q03 HBOC/tumor calls | 2985 | 2985 | yes |
| q03 HBOC/tumor pass% | 57.4 | 57.4 | yes |
| q03 ALL/blood calls | 10663 | 10663 | yes |
| q09 top review minutes (pass) | 509.1 | 509.1 | yes |
| q09 top review minutes (recheck) | 392.2 | 392.2 | yes |
| q13 GATK 4.5 avg_qual | 36.3 | 36.3 | yes |
| q13 GATK 4.5 pass% | 57.7 | 57.7 | yes |
| q13 GATK 4.5 calls | 2869 | 2869 | yes |

12.0 of 12 checks agree (queries q01, q03, q09, q13 – four results, more than the required two).
