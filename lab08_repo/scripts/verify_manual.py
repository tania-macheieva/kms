"""Незалежна перевірка результатів SPARQL-запитів: ті самі відповіді обчислюються звичайним Python-кодом
по тріплах abox.ttl (rdflib, ітерація без SPARQL). Збіг/розбіжність пишеться в queries/results/manual_verification.json."""
import json
from collections import defaultdict, deque
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

from rdflib import Graph, Namespace, RDF
from rdflib.namespace import RDFS

ROOT = Path(__file__).resolve().parents[1]
D = Namespace("http://example.org/dkh/onto#")
g = Graph().parse(ROOT / "data/graphs/abox.ttl", format="turtle")
res = json.loads((ROOT / "queries/results/results.json").read_text(encoding="utf-8"))
loc = lambda x: str(x).replace(str(D), "")
out = {}

# --- V-q01: SNP з QD<2
ann = {}
for v in g.subjects(RDF.type, D.SNP):
    for a in g.objects(v, D.hasAnnotation):
        if str(g.value(a, D.hasAnnotationName)) == "QD": ann[loc(v)] = float(g.value(a, D.hasNumericValue))
exp = sorted(((k, x) for k, x in ann.items() if x < 2.0), key=lambda t: (t[1], t[0]))
got = [(r[0].replace("dkh:", ""), float(r[1])) for r in res["q01_select_filter_lowqd.rq"]["rows"]]
out["q01"] = {"expected": exp, "sparql": got, "match": exp == got}

# --- V-q04: кількість варіантів і середнє QD по зразках
byS = defaultdict(list)
for v in g.subjects(D.fromSample, None):
    s = str(g.value(g.value(v, D.fromSample), D.hasSampleCode))
    for a in g.objects(v, D.hasAnnotation):
        if str(g.value(a, D.hasAnnotationName)) == "QD": byS[s].append(float(g.value(a, D.hasNumericValue)))
# Увага: середнє для C точно дорівнює 16.915; SPARQL ROUND() округлює «половину вгору» (16.92), а round() у Python на float дав би 16.91.
# Тому для звірки використовується Decimal з ROUND_HALF_UP (перша спроба з round() дала хибну «розбіжність»).
avg = lambda x: float((sum(Decimal(str(i)) for i in x) / len(x)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
exp = {s: (len(x), avg(x), min(x), max(x)) for s, x in sorted(byS.items())}
got = {r[0]: (int(r[1]), float(r[2]), float(r[3]), float(r[4])) for r in res["q04_aggregate_per_sample.rq"]["rows"]}
out["q04"] = {"expected": exp, "sparql": got, "match": exp == got}

# --- V-q06: родичі через ланцюжок зв'язків (BFS)
adj = defaultdict(set)
for p in (D.hasParent, D.hasChild, D.hasSibling):
    for s, o in g.subject_objects(p):
        adj[s].add(o)
        if p == D.hasParent: adj[o].add(s)   # ^hasParent
        if p == D.hasChild: adj[o].add(s)
# Увага: запит використовує hasParent|hasChild|hasSibling|^hasParent|^hasChild (hasSibling лише в прямому напрямку)
adj2 = defaultdict(set)
for s, o in g.subject_objects(D.hasParent): adj2[s].add(o); adj2[o].add(s)
for s, o in g.subject_objects(D.hasChild): adj2[s].add(o); adj2[o].add(s)
for s, o in g.subject_objects(D.hasSibling): adj2[s].add(o)
seen, dq = set(), deque([D.Olena])
while dq:
    x = dq.popleft()
    for y in adj2[x]:
        if y not in seen: seen.add(y); dq.append(y)
seen.discard(D.Olena)
exp = sorted(str(g.value(x, RDFS.label)) for x in seen)
got = [r[0] for r in res["q06_property_path_relatives.rq"]["rows"]]
out["q06"] = {"expected": exp, "sparql": got, "match": exp == got}

# --- V-q08: шанс/вік/можливість тестування; ступінь береться з inferred.ttl, шанс — з правил TBox за ЛР4 (CDC): 1° = 0.5, 2° = 0.25, 3° = 0.125
inf = Graph().parse(ROOT / "data/graphs/inferred.ttl", format="turtle")
P = {"FirstDegreeRelative": 0.5, "SecondDegreeRelative": 0.25, "ThirdDegreeRelative": 0.125}
exp = []
for cls, pr in P.items():
    for p in inf.subjects(RDF.type, D[cls]):
        age = g.value(p, D.hasAgeYears)
        if age is not None: exp.append((str(g.value(p, RDFS.label)), pr, int(age), "так" if int(age) >= 18 else "ні"))
exp.sort(key=lambda t: (-t[1], t[0]))
got = [(r[0], float(r[2]), int(r[3]), r[4]) for r in res["q08_relatives_probability_age.rq"]["rows"]]
out["q08"] = {"expected": exp, "sparql": got, "match": exp == got}

(ROOT / "queries/results/manual_verification.json").write_text(json.dumps(out, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
for k, v in out.items(): print(k, "OK" if v["match"] else "РОЗБІЖНІСТЬ", v if not v["match"] else "")
