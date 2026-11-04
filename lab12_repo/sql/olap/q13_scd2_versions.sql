-- question: BQ06 Did upgrading tool versions change average quality and read depth? (SCD2: every version is its own dim_pipeline row)
-- operation: group by SCD2 attributes; non-additive measures -> AVG over calls
SELECT p.family, p.version, p.valid_from, p.valid_to, count(*) AS calls, round(avg(f.qual), 1) AS avg_qual, round(avg(f.read_depth), 1) AS avg_depth, round(100.0 * sum(f.is_pass) / count(*), 1) AS pass_pct
FROM fact_variant_call f JOIN dim_pipeline p USING (pipeline_key) GROUP BY ALL ORDER BY p.family, p.valid_from;
