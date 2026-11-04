"""Порівняння SPARQL (pyoxigraph, RDF-граф ЛР8) та Cypher (FalkorDB, LPG) на 5 однакових питаннях. → docs/evidence/compare.json"""
import json
import re
import statistics
import sys
import time
from pathlib import Path

import pyoxigraph as ox

sys.path.insert(0, str(Path(__file__).parent))
import graphdb as gdb  # noqa: E402
import t2c  # noqa: E402
from store import PREFIXES  # noqa: E402

ROOT = gdb.ROOT
HDR = "".join(f"PREFIX {k}: <{v}>\n" for k, v in PREFIXES.items())
store = ox.Store()
for n in ("tbox", "abox", "inferred"): store.load(path=str(ROOT / f"data/graphs/{n}.ttl"), format=ox.RdfFormat.TURTLE, to_graph=ox.NamedNode(f"urn:g:{n}"))

P = [
 ("P1", "SNP-варіанти з QD < 2",
  'SELECT DISTINCT ?id WHERE { ?v a dkh:SNP ; dkh:hasVariantId ?id ; dkh:hasAnnotation ?a . ?a dkh:hasAnnotationName "QD" ; dkh:hasNumericValue ?x . FILTER (?x < 2.0) }',
  "MATCH (v:Variant {type:'SNP'})-[:HAS_ANNOTATION]->(a:Annotation {name:'QD'}) WHERE a.value < 2.0 RETURN DISTINCT v.id"),
 ("P2", "Кількість варіантів і середній QD по зразках (внутрішнє з'єднання з анотацією QD)",
  'SELECT ?c (COUNT(DISTINCT ?v) AS ?n) (ROUND(AVG(?x) * 100) / 100 AS ?avg) WHERE { ?v dkh:fromSample ?s ; dkh:hasAnnotation ?a . ?s dkh:hasSampleCode ?c . ?a dkh:hasAnnotationName "QD" ; dkh:hasNumericValue ?x } GROUP BY ?c',
  "MATCH (v:Variant)-[:FROM_SAMPLE]->(s:Sample), (v)-[:HAS_ANNOTATION]->(a:Annotation {name:'QD'}) RETURN s.code, count(DISTINCT v), round(avg(a.value) * 100) / 100"),
 ("P3", "Предки Olena (транзитивно)",
  'SELECT DISTINCT ?l WHERE { dkh:Olena dkh:hasParent+ ?p . ?p rdfs:label ?l }',
  "MATCH (:Person {name:'Olena'})-[:HAS_PARENT*1..]->(p:Person) RETURN DISTINCT p.name"),
 ("P4", "Кількість варіантів у кожному гені",
  'SELECT ?l (COUNT(DISTINCT ?v) AS ?n) WHERE { ?v dkh:locatedIn ?g . ?g rdfs:label ?l } GROUP BY ?l',
  "MATCH (v:Variant)-[:LOCATED_IN]->(g:Gene) RETURN g.symbol, count(DISTINCT v)"),
 ("P5", "Родичі зі ступенем, шансом успадкування, віком і можливістю тестування (≥ 18)",
  'SELECT DISTINCT ?name ?class ?prob ?age ?can WHERE { ?p dkh:hasAgeYears ?age ; rdfs:label ?name ; a ?class . ?class rdfs:subClassOf ?r . ?r owl:onProperty dkh:hasInheritanceProbability ; owl:hasValue ?prob . dkh:CT-01 dkh:hasMinTestingAge ?min . BIND (IF(?age >= ?min, "так", "ні") AS ?can) }',
  "MATCH (p:Person)-[:INSTANCE_OF]->(k:Concept) WHERE k.probability IS NOT NULL MATCH (c:Procedure {id:'CT-01'}) RETURN p.name, k.name, k.probability, p.ageYears, CASE WHEN p.ageYears >= c.minTestingAge THEN 'так' ELSE 'ні' END"),
]


def norm_sparql(res):
    def n(t):
        if t is None: return ""
        v = t.value
        if isinstance(t, ox.Literal) and t.datatype and t.datatype.value.endswith(("decimal", "integer", "double")): return f"{float(v):.6g}"
        return v.replace(PREFIXES["dkh"], "")
    vs = [v.value for v in res.variables]
    return sorted([n(s[v]) for v in vs] for s in res)


def size(q):
    s = re.sub(r"(?m)^\s*(#|//).*$", "", q); s = re.sub(r"\s+", " ", s).strip(); return len(s), len(s.split(" "))


def timed(fn, reps=5):
    fn(); ts = []
    for _ in range(reps):
        t = time.perf_counter(); r = fn(); ts.append((time.perf_counter() - t) * 1000)
    return r, round(statistics.median(ts), 2)


out = []
for pid, title, sq, cq in P:
    rs, ts = timed(lambda: norm_sparql(store.query(HDR + sq, use_default_graph_as_union=True)))
    rc, tc = timed(lambda: t2c.canon(gdb.graph().ro_query(cq).result_set))
    # Cypher: імена зведено до коротких (dkh: прибрано в SPARQL normalizer); порівняння як множини рядків
    out.append({"id": pid, "title": title, "sparql": sq, "cypher": cq, "sparql_rows": rs, "cypher_rows": rc, "equal": rs == rc, "sparql_ms": ts, "cypher_ms": tc, "sparql_len": size(sq), "cypher_len": size(cq)})
# додаткові варіанти для пояснення розбіжностей
extra = {}
q = "MATCH (v:Variant)-[:FROM_SAMPLE]->(s:Sample) OPTIONAL MATCH (v)-[:HAS_ANNOTATION]->(a:Annotation {name:'QD'}) RETURN s.code, count(DISTINCT v), round(avg(a.value) * 100) / 100"
extra["P2_cypher_all_variants"] = t2c.canon(gdb.graph().ro_query(q).result_set)
q = "MATCH (p:Person)-[:INSTANCE_OF]->(k:Concept) WHERE k.probability IS NOT NULL AND p.ageYears IS NOT NULL MATCH (c:Procedure {id:'CT-01'}) RETURN p.name, k.name, k.probability, p.ageYears, CASE WHEN p.ageYears >= c.minTestingAge THEN 'так' ELSE 'ні' END"
extra["P5_cypher_with_age"] = t2c.canon(gdb.graph().ro_query(q).result_set)
(ROOT / "docs/evidence").mkdir(parents=True, exist_ok=True)
(ROOT / "docs/evidence/compare.json").write_text(json.dumps({"pairs": out, "extra": extra}, ensure_ascii=False, indent=1), encoding="utf-8")
for o in out: print(o["id"], o["equal"], o["sparql_ms"], o["cypher_ms"], o["sparql_len"], o["cypher_len"])
if not all(o["equal"] for o in out):
    for o in out:
        if not o["equal"]: print(o["id"], "\n S:", o["sparql_rows"], "\n C:", o["cypher_rows"])
