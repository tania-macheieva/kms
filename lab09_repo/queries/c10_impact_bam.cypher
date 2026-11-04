// АНАЛІЗ ВПЛИВУ 2: Якщо sample1.bam буде перероблено — що залежить від нього (глибина до 4)?
// BAM <-DERIVED_FROM*- файли; процедури, що застосовуються до цих файлів; пороги цих процедур.
MATCH (f:DataFile {id: 'sample1_bam'})<-[:DERIVED_FROM*1..3]-(d:DataFile)<-[:APPLIES_TO]-(proc:Procedure)-[:HAS_THRESHOLD]->(t:Threshold)
RETURN d.id AS derivedFile, proc.id AS procedure, count(t) AS thresholdsToRecheck, collect(t.id) AS thresholds
