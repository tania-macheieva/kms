"""Будує tests/t2s.jsonl: питання (укр.), еталонний SPARQL і еталонна відповідь (обчислена виконанням еталонного запиту на сховищі).
split: dev (18) — на них аналізуються помилки й покращується промпт; heldout (6) — не розглядаються при створенні v2."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from store import ROOT, open_store  # noqa: E402
import t2s  # noqa: E402

Q = [
 ("d01", "dev", "Які SNP-варіанти мають значення QD менше за 2? Виведіть їхні ідентифікатори (hasVariantId).",
  'SELECT DISTINCT ?id WHERE { ?v a dkh:SNP ; dkh:hasVariantId ?id ; dkh:hasAnnotation ?a . ?a dkh:hasAnnotationName "QD" ; dkh:hasNumericValue ?x . FILTER (?x < 2.0) }'),
 ("d02", "dev", "Скільки варіантів належить зразку з кодом B?",
  'SELECT (COUNT(DISTINCT ?v) AS ?n) WHERE { ?v dkh:fromSample ?s . ?s dkh:hasSampleCode "B" }'),
 ("d03", "dev", "Які гени (їхні мітки rdfs:label) входять до панелі HBOC-panel?",
  'SELECT DISTINCT ?l WHERE { dkh:HBOC-panel dkh:hasMember ?g . ?g rdfs:label ?l }'),
 ("d04", "dev", "Чи має варіант VAR-103 клінічну значущість Pathogenic?",
  'ASK { dkh:VAR-103 dkh:hasClinicalSignificance dkh:Pathogenic }'),
 ("d05", "dev", "Скільки варіантів розташовано в кожному гені? Виведіть мітку гена та кількість.",
  'SELECT ?l (COUNT(DISTINCT ?v) AS ?n) WHERE { ?v dkh:locatedIn ?g . ?g rdfs:label ?l } GROUP BY ?l'),
 ("d06", "dev", "Яке найбільше значення FS серед усіх варіантів?",
  'SELECT (MAX(?x) AS ?m) WHERE { ?a dkh:hasAnnotationName "FS" ; dkh:hasNumericValue ?x }'),
 ("d07", "dev", "Які варіанти розташовані в гені TP53? Виведіть їхні ідентифікатори.",
  'SELECT DISTINCT ?id WHERE { ?v dkh:locatedIn dkh:TP53 ; dkh:hasVariantId ?id }'),
 ("d08", "dev", "Скільки років Sofiia?",
  'SELECT ?age WHERE { dkh:Sofiia dkh:hasAgeYears ?age }'),
 ("d09", "dev", "Хто є батьками Olena? Виведіть мітки.",
  'SELECT DISTINCT ?l WHERE { dkh:Olena dkh:hasParent ?p . ?p rdfs:label ?l }'),
 ("d10", "dev", "Хто є дітьми Maria? Виведіть мітки.",
  'SELECT DISTINCT ?l WHERE { dkh:Maria dkh:hasChild ?c . ?c rdfs:label ?l }'),
 ("d11", "dev", "Які варіанти мають клінічну значущість Pathogenic? Виведіть ідентифікатори.",
  'SELECT DISTINCT ?id WHERE { ?v dkh:hasClinicalSignificance dkh:Pathogenic ; dkh:hasVariantId ?id }'),
 ("d12", "dev", "Які числові значення мають пороги фільтрації для анотації FS?",
  'SELECT DISTINCT ?x WHERE { ?t a dkh:FilterThreshold ; dkh:onAnnotationName "FS" ; dkh:hasThresholdValue ?x }'),
 ("d13", "dev", "Які особи старші за 60 років? Виведіть мітки.",
  'SELECT DISTINCT ?l WHERE { ?p a dkh:Person ; dkh:hasAgeYears ?a ; rdfs:label ?l . FILTER (?a > 60) }'),
 ("d14", "dev", "Скільки існує анотацій з іменем QD?",
  'SELECT (COUNT(DISTINCT ?a) AS ?n) WHERE { ?a dkh:hasAnnotationName "QD" }'),
 ("d15", "dev", "Яке середнє значення SOR для кожного зразка? Виведіть код зразка та середнє.",
  'SELECT ?c (AVG(?x) AS ?m) WHERE { ?v dkh:fromSample ?s ; dkh:hasAnnotation ?a . ?s dkh:hasSampleCode ?c . ?a dkh:hasAnnotationName "SOR" ; dkh:hasNumericValue ?x } GROUP BY ?c'),
 ("d16", "dev", "Які Indel-варіанти належать зразку A? Виведіть ідентифікатори.",
  'SELECT DISTINCT ?id WHERE { ?v a dkh:Indel ; dkh:fromSample dkh:SAMPLE-A ; dkh:hasVariantId ?id }'),
 ("d17", "dev", "Які SNP-варіанти мають FS більше за 60?",
  'SELECT DISTINCT ?id WHERE { ?v a dkh:SNP ; dkh:hasVariantId ?id ; dkh:hasAnnotation ?a . ?a dkh:hasAnnotationName "FS" ; dkh:hasNumericValue ?x . FILTER (?x > 60.0) }'),
 ("d18", "dev", "Чи існує варіант у гені BRCA1 із клінічною значущістю Benign?",
  'ASK { ?v dkh:locatedIn dkh:BRCA1 ; dkh:hasClinicalSignificance dkh:Benign }'),
 ("h01", "heldout", "Хто є предками Olena (батьки, їхні батьки тощо)? Виведіть мітки.",
  'SELECT DISTINCT ?l WHERE { dkh:Olena dkh:hasParent+ ?p . ?p rdfs:label ?l }'),
 ("h02", "heldout", "Який варіант має найменше значення MQ? Виведіть його ідентифікатор.",
  'SELECT ?id WHERE { ?v dkh:hasVariantId ?id ; dkh:hasAnnotation ?a . ?a dkh:hasAnnotationName "MQ" ; dkh:hasNumericValue ?x } ORDER BY ?x LIMIT 1'),
 ("h03", "heldout", "Скільки Indel-варіантів у зразку C?",
  'SELECT (COUNT(DISTINCT ?v) AS ?n) WHERE { ?v a dkh:Indel ; dkh:fromSample ?s . ?s dkh:hasSampleCode "C" }'),
 ("h04", "heldout", "Які гени мають більше п'ятнадцяти варіантів? Виведіть мітки.",
  'SELECT ?l WHERE { ?v dkh:locatedIn ?g . ?g rdfs:label ?l } GROUP BY ?l HAVING (COUNT(DISTINCT ?v) > 15)'),
 ("h05", "heldout", "Які варіанти в гені PALB2 не мають вказаної клінічної значущості? Виведіть ідентифікатори.",
  'SELECT DISTINCT ?id WHERE { ?v dkh:locatedIn dkh:PALB2 ; dkh:hasVariantId ?id . FILTER NOT EXISTS { ?v dkh:hasClinicalSignificance ?s } }'),
 ("h06", "heldout", "Який шанс успадкування (hasInheritanceProbability) визначено для класу SecondDegreeRelative?",
  'SELECT DISTINCT ?p WHERE { dkh:SecondDegreeRelative rdfs:subClassOf ?r . ?r owl:onProperty dkh:hasInheritanceProbability ; owl:hasValue ?p }'),
]


def main():
    st = open_store(); rows = []
    for qid, split, text, gold in Q:
        r = t2s.execute(st, gold, limit=None)
        assert r["ok"], (qid, r)
        rows.append({"id": qid, "split": split, "question": text, "gold_query": gold, "gold_answer": r["canon"]})
        print(qid, split, str(r["canon"])[:110])
    (ROOT / "tests").mkdir(exist_ok=True)
    with open(ROOT / "tests/t2s.jsonl", "w", encoding="utf-8") as f:
        for x in rows: f.write(json.dumps(x, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
