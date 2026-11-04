// CQ01: За якого QD SNP-варіант отримує прапорець LowQD? -> SNP із QD < 2.
// Конструкції: MATCH з міткою та властивістю, фільтр WHERE, сортування.
MATCH (v:Variant {type: 'SNP'})-[:HAS_ANNOTATION]->(a:Annotation {name: 'QD'})
WHERE a.value < 2.0
RETURN v.id AS variant, a.value AS qd
ORDER BY qd, variant
