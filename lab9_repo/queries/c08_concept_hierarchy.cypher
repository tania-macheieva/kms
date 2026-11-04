// Скільки варіантів належить кожному предку в ієрархії класів (INSTANCE_OF + SUBCLASS_OF*)?
// Конструкції: змінна довжина *0..4 (0 = сам клас), агрегація за предком.
MATCH (v:Variant)-[:INSTANCE_OF]->(:Concept)-[:SUBCLASS_OF*0..4]->(anc:Concept)
RETURN anc.name AS concept, count(DISTINCT v) AS variants
ORDER BY variants DESC, concept
