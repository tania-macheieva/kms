// CQ14/CQ17: Які гени панелі мають патогенні варіанти (і які — жодного)?
// Конструкції: OPTIONAL MATCH (гени без патогенних варіантів не зникають), WITH, умовний підрахунок.
MATCH (:GenePanel {name: 'HBOC-panel'})-[:HAS_MEMBER]->(g:Gene)
OPTIONAL MATCH (g)<-[:LOCATED_IN]-(v:Variant)
WHERE v.clinicalSignificance = 'Pathogenic'
WITH g, count(v) AS pathogenic, collect(v.id) AS ids
RETURN g.symbol AS gene, pathogenic, ids
ORDER BY pathogenic DESC, gene
