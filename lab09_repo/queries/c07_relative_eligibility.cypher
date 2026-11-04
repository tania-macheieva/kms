// CQ11-CQ15: шанс успадкування (з вузла Concept), вік і чи можна тестувати відповідно до процедури CT-01.
// Конструкції: JOIN через три мітки, WHERE, обчислюваний стовпець, ORDER BY.
MATCH (c:Procedure {id: 'CT-01'})-[:APPLIES_TO]->(p:Person)-[:INSTANCE_OF]->(k:Concept)
WHERE k.probability IS NOT NULL
RETURN p.name AS person, k.name AS degree, k.probability AS probability, p.ageYears AS age,
       CASE WHEN p.ageYears >= c.minTestingAge THEN 'так' ELSE 'ні' END AS canTest
ORDER BY probability DESC, person
