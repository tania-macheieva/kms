-- question: What is the pass rate per pipeline family, per variant type, and per family x variant type, in ONE pass over the fact?
-- operation: GROUPING SETS (taxonomy role-playing: variant_type_key -> dim_taxon)
SELECT coalesce(p.family, 'ALL') AS family, coalesce(t.label, 'ALL') AS variant_type, count(*) AS calls, round(100.0 * sum(f.is_pass) / count(*), 1) AS pass_pct
FROM fact_variant_call f JOIN dim_pipeline p USING (pipeline_key) JOIN dim_taxon t ON t.taxon_key = f.variant_type_key
GROUP BY GROUPING SETS ((p.family), (t.label), (p.family, t.label)) ORDER BY grouping(p.family) , grouping(t.label), 1, 2;
