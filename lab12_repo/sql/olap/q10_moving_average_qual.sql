-- question: BQ07-like How does the average call quality move month by month per family (3-month moving average smooths the noise)?
-- operation: WINDOW moving average (AVG() OVER (ROWS BETWEEN 2 PRECEDING AND CURRENT ROW)); non-additive measure -> avg of calls, not avg of averages
WITH m AS (SELECT p.family, d.year, d.month, round(avg(f.qual), 2) AS avg_qual, count(*) AS calls FROM fact_variant_call f JOIN dim_pipeline p USING (pipeline_key) JOIN dim_date d USING (date_key) GROUP BY ALL)
SELECT family, year, month, avg_qual, round(avg(avg_qual) OVER (PARTITION BY family ORDER BY year, month ROWS BETWEEN 2 PRECEDING AND CURRENT ROW), 2) AS moving_avg_3m
FROM m WHERE family IN ('GATK', 'DEEPVARIANT') ORDER BY family, year, month;
