-- question: Drill-down through the taxonomy attached to the PIPELINE dimension: class 'variant filtering' > subclass ('hard filtering' / 'variant quality score recalibration'): which procedure gives a higher pass rate?
-- operation: drill-down class -> subclass (parent_key self-join of dim_taxon) + SCD2 version detail
SELECT c.label AS class, t.label AS subclass, t.iri, p.family, p.version, count(*) AS calls, round(100.0 * sum(f.is_pass) / count(*), 1) AS pass_pct
FROM fact_variant_call f JOIN dim_pipeline p USING (pipeline_key) JOIN dim_taxon t ON t.taxon_key = p.filter_taxon_key JOIN dim_taxon c ON c.taxon_key = t.parent_key
GROUP BY ALL ORDER BY subclass, family, version;
