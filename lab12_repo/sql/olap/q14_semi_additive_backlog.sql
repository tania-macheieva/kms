-- question: BQ08 Monthly CPU hours (additive) and queue backlog (semi-additive: summed across families within a day, then AVERAGED over days) per family
-- operation: correct aggregation of a semi-additive measure from the snapshot fact
WITH day_fam AS (SELECT d.year, d.month, p.family, f.date_key, f.cpu_hours, f.queue_backlog FROM fact_pipeline_day f JOIN dim_pipeline p USING (pipeline_key) JOIN dim_date d USING (date_key))
SELECT year, month, round(sum(cpu_hours), 1) AS cpu_hours_all, round(sum(queue_backlog) / count(DISTINCT date_key), 1) AS avg_daily_backlog_all_families
FROM day_fam GROUP BY ALL ORDER BY year, month;
