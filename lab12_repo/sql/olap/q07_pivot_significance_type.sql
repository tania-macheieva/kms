-- question: BQ04 How are clinical-significance classes distributed across variant types?
-- operation: PIVOT (rows = variant type, columns = significance)
PIVOT (SELECT vt.label AS variant_type, sg.label AS significance, f.call_count
       FROM fact_variant_call f JOIN dim_taxon vt ON vt.taxon_key = f.variant_type_key JOIN dim_taxon sg ON sg.taxon_key = f.significance_key)
ON significance USING sum(call_count) GROUP BY variant_type ORDER BY variant_type;
