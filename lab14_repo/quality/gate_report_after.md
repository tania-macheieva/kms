# Gate report: after (`store_clean`) — **PASS**

23/25 passed; blocking failures 0, warnings 2

| check | status | severity | message |
|---|---|---|---|
| test_Q01_shacl_conforms | pass | blocking |  |
| test_Q02_sparql_no_orphan_variants | pass | blocking |  |
| test_Q03_sparql_hardfiltering_has_thresholds | pass | blocking |  |
| test_Q04_sparql_annotation_names_unique_per_variant | pass | blocking |  |
| test_Q05_jsonschema_chunks | pass | blocking |  |
| test_Q06_jsonschema_alternatives | pass | blocking |  |
| test_Q07_jsonschema_fixtures | pass | blocking |  |
| test_Q08_sql_unique_chunk_ids | pass | blocking |  |
| test_Q09_sql_applies_to_person_integrity | pass | blocking |  |
| test_Q10_sql_relationship_provenance | pass | blocking |  |
| test_Q11_metric_threshold[M01_completeness] | pass | blocking |  |
| test_Q11_metric_threshold[M02_schema_validity] | pass | blocking |  |
| test_Q11_metric_threshold[M03_open_conflicts] | pass | blocking |  |
| test_Q11_metric_threshold[M04_active_logical_violations] | pass | blocking |  |
| test_Q11_metric_threshold[M05_provenance_fidelity] | pass | blocking |  |
| test_Q11_metric_threshold[M06_expert_sample_accuracy] | fail | warning | AssertionError: M06_expert_sample_accuracy=0.6389 violates >= 0.9 (warning) assert False |
| test_Q11_metric_threshold[M07_conflict_documentation] | pass | blocking |  |
| test_Q11_metric_threshold[M08_near_duplicate_share] | pass | blocking |  |
| test_Q11_metric_threshold[M09_freshness] | pass | blocking |  |
| test_Q11_metric_threshold[M10_id_uniqueness] | pass | blocking |  |
| test_Q11_metric_threshold[M11_graph_referential_integrity] | pass | blocking |  |
| test_Q11_metric_threshold[M12_sensitivity_valid] | pass | blocking |  |
| test_Q11_metric_threshold[M13_language_consistency] | pass | blocking |  |
| test_Q11_metric_threshold[M14_self_retrieval_at1] | fail | warning | AssertionError: M14_self_retrieval_at1=0.957 violates >= 0.97 (warning) assert False |
| test_Q12_merge_is_reversible | pass | blocking |  |
