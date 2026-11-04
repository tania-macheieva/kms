-- question: BQ11 In 2026, do weekend calls need more manual review than weekday calls? (slice year = 2026)
-- operation: SLICE (one value of the date dimension) + group by day of week
SELECT d.day_of_week, d.is_weekend, count(*) AS calls, round(sum(f.review_minutes), 1) AS review_min_total, round(sum(f.review_minutes) / count(*), 2) AS review_min_per_call
FROM fact_variant_call f JOIN dim_date d USING (date_key) WHERE d.year = 2026
GROUP BY d.day_of_week, d.is_weekend ORDER BY d.day_of_week;
