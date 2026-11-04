-- question: BQ10 DRILL-DOWN step 2 (subclass level): inside the class 'genetic variant', calls and pass rate per leaf concept with its IRI
-- operation: drill-down class -> subclass (WHERE facet_label = ... , GROUP BY leaf concept)
SELECT t.facet_label AS class, t.label AS subclass, t.iri, count(*) AS calls, round(100.0 * sum(f.is_pass) / count(*), 1) AS pass_pct, round(avg(f.qual), 1) AS avg_qual
FROM fact_variant_call f JOIN dim_taxon t ON t.taxon_key = f.variant_type_key WHERE t.facet_label = 'genetic variant'
GROUP BY ALL ORDER BY calls DESC;
