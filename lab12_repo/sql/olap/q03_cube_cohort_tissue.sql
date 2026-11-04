-- question: BQ09 Which cohort / tissue combinations have the highest share of passed calls? (all subtotals)
-- operation: CUBE (cohort, tissue) with GROUPING()
SELECT coalesce(s.cohort, 'ALL') AS cohort, coalesce(s.tissue, 'ALL') AS tissue, count(*) AS calls, round(100.0 * sum(f.is_pass) / count(*), 1) AS pass_pct
FROM fact_variant_call f JOIN dim_sample s USING (sample_key)
GROUP BY CUBE (s.cohort, s.tissue) ORDER BY grouping(s.cohort), grouping(s.tissue), s.cohort, s.tissue;
