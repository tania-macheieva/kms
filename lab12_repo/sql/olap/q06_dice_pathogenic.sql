-- question: In the HBOC and Lynch cohorts, blood and tumor samples only: how many pathogenic calls per gene?
-- operation: DICE (sub-cube on 3 dimensions: sample, taxon role significance, tissue)
SELECT g.gene_symbol, count(*) AS pathogenic_calls, count(DISTINCT f.sample_key) AS samples
FROM fact_variant_call f JOIN dim_sample s USING (sample_key) JOIN dim_gene g USING (gene_key) JOIN dim_taxon sg ON sg.taxon_key = f.significance_key
WHERE s.cohort IN ('HBOC', 'Lynch') AND s.tissue IN ('blood', 'tumor') AND sg.label = 'pathogenic variant'
GROUP BY g.gene_symbol ORDER BY pathogenic_calls DESC;
