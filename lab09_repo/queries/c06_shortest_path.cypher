// CQ13: Яка найкоротша родинна лінія від пробанда до Maria?
// Конструкції: shortestPath (у FalkorDB — лише в RETURN/WITH і лише спрямований).
MATCH (a:Person {name: 'Olena'}), (b:Person {name: 'Maria'})
WITH shortestPath((a)-[:HAS_PARENT*]->(b)) AS p
RETURN length(p) AS hops, [n IN nodes(p) | n.name] AS line
