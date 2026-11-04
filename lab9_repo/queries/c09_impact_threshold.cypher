// АНАЛІЗ ВПЛИВУ 1: Якщо змінити поріг QD_lt_2 — на які варіанти та гени це вплине? (залежності на 5 кроків)
// Threshold -CHECKS-> AnnotationType <-OF_TYPE- Annotation <-HAS_ANNOTATION- Variant -LOCATED_IN-> Gene
MATCH (t:Threshold {id: 'QD_lt_2'})-[:CHECKS]->(:AnnotationType)<-[:OF_TYPE]-(:Annotation)<-[:HAS_ANNOTATION]-(v:Variant)-[:LOCATED_IN]->(g:Gene)
RETURN g.symbol AS gene, count(DISTINCT v) AS variantsAffected
ORDER BY variantsAffected DESC, gene
