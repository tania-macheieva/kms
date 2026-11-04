"""tests/t2c.jsonl: питання, еталонний Cypher і еталонна відповідь (обчислена виконанням еталону)."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import t2c  # noqa: E402

Q = [
 ("t01", "Які SNP-варіанти мають значення QD менше за 2? Виведіть ідентифікатори.", "MATCH (v:Variant {type:'SNP'})-[:HAS_ANNOTATION]->(a:Annotation {name:'QD'}) WHERE a.value < 2.0 RETURN DISTINCT v.id"),
 ("t02", "Скільки варіантів належить зразку з кодом B?", "MATCH (v:Variant)-[:FROM_SAMPLE]->(:Sample {code:'B'}) RETURN count(DISTINCT v)"),
 ("t03", "Які гени входять до панелі HBOC-panel?", "MATCH (:GenePanel {name:'HBOC-panel'})-[:HAS_MEMBER]->(g:Gene) RETURN g.symbol"),
 ("t04", "Чи має варіант VAR-103 клінічну значущість Pathogenic?", "MATCH (v:Variant {id:'VAR-103'}) RETURN v.clinicalSignificance = 'Pathogenic'"),
 ("t05", "Скільки варіантів розташовано в кожному гені? Виведіть символ гена та кількість.", "MATCH (v:Variant)-[:LOCATED_IN]->(g:Gene) RETURN g.symbol, count(DISTINCT v)"),
 ("t06", "Яке найбільше значення FS серед усіх анотацій?", "MATCH (a:Annotation {name:'FS'}) RETURN max(a.value)"),
 ("t07", "Які варіанти розташовані в гені TP53? Виведіть ідентифікатори.", "MATCH (v:Variant)-[:LOCATED_IN]->(:Gene {symbol:'TP53'}) RETURN DISTINCT v.id"),
 ("t08", "Скільки років Sofiia?", "MATCH (p:Person {name:'Sofiia'}) RETURN p.ageYears"),
 ("t09", "Хто є батьками Olena?", "MATCH (:Person {name:'Olena'})-[:HAS_PARENT]->(p:Person) RETURN p.name"),
 ("t10", "Які особи старші за 60 років?", "MATCH (p:Person) WHERE p.ageYears > 60 RETURN p.name"),
 ("t11", "Які варіанти мають клінічну значущість Pathogenic? Виведіть ідентифікатори.", "MATCH (v:Variant {clinicalSignificance:'Pathogenic'}) RETURN v.id"),
 ("t12", "Хто є предками Olena (батьки, їхні батьки тощо)?", "MATCH (:Person {name:'Olena'})-[:HAS_PARENT*1..]->(p:Person) RETURN DISTINCT p.name"),
 ("t13", "Який варіант має найменше значення MQ? Виведіть його ідентифікатор.", "MATCH (v:Variant)-[:HAS_ANNOTATION]->(a:Annotation {name:'MQ'}) RETURN v.id ORDER BY a.value LIMIT 1"),
 ("t14", "Які гени мають більше п'ятнадцяти варіантів?", "MATCH (v:Variant)-[:LOCATED_IN]->(g:Gene) WITH g, count(DISTINCT v) AS n WHERE n > 15 RETURN g.symbol"),
 ("t15", "Скільки зв'язків у графі мають джерело hermit (виведені reasoner'ом)?", "MATCH ()-[r]->() WHERE r.source = 'hermit' RETURN count(r)"),
 ("t16", "Які пороги фільтрації перевіряють анотацію FS? Виведіть ідентифікатори порогів.", "MATCH (t:Threshold)-[:CHECKS]->(:AnnotationType {name:'FS'}) RETURN t.id"),
]

HARD = [
 ("t17", "Скільки SNP-варіантів мають значення FS більше за 60?", "MATCH (v:Variant {type:'SNP'})-[:HAS_ANNOTATION]->(a:Annotation {name:'FS'}) WHERE a.value > 60.0 RETURN count(DISTINCT v)"),
 ("t18", "Які гени панелі HBOC-panel мають патогенні варіанти, а які — жодного? Виведіть символ гена та кількість патогенних варіантів (нуль теж виведіть).", "MATCH (:GenePanel {name:'HBOC-panel'})-[:HAS_MEMBER]->(g:Gene) OPTIONAL MATCH (g)<-[:LOCATED_IN]-(v:Variant {clinicalSignificance:'Pathogenic'}) RETURN g.symbol, count(v)"),
 ("t19", "Яке середнє значення SOR для кожного зразка? Виведіть код зразка та середнє.", "MATCH (v:Variant)-[:FROM_SAMPLE]->(s:Sample), (v)-[:HAS_ANNOTATION]->(a:Annotation {name:'SOR'}) RETURN s.code, avg(a.value)"),
 ("t20", "Скільки кроків має найкоротший шлях від Olena до Maria за зв'язками HAS_PARENT?", "MATCH (a:Person {name:'Olena'}), (b:Person {name:'Maria'}) WITH shortestPath((a)-[:HAS_PARENT*]->(b)) AS p RETURN length(p)"),
 ("t21", "Які варіанти в гені PALB2 не мають вказаної клінічної значущості? Виведіть ідентифікатори.", "MATCH (v:Variant)-[:LOCATED_IN]->(:Gene {symbol:'PALB2'}) WHERE v.clinicalSignificance IS NULL RETURN v.id"),
 ("t22", "Які варіанти мають одночасно QD менше за 2 та SOR більше за 3? Виведіть ідентифікатори.", "MATCH (v:Variant)-[:HAS_ANNOTATION]->(q:Annotation {name:'QD'}), (v)-[:HAS_ANNOTATION]->(s:Annotation {name:'SOR'}) WHERE q.value < 2.0 AND s.value > 3.0 RETURN DISTINCT v.id"),
 ("t23", "Скільки різних значень source мають зв'язки в графі?", "MATCH ()-[r]->() RETURN count(DISTINCT r.source)"),
 ("t24", "Які особи мають шанс успадкування 0.5 за ступенем споріднення?", "MATCH (p:Person)-[:INSTANCE_OF]->(k:Concept) WHERE k.probability = 0.5 RETURN DISTINCT p.name"),
 ("t25", "До якої спільноти (community) належить Olena і скільки вузлів у цій спільноті?", "MATCH (o:Person {name:'Olena'}) MATCH (n) WHERE n.community = o.community RETURN o.community, count(n)"),
 ("t26", "Які процедури залежать від sample1_bam через похідні файли (DERIVED_FROM)? Виведіть ідентифікатори процедур.", "MATCH (:DataFile {id:'sample1_bam'})<-[:DERIVED_FROM*1..3]-(d:DataFile)<-[:APPLIES_TO]-(p:Procedure) RETURN DISTINCT p.id"),
 ("t27", "Скільки варіантів із QD менше за 2 є в кожному зразку? Виведіть код зразка та кількість.", "MATCH (v:Variant)-[:FROM_SAMPLE]->(s:Sample), (v)-[:HAS_ANNOTATION]->(a:Annotation {name:'QD'}) WHERE a.value < 2.0 RETURN s.code, count(DISTINCT v)"),
]


def main():
    rows = []
    for tier, lst in (('easy', Q), ('hard', HARD)):
      for qid, text, gold in lst:
        r = t2c.execute(gold, limit=False); assert r["ok"], (qid, r)
        rows.append({"id": qid, "tier": tier, "question": text, "gold_query": gold, "gold_answer": r["canon"]}); print(qid, str(r["canon"])[:90])
    with open(t2c.ROOT / "tests/t2c.jsonl", "w", encoding="utf-8") as f:
        for x in rows: f.write(json.dumps(x, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
