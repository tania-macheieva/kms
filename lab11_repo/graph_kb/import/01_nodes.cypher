// Примітка: toFloat() у FalkorDB повертає значення з точністю float32 (напр. 1.1 → 1.10000002384186), тому округлення round(x*1000)/1000 повертає точний double (дані мають ≤ 1 знака після коми). У Neo4j це безпечно, але зайве.
// Вузли: LOAD CSV + MERGE за ключем (ідемпотентно). Файли — у каталозі import сервера.

LOAD CSV WITH HEADERS FROM 'file:///nodes_Variant.csv' AS row
MERGE (n:Variant {id: row.id})
SET n.type = CASE row.type WHEN '' THEN null ELSE row.type END, n.clinicalSignificance = CASE row.clinicalSignificance WHEN '' THEN null ELSE row.clinicalSignificance END, n.exonEnd = CASE row.exonEnd WHEN 'true' THEN true WHEN 'false' THEN false ELSE null END;

LOAD CSV WITH HEADERS FROM 'file:///nodes_Annotation.csv' AS row
MERGE (n:Annotation {id: row.id})
SET n.name = CASE row.name WHEN '' THEN null ELSE row.name END, n.value = CASE row.value WHEN '' THEN null ELSE round(toFloat(row.value) * 1000) / 1000 END;

LOAD CSV WITH HEADERS FROM 'file:///nodes_AnnotationType.csv' AS row
MERGE (n:AnnotationType {name: row.name});

LOAD CSV WITH HEADERS FROM 'file:///nodes_Gene.csv' AS row
MERGE (n:Gene {symbol: row.symbol})
SET n.chromosome = CASE row.chromosome WHEN '' THEN null ELSE row.chromosome END;

LOAD CSV WITH HEADERS FROM 'file:///nodes_GenePanel.csv' AS row
MERGE (n:GenePanel {name: row.name});

LOAD CSV WITH HEADERS FROM 'file:///nodes_Sample.csv' AS row
MERGE (n:Sample {code: row.code});

LOAD CSV WITH HEADERS FROM 'file:///nodes_Person.csv' AS row
MERGE (n:Person {name: row.name})
SET n.ageYears = CASE row.ageYears WHEN '' THEN null ELSE toInteger(row.ageYears) END, n.sex = CASE row.sex WHEN '' THEN null ELSE row.sex END, n.deceased = CASE row.deceased WHEN 'true' THEN true WHEN 'false' THEN false ELSE null END, n.proband = CASE row.proband WHEN 'true' THEN true WHEN 'false' THEN false ELSE null END;

LOAD CSV WITH HEADERS FROM 'file:///nodes_Diagnosis.csv' AS row
MERGE (n:Diagnosis {id: row.id})
SET n.kind = CASE row.kind WHEN '' THEN null ELSE row.kind END;

LOAD CSV WITH HEADERS FROM 'file:///nodes_Threshold.csv' AS row
MERGE (n:Threshold {id: row.id})
SET n.annotation = CASE row.annotation WHEN '' THEN null ELSE row.annotation END, n.op = CASE row.op WHEN '' THEN null ELSE row.op END, n.value = CASE row.value WHEN '' THEN null ELSE round(toFloat(row.value) * 1000) / 1000 END, n.variantType = CASE row.variantType WHEN '' THEN null ELSE row.variantType END;

LOAD CSV WITH HEADERS FROM 'file:///nodes_Procedure.csv' AS row
MERGE (n:Procedure {id: row.id})
SET n.kind = CASE row.kind WHEN '' THEN null ELSE row.kind END, n.minTestingAge = CASE row.minTestingAge WHEN '' THEN null ELSE toInteger(row.minTestingAge) END;

LOAD CSV WITH HEADERS FROM 'file:///nodes_DataFile.csv' AS row
MERGE (n:DataFile {id: row.id})
SET n.format = CASE row.format WHEN '' THEN null ELSE row.format END, n.label = CASE row.label WHEN '' THEN null ELSE row.label END;

LOAD CSV WITH HEADERS FROM 'file:///nodes_Instrument.csv' AS row
MERGE (n:Instrument {id: row.id});

LOAD CSV WITH HEADERS FROM 'file:///nodes_Situation.csv' AS row
MERGE (n:Situation {id: row.id})
SET n.name = CASE row.name WHEN '' THEN null ELSE row.name END, n.guard = CASE row.guard WHEN '' THEN null ELSE row.guard END;

LOAD CSV WITH HEADERS FROM 'file:///nodes_Concept.csv' AS row
MERGE (n:Concept {name: row.name})
SET n.probability = CASE row.probability WHEN '' THEN null ELSE round(toFloat(row.probability) * 1000) / 1000 END;
