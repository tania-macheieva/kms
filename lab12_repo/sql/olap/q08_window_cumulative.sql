-- question: How many calls has each pipeline family accumulated by the end of each quarter?
-- operation: WINDOW running total (SUM() OVER (PARTITION BY family ORDER BY quarter))
WITH q AS (SELECT p.family, d.year, d.quarter, count(*) AS calls FROM fact_variant_call f JOIN dim_pipeline p USING (pipeline_key) JOIN dim_date d USING (date_key) GROUP BY ALL)
SELECT family, year, quarter, calls, sum(calls) OVER (PARTITION BY family ORDER BY year, quarter) AS cumulative_calls
FROM q ORDER BY family, year, quarter;
