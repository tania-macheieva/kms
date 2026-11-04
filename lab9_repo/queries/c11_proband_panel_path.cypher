// CQ17: Чи потрапляє варіант пробанда в ген панелі, для якої доречне каскадне тестування? (шлях з 3 зв'язків)
MATCH (p:Person {proband: true})-[:CARRIES]->(v:Variant)-[:LOCATED_IN]->(g:Gene)<-[:HAS_MEMBER]-(panel:GenePanel)
RETURN p.name AS proband, v.id AS variant, v.clinicalSignificance AS significance, g.symbol AS gene, panel.name AS panel
