-- question: BQ02 How does the number of variant calls and the share of passed calls change by year and quarter (with subtotals)?
-- operation: ROLLUP (year > quarter)
SELECT d.year, d.quarter, count(*) AS calls, sum(f.is_pass) AS passed, round(100.0 * sum(f.is_pass) / count(*), 1) AS pass_pct,
       grouping(d.year) AS g_year, grouping(d.quarter) AS g_quarter
FROM fact_variant_call f JOIN dim_date d USING (date_key)
GROUP BY ROLLUP (d.year, d.quarter) ORDER BY d.year NULLS LAST, d.quarter NULLS LAST;
