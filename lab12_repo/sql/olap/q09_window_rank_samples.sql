-- question: BQ05 Which 3 samples consumed the most review minutes inside each QC status group?
-- operation: WINDOW RANK (DENSE_RANK() OVER (PARTITION BY qc_status ORDER BY minutes DESC))
WITH m AS (SELECT s.qc_status, s.sample_code, s.cohort, round(sum(f.review_minutes), 1) AS review_min, count(*) AS calls FROM fact_variant_call f JOIN dim_sample s USING (sample_key) GROUP BY ALL),
     r AS (SELECT *, dense_rank() OVER (PARTITION BY qc_status ORDER BY review_min DESC) AS rnk FROM m)
SELECT * FROM r WHERE rnk <= 3 ORDER BY qc_status, rnk, sample_code;
