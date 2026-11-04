"""Генерує llm_log/prompts/v1.txt, v2.txt (шаблони) та вхідні файли llm_log/in/{v}_{batch}.txt для сліпих генераторів (без еталонів)."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import t2s  # noqa: E402

ROOT = t2s.ROOT
V1 = """Ти пишеш SPARQL-запити до RDF-графа знань (біомедичні дані: варіанти, гени, родичі). Нижче — схема графа.
Префікси dkh:, rdf:, rdfs:, owl:, xsd: додаються автоматично, їх у запиті можна не оголошувати.

{schema}

Завдання: для питання користувача напиши один SPARQL 1.1 запит. Поверни лише запит.

Питання: {question}"""
V2 = """Ти пишеш SPARQL-запити до RDF-графа знань (біомедичні дані: варіанти, гени, родичі). Префікси dkh:, rdf:, rdfs:, owl:, xsd: додаються автоматично.

Правила (виведені з аналізу помилок першої версії промпту на dev-питаннях):
1. Використовуй лише класи, властивості та індивіди зі схеми нижче; не вигадуй імен.
2. Граф НЕ містить повного виведення (reasoning): типи dkh:GeneticVariant, dkh:QualityAnnotation та інші надкласи присутні лише для частини вузлів. Тому не добирай вузли через `a <надклас>`. Замість цього спирайся на властивості: варіант — це вузол із dkh:hasVariantId; анотація — вузол із dkh:hasAnnotationName і dkh:hasNumericValue; типи SNP/Indel (dkh:SNP, dkh:Indel) явно задані для варіантів.
3. Анотації якості: ?v dkh:hasAnnotation ?a . ?a dkh:hasAnnotationName "QD" ; dkh:hasNumericValue ?x (імена "QD", "FS", "SOR", "MQ"; числа — xsd:decimal).
4. Клінічна значущість — це індивід (dkh:Pathogenic, dkh:Benign), у нього НЕМАЄ rdfs:label; порівнюй IRI напряму: ?v dkh:hasClinicalSignificance dkh:Pathogenic.
5. Дані зберігаються у кількох іменованих графах, тож дублікати рядків можливі: у SELECT завжди пиши DISTINCT, а в підрахунках COUNT(DISTINCT ...).
6. Повертай лише ті стовпці, про які запитано (наприклад, лише ідентифікатор, без IRI вузла).
7. Мітки (назви) мають вигляд rdfs:label.

Приклади (не з тестового набору):
Питання: Які варіанти мають значення SOR більше за 3? Виведіть ідентифікатори.
SELECT DISTINCT ?id WHERE { ?v dkh:hasVariantId ?id ; dkh:hasAnnotation ?a . ?a dkh:hasAnnotationName "SOR" ; dkh:hasNumericValue ?x . FILTER (?x > 3.0) }
Питання: Скільки анотацій має ім'я MQ?
SELECT (COUNT(DISTINCT ?a) AS ?n) WHERE { ?a dkh:hasAnnotationName "MQ" }

{schema}

Завдання: для питання користувача напиши один SPARQL 1.1 запит. Поверни лише запит у блоці ```sparql.

Питання: {question}"""
(ROOT / "llm_log/prompts/v1.txt").write_text(V1, encoding="utf-8")
(ROOT / "llm_log/prompts/v2.txt").write_text(V2, encoding="utf-8")


def build(version, batches=2):
    tpl = {"v1": V1, "v2": V2}[version]
    qs = [json.loads(l) for l in (ROOT / "tests/t2s.jsonl").read_text(encoding="utf-8").splitlines()]
    schema = t2s.schema_text()
    for b in range(batches):
        part = qs[b::batches]
        head = tpl.split("Питання: {question}")[0].replace("{schema}", schema)
        body = "\n".join(f"{q['id']}: {q['question']}" for q in part)
        (ROOT / f"llm_log/in/{version}_b{b+1}.txt").write_text(head + "\n\nПитання (для КОЖНОГО окремо напиши запит; відповідай незалежно одне від одного):\n" + body + "\n", encoding="utf-8")


if __name__ == "__main__":
    for v in ("v1", "v2"): build(v)
    print(sorted(p.name for p in (ROOT / "llm_log/in").iterdir()))
