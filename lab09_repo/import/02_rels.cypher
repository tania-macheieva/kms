// Зв'язки: MATCH кінців + MERGE зв'язку; властивості походження source/confidence/validFrom ставляться при створенні.

LOAD CSV WITH HEADERS FROM 'file:///rels_APPLIES_TO__Procedure_DataFile.csv' AS row
MATCH (a:Procedure {id: row.from}), (b:DataFile {id: row.to})
MERGE (a)-[r:APPLIES_TO]->(b)
ON CREATE SET r.source = row.source, r.confidence = round(toFloat(row.confidence) * 1000) / 1000, r.validFrom = date(row.validFrom);

LOAD CSV WITH HEADERS FROM 'file:///rels_APPLIES_TO__Procedure_Person.csv' AS row
MATCH (a:Procedure {id: row.from}), (b:Person {name: row.to})
MERGE (a)-[r:APPLIES_TO]->(b)
ON CREATE SET r.source = row.source, r.confidence = round(toFloat(row.confidence) * 1000) / 1000, r.validFrom = date(row.validFrom);

LOAD CSV WITH HEADERS FROM 'file:///rels_CARRIES__Person_Variant.csv' AS row
MATCH (a:Person {name: row.from}), (b:Variant {id: row.to})
MERGE (a)-[r:CARRIES]->(b)
ON CREATE SET r.source = row.source, r.confidence = round(toFloat(row.confidence) * 1000) / 1000, r.validFrom = date(row.validFrom);

LOAD CSV WITH HEADERS FROM 'file:///rels_CHECKS__Threshold_AnnotationType.csv' AS row
MATCH (a:Threshold {id: row.from}), (b:AnnotationType {name: row.to})
MERGE (a)-[r:CHECKS]->(b)
ON CREATE SET r.source = row.source, r.confidence = round(toFloat(row.confidence) * 1000) / 1000, r.validFrom = date(row.validFrom);

LOAD CSV WITH HEADERS FROM 'file:///rels_DERIVED_FROM__DataFile_DataFile.csv' AS row
MATCH (a:DataFile {id: row.from}), (b:DataFile {id: row.to})
MERGE (a)-[r:DERIVED_FROM]->(b)
ON CREATE SET r.source = row.source, r.confidence = round(toFloat(row.confidence) * 1000) / 1000, r.validFrom = date(row.validFrom);

LOAD CSV WITH HEADERS FROM 'file:///rels_FROM_SAMPLE__Variant_Sample.csv' AS row
MATCH (a:Variant {id: row.from}), (b:Sample {code: row.to})
MERGE (a)-[r:FROM_SAMPLE]->(b)
ON CREATE SET r.source = row.source, r.confidence = round(toFloat(row.confidence) * 1000) / 1000, r.validFrom = date(row.validFrom);

LOAD CSV WITH HEADERS FROM 'file:///rels_GENERATED_BY__DataFile_Instrument.csv' AS row
MATCH (a:DataFile {id: row.from}), (b:Instrument {id: row.to})
MERGE (a)-[r:GENERATED_BY]->(b)
ON CREATE SET r.source = row.source, r.confidence = round(toFloat(row.confidence) * 1000) / 1000, r.validFrom = date(row.validFrom);

LOAD CSV WITH HEADERS FROM 'file:///rels_GUARD_CLASS__Situation_Concept.csv' AS row
MATCH (a:Situation {id: row.from}), (b:Concept {name: row.to})
MERGE (a)-[r:GUARD_CLASS]->(b)
ON CREATE SET r.source = row.source, r.confidence = round(toFloat(row.confidence) * 1000) / 1000, r.validFrom = date(row.validFrom);

LOAD CSV WITH HEADERS FROM 'file:///rels_HAS_ANNOTATION__Variant_Annotation.csv' AS row
MATCH (a:Variant {id: row.from}), (b:Annotation {id: row.to})
MERGE (a)-[r:HAS_ANNOTATION]->(b)
ON CREATE SET r.source = row.source, r.confidence = round(toFloat(row.confidence) * 1000) / 1000, r.validFrom = date(row.validFrom);

LOAD CSV WITH HEADERS FROM 'file:///rels_HAS_DIAGNOSIS__Person_Diagnosis.csv' AS row
MATCH (a:Person {name: row.from}), (b:Diagnosis {id: row.to})
MERGE (a)-[r:HAS_DIAGNOSIS]->(b)
ON CREATE SET r.source = row.source, r.confidence = round(toFloat(row.confidence) * 1000) / 1000, r.validFrom = date(row.validFrom);

LOAD CSV WITH HEADERS FROM 'file:///rels_HAS_MEMBER__GenePanel_Gene.csv' AS row
MATCH (a:GenePanel {name: row.from}), (b:Gene {symbol: row.to})
MERGE (a)-[r:HAS_MEMBER]->(b)
ON CREATE SET r.source = row.source, r.confidence = round(toFloat(row.confidence) * 1000) / 1000, r.validFrom = date(row.validFrom);

LOAD CSV WITH HEADERS FROM 'file:///rels_HAS_PARENT__Person_Person.csv' AS row
MATCH (a:Person {name: row.from}), (b:Person {name: row.to})
MERGE (a)-[r:HAS_PARENT]->(b)
ON CREATE SET r.source = row.source, r.confidence = round(toFloat(row.confidence) * 1000) / 1000, r.validFrom = date(row.validFrom);

LOAD CSV WITH HEADERS FROM 'file:///rels_HAS_PROBAND__Procedure_Person.csv' AS row
MATCH (a:Procedure {id: row.from}), (b:Person {name: row.to})
MERGE (a)-[r:HAS_PROBAND]->(b)
ON CREATE SET r.source = row.source, r.confidence = round(toFloat(row.confidence) * 1000) / 1000, r.validFrom = date(row.validFrom);

LOAD CSV WITH HEADERS FROM 'file:///rels_HAS_SIBLING__Person_Person.csv' AS row
MATCH (a:Person {name: row.from}), (b:Person {name: row.to})
MERGE (a)-[r:HAS_SIBLING]->(b)
ON CREATE SET r.source = row.source, r.confidence = round(toFloat(row.confidence) * 1000) / 1000, r.validFrom = date(row.validFrom);

LOAD CSV WITH HEADERS FROM 'file:///rels_HAS_THRESHOLD__Procedure_Threshold.csv' AS row
MATCH (a:Procedure {id: row.from}), (b:Threshold {id: row.to})
MERGE (a)-[r:HAS_THRESHOLD]->(b)
ON CREATE SET r.source = row.source, r.confidence = round(toFloat(row.confidence) * 1000) / 1000, r.validFrom = date(row.validFrom);

LOAD CSV WITH HEADERS FROM 'file:///rels_INSTANCE_OF__Person_Concept.csv' AS row
MATCH (a:Person {name: row.from}), (b:Concept {name: row.to})
MERGE (a)-[r:INSTANCE_OF]->(b)
ON CREATE SET r.source = row.source, r.confidence = round(toFloat(row.confidence) * 1000) / 1000, r.validFrom = date(row.validFrom);

LOAD CSV WITH HEADERS FROM 'file:///rels_INSTANCE_OF__Variant_Concept.csv' AS row
MATCH (a:Variant {id: row.from}), (b:Concept {name: row.to})
MERGE (a)-[r:INSTANCE_OF]->(b)
ON CREATE SET r.source = row.source, r.confidence = round(toFloat(row.confidence) * 1000) / 1000, r.validFrom = date(row.validFrom);

LOAD CSV WITH HEADERS FROM 'file:///rels_LOCATED_IN__Variant_Gene.csv' AS row
MATCH (a:Variant {id: row.from}), (b:Gene {symbol: row.to})
MERGE (a)-[r:LOCATED_IN]->(b)
ON CREATE SET r.source = row.source, r.confidence = round(toFloat(row.confidence) * 1000) / 1000, r.validFrom = date(row.validFrom);

LOAD CSV WITH HEADERS FROM 'file:///rels_OF_TYPE__Annotation_AnnotationType.csv' AS row
MATCH (a:Annotation {id: row.from}), (b:AnnotationType {name: row.to})
MERGE (a)-[r:OF_TYPE]->(b)
ON CREATE SET r.source = row.source, r.confidence = round(toFloat(row.confidence) * 1000) / 1000, r.validFrom = date(row.validFrom);

LOAD CSV WITH HEADERS FROM 'file:///rels_REQUIRES__Procedure_Variant.csv' AS row
MATCH (a:Procedure {id: row.from}), (b:Variant {id: row.to})
MERGE (a)-[r:REQUIRES]->(b)
ON CREATE SET r.source = row.source, r.confidence = round(toFloat(row.confidence) * 1000) / 1000, r.validFrom = date(row.validFrom);

LOAD CSV WITH HEADERS FROM 'file:///rels_SUBCLASS_OF__Concept_Concept.csv' AS row
MATCH (a:Concept {name: row.from}), (b:Concept {name: row.to})
MERGE (a)-[r:SUBCLASS_OF]->(b)
ON CREATE SET r.source = row.source, r.confidence = round(toFloat(row.confidence) * 1000) / 1000, r.validFrom = date(row.validFrom);
