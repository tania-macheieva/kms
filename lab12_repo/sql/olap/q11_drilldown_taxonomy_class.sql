-- question: BQ10 DRILL-DOWN along the taxonomy path (role = variant type): 'Genetic variation' > 'genetic variant' > leaf concept - calls and pass rate at every level
-- operation: ROLLUP over the taxonomy hierarchy columns of dim_taxon (top_label > facet_label > label)
SELECT t.top_label, t.facet_label, t.label, count(*) AS calls, round(100.0 * sum(f.is_pass) / count(*), 1) AS pass_pct,
       grouping(t.top_label) + grouping(t.facet_label) + grouping(t.label) AS rollup_level
FROM fact_variant_call f JOIN dim_taxon t ON t.taxon_key = f.variant_type_key
GROUP BY ROLLUP (t.top_label, t.facet_label, t.label) ORDER BY rollup_level DESC, calls DESC;
