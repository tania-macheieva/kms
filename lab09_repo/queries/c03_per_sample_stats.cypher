// CQ08: Який обсяг даних і яка якість по зразках (чи малий набір для VQSR)? 
// Конструкції: агрегації count/avg/min/max з групуванням за зразком.
MATCH (v:Variant)-[:FROM_SAMPLE]->(s:Sample)
OPTIONAL MATCH (v)-[:HAS_ANNOTATION]->(a:Annotation {name: 'QD'})
RETURN s.code AS sample, count(DISTINCT v) AS variants, round(avg(a.value) * 100) / 100 AS avgQD, min(a.value) AS minQD, max(a.value) AS maxQD
ORDER BY sample
