# Gate report: S0_baseline (`/home/claude/w/lab14_repo/store`) — **FAIL**

14/25 passed; blocking failures 9, warnings 2

| check | status | severity | message |
|---|---|---|---|
| test_Q01_shacl_conforms | fail | blocking | AssertionError: SHACL violations {'S05': 3, 'S14': 1}: [('S05: chunk needs a non-empty section', 'http://dkh.example/Chunk/gatk_readme#h000'), ('S05: chunk needs a non-empty section', 'http://dkh.example/Chunk/gatk_docke |
| test_Q02_sparql_no_orphan_variants | pass | blocking |  |
| test_Q03_sparql_hardfiltering_has_thresholds | pass | blocking |  |
| test_Q04_sparql_annotation_names_unique_per_variant | pass | blocking |  |
| test_Q05_jsonschema_chunks | fail | blocking | AssertionError: [('bcftools_readme#h000', "'' should be non-empty"), ('gatk_readme#h000', "'' should be non-empty"), ('gatk_docker#h000', "'' should be non-empty")] assert not [('bcftools_readme#h000', "'' should be non- |
| test_Q06_jsonschema_alternatives | fail | blocking | AssertionError: no alternatives register assert False  +  where False = exists()  +    where exists = PosixPath('/home/claude/w/lab14_repo/store/alternatives.jsonl').exists |
| test_Q07_jsonschema_fixtures | pass | blocking |  |
| test_Q08_sql_unique_chunk_ids | pass | blocking |  |
| test_Q09_sql_applies_to_person_integrity | pass | blocking |  |
| test_Q10_sql_relationship_provenance | pass | blocking |  |
| test_Q11_metric_threshold[M01_completeness] | fail | blocking | AssertionError: M01_completeness=0.9956 violates >= 1.0 (blocking) assert False |
| test_Q11_metric_threshold[M02_schema_validity] | fail | blocking | AssertionError: M02_schema_validity=0.9956 violates >= 1.0 (blocking) assert False |
| test_Q11_metric_threshold[M03_open_conflicts] | fail | blocking | AssertionError: M03_open_conflicts=8 violates <= 0 (blocking) assert False |
| test_Q11_metric_threshold[M04_active_logical_violations] | fail | blocking | AssertionError: M04_active_logical_violations=1 violates <= 0 (blocking) assert False |
| test_Q11_metric_threshold[M05_provenance_fidelity] | pass | blocking |  |
| test_Q11_metric_threshold[M06_expert_sample_accuracy] | fail | warning | AssertionError: M06_expert_sample_accuracy=0.6389 violates >= 0.9 (warning) assert False |
| test_Q11_metric_threshold[M07_conflict_documentation] | fail | blocking | AssertionError: M07_conflict_documentation=0.0 violates >= 1.0 (blocking) assert False |
| test_Q11_metric_threshold[M08_near_duplicate_share] | fail | blocking | AssertionError: M08_near_duplicate_share=0.0203 violates <= 0.0 (blocking) assert False |
| test_Q11_metric_threshold[M09_freshness] | pass | blocking |  |
| test_Q11_metric_threshold[M10_id_uniqueness] | pass | blocking |  |
| test_Q11_metric_threshold[M11_graph_referential_integrity] | pass | blocking |  |
| test_Q11_metric_threshold[M12_sensitivity_valid] | pass | blocking |  |
| test_Q11_metric_threshold[M13_language_consistency] | pass | blocking |  |
| test_Q11_metric_threshold[M14_self_retrieval_at1] | fail | warning | AssertionError: M14_self_retrieval_at1=0.9404 violates >= 0.97 (warning) assert False |
| test_Q12_merge_is_reversible | pass | blocking |  |
