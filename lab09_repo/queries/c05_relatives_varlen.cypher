// CQ11-CQ13/CQ14: Хто є родичем пробанда Olena і через скільки родинних кроків?
// Конструкції: шлях змінної довжини *1..4 за кількома типами зв'язків без напрямку, DISTINCT, агрегація min(length).
MATCH p = (o:Person {name: 'Olena'})-[:HAS_PARENT|HAS_SIBLING*1..4]-(r:Person)
WHERE r <> o
RETURN r.name AS relative, min(length(p)) AS steps
ORDER BY steps, relative
