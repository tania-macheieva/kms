// Схема для Neo4j 5 (довідково; у цьому середовищі виконано еквівалент через API FalkorDB — scripts/import_graph.py).

CREATE CONSTRAINT variant_id IF NOT EXISTS FOR (n:Variant) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT gene_symbol IF NOT EXISTS FOR (n:Gene) REQUIRE n.symbol IS UNIQUE;
CREATE CONSTRAINT person_name IF NOT EXISTS FOR (n:Person) REQUIRE n.name IS UNIQUE;
CREATE CONSTRAINT annotation_id IF NOT EXISTS FOR (n:Annotation) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT sample_code IF NOT EXISTS FOR (n:Sample) REQUIRE n.code IS UNIQUE;
CREATE CONSTRAINT threshold_id IF NOT EXISTS FOR (n:Threshold) REQUIRE n.id IS UNIQUE;
CREATE INDEX annotation_name_idx IF NOT EXISTS FOR (n:Annotation) ON (n.name);
CREATE INDEX annotation_value_idx IF NOT EXISTS FOR (n:Annotation) ON (n.value);
CREATE INDEX variant_type_idx IF NOT EXISTS FOR (n:Variant) ON (n.type);
CREATE INDEX person_ageYears_idx IF NOT EXISTS FOR (n:Person) ON (n.ageYears);

SHOW CONSTRAINTS;
SHOW INDEXES;
