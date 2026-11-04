// CQ05: Чи достатньо одного прапорця, щоб відхилити варіант? -> пороги беруться з ГРАФА (вузли Threshold), а не з тексту запиту.
// Конструкції: шлях з 4 зв'язків, WITH + агрегація collect/count, фільтр після агрегації, CASE.
MATCH (t:Threshold)-[:CHECKS]->(:AnnotationType)<-[:OF_TYPE]-(a:Annotation)<-[:HAS_ANNOTATION]-(v:Variant)
WHERE (t.variantType = 'all' OR t.variantType = toUpper(v.type))
  AND ((t.op = '<' AND a.value < t.value) OR (t.op = '>' AND a.value > t.value))
WITH v, collect(t.id) AS flags
WHERE size(flags) >= 1
RETURN v.id AS variant, size(flags) AS nFlags, flags
ORDER BY nFlags DESC, variant
LIMIT 10
