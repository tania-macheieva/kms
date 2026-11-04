-- question: BQ01 How many calls passed in each gene, and what share of the chromosome / of all calls does each gene give? (hierarchy gene -> chromosome)
-- operation: ROLLUP (chromosome > gene)
SELECT g.chromosome, g.gene_symbol, count(*) AS calls, sum(f.is_pass) AS passed, round(100.0 * sum(f.is_pass) / count(*), 1) AS pass_pct,
       grouping(g.chromosome) AS g_chr, grouping(g.gene_symbol) AS g_gene
FROM fact_variant_call f JOIN dim_gene g USING (gene_key)
GROUP BY ROLLUP (g.chromosome, g.gene_symbol) ORDER BY try_cast(g.chromosome AS INT) NULLS LAST, grouping(g.gene_symbol), calls DESC;
