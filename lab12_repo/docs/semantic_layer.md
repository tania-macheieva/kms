# Semantic layer (R4)

`semantic/metrics.yml` – definitions, `semantic/sl.py` – `metric_sql(metric, by, where)` generates SQL. Filters are parameterized; `order_by` accepts only selected dimension/metric names (optionally followed by `ASC` or `DESC`), and an empty filter or non-positive limit is rejected. Tests: `tests/test_semantic.py`, consistency: `scripts/check_semantic.py`.

## Why

Without a layer every analyst writes his own `pass rate` (average of monthly percentages, `COUNT(DISTINCT)` vs `COUNT(*)`, a different set of joins). With it the **definition lives in one place**, carries its unit, owner, sources and limitations, is checked once, and queries (including text-to-SQL, R5) use it as the vocabulary. It also stops forbidden combinations: a metric on the snapshot fact cannot be sliced by gene (`SemanticError`).

## Metrics (7, all fields filled)

| metric | definition | formula | unit | owner | sources | additivity | limitations | status / reviewed |
|---|---|---|---|---|---|---|---|---|
| `call_count` | Number of called variants (rows of the fact at the grain "one call"). | `count(*)` | calls | bioinformatics lead | fact_variant_call | additive | Counts calls, not distinct variants or samples; the same variant in two samples is two calls. Rejected rows (quarantine) are not included. | approved / 2026-11-02 |
| `pass_rate` | Share of calls that passed the pipeline filter. | `round(100.0 * sum(f.is_pass) / count(*), 1)` | % | bioinformatics lead | fact_variant_call.is_pass | non-additive (ratio of two additive sums) | Ratio of sums, never an average of group percentages. is_pass is a simplified flag (quality >= 30 and depth >= 10 in the synthetic data), not a clinical validation. | approved / 2026-11-02 |
| `avg_qual` | Mean QUAL over the calls in the group. | `round(avg(f.qual), 1)` | Phred-like score | bioinformatics lead | fact_variant_call.qual | non-additive | Not comparable between callers (different QUAL calibration); mean of calls, not mean of monthly means. | approved / 2026-11-02 |
| `review_min_per_call` | Manual review time divided by the number of calls. | `round(sum(f.review_minutes) / count(*), 2)` | minutes per call | lab operations | fact_variant_call.review_minutes | non-additive (ratio) | Only pathogenic and uncertain calls are reviewed, the denominator includes all calls; time is self-reported in the synthetic data. | draft / 2026-11-02 |
| `pathogenic_share` | Share of calls whose clinical significance is the taxonomy concept 'pathogenic variant' (C033). | `round(100.0 * sum(CASE WHEN sg_p.notation = 'C033' THEN 1 ELSE 0 END) / count(*), 1)` | % | clinical geneticist | fact_variant_call.significance_key, dim_taxon (IRI .../C033) | non-additive (ratio) | Classification is from the generator, not an ACMG assessment; do not use for any clinical decision. | draft / 2026-11-02 |
| `cpu_hours` | Compute time consumed by pipeline runs. | `round(sum(f.cpu_hours), 1)` | hours | IT operations | fact_pipeline_day.cpu_hours | additive | Synthetic estimate; only the 4 pipeline families. | approved / 2026-11-02 |
| `avg_daily_backlog` | Queue backlog summed over the pipelines in a day, averaged over the days of the period. | `round(sum(f.queue_backlog) / count(DISTINCT f.date_key), 1)` | jobs | IT operations | fact_pipeline_day.queue_backlog | semi-additive (sum across pipelines, average across time) | Must not be summed over days; if a family is filtered out the value is the backlog of the remaining families. | approved / 2026-11-02 |

Layer metadata: version 1.0, reviewed 2026-11-02, reviewer: pending - draft prepared with LLM assistance, student review required (status draft metrics). Of 7 metrics 5 are `approved`, 2 are `draft` (review minutes are self-reported; pathogenic share is a generator label) – the approval is a decision to be confirmed by the student/owner.

## Generated SQL (examples)

`metric_sql('pass_rate', by=['year', 'family'], where=None)`

```sql
SELECT d.year AS year, p.family AS family, round(100.0 * sum(f.is_pass) / count(*), 1) AS pass_rate
FROM fact_variant_call f
JOIN dim_date d ON d.date_key = f.date_key
JOIN dim_pipeline p ON p.pipeline_key = f.pipeline_key
GROUP BY d.year, p.family
ORDER BY d.year, p.family
```
params: `[]`

`metric_sql('pathogenic_share', by=['gene'], where={'cohort': ['HBOC']})`

```sql
SELECT g.gene_symbol AS gene, round(100.0 * sum(CASE WHEN sg_p.notation = 'C033' THEN 1 ELSE 0 END) / count(*), 1) AS pathogenic_share
FROM fact_variant_call f
JOIN dim_gene g ON g.gene_key = f.gene_key
JOIN dim_sample s ON s.sample_key = f.sample_key
JOIN dim_taxon sg_p ON sg_p.taxon_key = f.significance_key
WHERE s.cohort IN (?)
GROUP BY g.gene_symbol
ORDER BY g.gene_symbol
```
params: `['HBOC']`

`metric_sql('avg_daily_backlog', by=['year', 'month'], where=None)`

```sql
SELECT d.year AS year, d.month AS month, round(sum(f.queue_backlog) / count(DISTINCT f.date_key), 1) AS avg_daily_backlog
FROM fact_pipeline_day f
JOIN dim_date d ON d.date_key = f.date_key
GROUP BY d.year, d.month
ORDER BY d.year, d.month
```
params: `[]`

## Consistency: one question, three paths

| question | paths compared (rows) | identical |
|---|---|---|
| What is the pass rate by year? | semantic layer (2); hand SQL (2); pandas (2) | yes |
| What is the average call quality per tool version? | semantic layer (8); hand SQL (q13-style) (8); pandas (8) | yes |
| What share of calls is pathogenic, per gene? | semantic layer (10); hand SQL (label) (10); pandas (by key of IRI C033) (10) | yes |
| What is the average daily queue backlog per month? | semantic layer (21); OLAP file q14 (21); pandas (21) | yes |

4 of 4 questions give identical results by the semantic layer, by hand-written OLAP SQL and by pandas (more than the required two).

Why a definition matters: the average of the 21 monthly pass rates is 57.15% while the ratio of sums is 57.4% (difference -0.25 pp). It is small here because months have similar volumes; with unbalanced groups (e.g. a rare variant type) the gap grows – the layer fixes the correct form once.

## Limits

- The layer is a small Python/YAML implementation, not dbt/Cube: no derived metrics from other metrics, no time-intelligence functions, no access control per metric.
- Filters accept only equality/IN; dimension attributes and metric formulas are trusted (they come from the reviewed YAML, not from users); all user values are bound parameters.
- Review is formal: the `reviewer` field says that the student's review is pending.
