"""Будує data/*.csv (вузли та зв'язки LPG) з RDF-графа ЛР8 (data/graphs/{tbox,abox,inferred}.ttl).
Властивості походження на кожному зв'язку: source, confidence, validFrom. Без випадковості (детермінований обхід, сортування)."""
import csv
import re
from pathlib import Path

from rdflib import Graph, Namespace, RDF, RDFS, OWL, URIRef, Literal

ROOT = Path(__file__).resolve().parents[1]
D = Namespace("http://example.org/dkh/onto#")
VALID_FROM = "2026-10-26"
g = Graph()
for n in ("tbox", "abox", "inferred"): g.parse(ROOT / f"data/graphs/{n}.ttl", format="turtle")
a = Graph().parse(ROOT / "data/graphs/abox.ttl", format="turtle")
inf = Graph().parse(ROOT / "data/graphs/inferred.ttl", format="turtle")
loc = lambda x: str(x).split("#")[-1]
val = lambda s, p: g.value(s, p)
types = lambda s: {loc(t) for t in a.objects(s, RDF.type) if str(t).startswith(str(D))}
SRC = {"cohort": ("synthetic-seed42", 0.8), "lab7": ("lab7-abox", 1.0), "gatk": ("gatk", 1.0), "cdc": ("cdc", 1.0), "hermit": ("hermit", 0.95)}

nodes = {k: [] for k in ("Variant", "Annotation", "AnnotationType", "Gene", "GenePanel", "Sample", "Person", "Diagnosis", "Threshold", "Procedure", "DataFile", "Instrument", "Situation", "Concept")}
rels = []   # (type, from_label, from_key, to_label, to_key, source)
def rel(t, fl, fk, tl, tk, src): rels.append((t, fl, fk, tl, tk, src))
is_cohort = lambda s: loc(s).startswith("VAR-1") or "SAMPLE" in loc(s)

# --- варіанти й анотації
ann_types = {}
for v in sorted(a.subjects(D.hasVariantId, None)):
    vid = str(val(v, D.hasVariantId)); t = "SNP" if D.SNP in set(a.objects(v, RDF.type)) else ("Indel" if D.Indel in set(a.objects(v, RDF.type)) else "Variant")
    cs = val(v, D.hasClinicalSignificance); ex = val(v, D.hasExonEndPosition)
    nodes["Variant"].append({"id": vid, "type": t, "clinicalSignificance": loc(cs) if cs else "", "exonEnd": str(ex).lower() if ex is not None else ""})
    src = "cohort" if is_cohort(v) else "lab7"
    for gn in a.objects(v, D.locatedIn): rel("LOCATED_IN", "Variant", vid, "Gene", loc(gn), src)
    for s in a.objects(v, D.fromSample): rel("FROM_SAMPLE", "Variant", vid, "Sample", str(val(s, D.hasSampleCode)), src)
    for an in sorted(a.objects(v, D.hasAnnotation)):
        nm = str(val(an, D.hasAnnotationName)); aid = loc(an)
        nodes["Annotation"].append({"id": aid, "name": nm, "value": str(val(an, D.hasNumericValue))})
        ann_types[nm] = 1
        rel("HAS_ANNOTATION", "Variant", vid, "Annotation", aid, src); rel("OF_TYPE", "Annotation", aid, "AnnotationType", nm, src)
for nm in ("QD", "FS", "SOR", "MQ", "MQRankSum", "ReadPosRankSum"): nodes["AnnotationType"].append({"name": nm})
# --- гени, панель, зразки
chrom = {}
for gn in sorted(a.subjects(RDF.type, D.Gene)) or []: pass
for gn in sorted({o for o in a.objects(None, D.locatedIn)}):
    nodes["Gene"].append({"symbol": loc(gn), "chromosome": str(val(gn, D.onChromosome) or "")})
for p in sorted(a.subjects(RDF.type, D.GenePanel)):
    nodes["GenePanel"].append({"name": loc(p)})
    for m in a.objects(p, D.hasMember): rel("HAS_MEMBER", "GenePanel", loc(p), "Gene", loc(m), "lab7")
for s in sorted(a.subjects(RDF.type, D.Sample)): nodes["Sample"].append({"code": str(val(s, D.hasSampleCode))})
# --- особи, діагнози
persons = sorted(set(a.subjects(RDF.type, D.Person)) | set(a.subjects(RDF.type, D.Proband)))
for p in persons:
    age = val(p, D.hasAgeYears); sex = val(p, D.hasSex); dec = val(p, D.isDeceased)
    nodes["Person"].append({"name": loc(p), "ageYears": str(age) if age is not None else "", "sex": str(sex) if sex else "", "deceased": str(dec).lower() if dec is not None else "", "proband": "true" if D.Proband in set(a.objects(p, RDF.type)) else "false"})
for p in persons:
    for q in sorted(a.objects(p, D.hasParent)): rel("HAS_PARENT", "Person", loc(p), "Person", loc(q), "lab7")
    for q in sorted(a.objects(p, D.hasChild)):   # зберігаємо як HAS_PARENT у зворотному напрямку, якщо ще немає
        if (q, D.hasParent, p) not in a: rel("HAS_PARENT", "Person", loc(q), "Person", loc(p), "lab7")
    for q in sorted(a.objects(p, D.hasSibling)): rel("HAS_SIBLING", "Person", loc(p), "Person", loc(q), "lab7")
    for q in sorted(a.objects(p, D.carries)): rel("CARRIES", "Person", loc(p), "Variant", str(val(q, D.hasVariantId)), "lab7")
    for dg in sorted(a.objects(p, D.hasDiagnosis)):
        nodes["Diagnosis"].append({"id": loc(dg), "kind": ", ".join(sorted(types(dg) - {"NamedIndividual"}))}); rel("HAS_DIAGNOSIS", "Person", loc(p), "Diagnosis", loc(dg), "lab7")
# --- пороги, процедури, файли, ситуації
for t in sorted(a.subjects(RDF.type, D.FilterThreshold)):
    nodes["Threshold"].append({"id": loc(t), "annotation": str(val(t, D.onAnnotationName)), "op": str(val(t, D.hasComparisonOperator)), "value": str(val(t, D.hasThresholdValue)), "variantType": str(val(t, D.forVariantType))})
    rel("CHECKS", "Threshold", loc(t), "AnnotationType", str(val(t, D.onAnnotationName)), "gatk")
for p in sorted(a.subjects(RDF.type, D.HardFiltering)) + sorted(a.subjects(RDF.type, D.CascadeTesting)):
    kind = "HardFiltering" if D.HardFiltering in set(a.objects(p, RDF.type)) else "CascadeTesting"
    nodes["Procedure"].append({"id": loc(p), "kind": kind, "minTestingAge": str(val(p, D.hasMinTestingAge) or "")})
    src = "gatk" if kind == "HardFiltering" else "cdc"
    for t in sorted(a.objects(p, D.hasThreshold)): rel("HAS_THRESHOLD", "Procedure", loc(p), "Threshold", loc(t), src)
    for t in sorted(a.objects(p, D.appliesTo)):
        if t in set(persons): rel("APPLIES_TO", "Procedure", loc(p), "Person", loc(t), src)
        else: rel("APPLIES_TO", "Procedure", loc(p), "DataFile", loc(t), src)
    for t in sorted(a.objects(p, D.hasProband)): rel("HAS_PROBAND", "Procedure", loc(p), "Person", loc(t), src)
    for t in sorted(a.objects(p, D.requires)): rel("REQUIRES", "Procedure", loc(p), "Variant", str(val(t, D.hasVariantId)), src)
for f in sorted(list(a.subjects(RDF.type, D.VCFFile)) + list(a.subjects(RDF.type, D.BAMFile))):
    nodes["DataFile"].append({"id": loc(f), "format": "VCF" if D.VCFFile in set(a.objects(f, RDF.type)) else "BAM", "label": str(val(f, RDFS.label))})
    for q in a.objects(f, D.derivedFrom): rel("DERIVED_FROM", "DataFile", loc(f), "DataFile", loc(q), "lab7")
    for q in a.objects(f, D.generatedBy): rel("GENERATED_BY", "DataFile", loc(f), "Instrument", loc(q), "lab7")
for i in sorted(a.subjects(RDF.type, D.Sequencer)): nodes["Instrument"].append({"id": loc(i)})
for s in sorted(a.subjects(RDF.type, D.SituationTemplate)):
    nodes["Situation"].append({"id": loc(s), "name": str(val(s, RDFS.label)), "guard": str(val(s, D.hasGuard))})
    for q in a.objects(s, D.guardClass): rel("GUARD_CLASS", "Situation", loc(s), "Concept", loc(q), "lab7")
# --- Concept: класи, що використовуються, та їхні предки (SUBCLASS_OF); INSTANCE_OF для варіантів, осіб, порогів
tb = Graph().parse(ROOT / "data/graphs/tbox.ttl", format="turtle")
prob = {}
for c in (D.FirstDegreeRelative, D.SecondDegreeRelative, D.ThirdDegreeRelative):
    for r in tb.objects(c, RDFS.subClassOf):
        if (r, OWL.onProperty, D.hasInheritanceProbability) in tb: prob[loc(c)] = str(tb.value(r, OWL.hasValue))
used = set()
def inst(label, key, cls, src="lab7"): used.add(cls); rel("INSTANCE_OF", label, key, "Concept", loc(cls), src)
for v in a.subjects(D.hasVariantId, None):
    for t in a.objects(v, RDF.type):
        if t in (D.SNP, D.Indel): inst("Variant", str(val(v, D.hasVariantId)), t, "cohort" if is_cohort(v) else "lab7")
for p in persons:
    for t in inf.objects(p, RDF.type):
        if loc(t) in prob: inst("Person", loc(p), t, "hermit")
    if D.Proband in set(a.objects(p, RDF.type)): inst("Person", loc(p), D.Proband)
for t in a.subjects(RDF.type, D.FilterThreshold): pass
used |= {D.GeneticVariant, D.Person}
for s in a.subjects(RDF.type, D.SituationTemplate):
    for q in a.objects(s, D.guardClass): used.add(q)
closure = set(); edges = []
def climb(c):
    if c in closure: return
    closure.add(c)
    for sup in sorted(tb.objects(c, RDFS.subClassOf)):
        if isinstance(sup, URIRef) and str(sup).startswith(str(D)): edges.append((c, sup)); climb(sup)
for c in sorted(used): climb(c)
for c in sorted(closure): nodes["Concept"].append({"name": loc(c), "probability": prob.get(loc(c), "")})
for c, s in sorted(set(edges)): rel("SUBCLASS_OF", "Concept", loc(c), "Concept", loc(s), "lab7")
# --- запис
out = ROOT / "data"; KEY = {"Variant": "id", "Annotation": "id", "AnnotationType": "name", "Gene": "symbol", "GenePanel": "name", "Sample": "code", "Person": "name", "Diagnosis": "id", "Threshold": "id", "Procedure": "id", "DataFile": "id", "Instrument": "id", "Situation": "id", "Concept": "name"}
for lab, rows in nodes.items():
    seen = set(); uniq = []
    for r in rows:
        if r[KEY[lab]] not in seen: seen.add(r[KEY[lab]]); uniq.append(r)
    nodes[lab] = uniq
    with open(out / f"nodes_{lab}.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, list(uniq[0])); w.writeheader(); w.writerows(uniq)
seen = set(); ru = []
for r in rels:
    if r[:5] not in seen: seen.add(r[:5]); ru.append(r)
by = {}
for t, fl, fk, tl, tk, src in ru: by.setdefault((t, fl, tl), []).append({"from": fk, "to": tk, "source": SRC[src][0], "confidence": SRC[src][1], "validFrom": VALID_FROM})
for (t, fl, tl), rows in sorted(by.items()):
    with open(out / f"rels_{t}__{fl}_{tl}.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, ["from", "to", "source", "confidence", "validFrom"]); w.writeheader(); w.writerows(rows)
print(sum(len(v) for v in nodes.values()), "вузлів;", len(ru), "зв'язків;", len(by), "типів;", {k: len(v) for k, v in nodes.items()})
