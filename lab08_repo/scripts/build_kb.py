"""Будує data/kb.ttl (union) і data/graphs/{tbox,abox,inferred}.ttl: онтологія + індивіди ЛР7 + синтетична когорта (seed 42) + виведення HermiT.
Синтетичні дані: вигадані зразки/варіанти; значення анотацій згенеровано випадково в правдоподібних діапазонах."""
import json
import random
import sys
from pathlib import Path

from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import OWL, RDF, RDFS, XSD

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from reasoning import infer   # noqa: E402

D = Namespace("http://example.org/dkh/onto#")
SEED = 42
rnd = random.Random(SEED)


def dec(x): return Literal(f"{x:.1f}", datatype=XSD.decimal)


def load_lab7():
    tbox = Graph().parse(ROOT / "data/lab7/onto.owl", format="turtle")
    abox = Graph().parse(ROOT / "data/lab7/onto_data.ttl", format="turtle")
    for s in set(abox.subjects(OWL.imports, None)): abox.remove((s, None, None))
    return tbox, abox


def cohort(abox, tbox):
    """Розширення схеми (Sample, fromSample) + 3 зразки по 20 варіантів."""
    for t in ((D.Sample, RDF.type, OWL.Class), (D.Sample, RDFS.label, Literal("sample", lang="en")), (D.fromSample, RDF.type, OWL.ObjectProperty), (D.fromSample, RDFS.label, Literal("from sample", lang="en")),
              (D.fromSample, RDFS.domain, D.GeneticVariant), (D.fromSample, RDFS.range, D.Sample), (D.hasSampleCode, RDF.type, OWL.DatatypeProperty), (D.hasSampleCode, RDFS.range, XSD.string),
              (D.hasSampleCode, RDFS.label, Literal("has sample code", lang="en"))):
        tbox.add(t)
    genes = ["BRCA1", "BRCA2", "PALB2", "TP53"]
    n = 100
    for sc in ("A", "B", "C"):
        s = D[f"SAMPLE-{sc}"]
        for t in ((s, RDF.type, OWL.NamedIndividual), (s, RDF.type, D.Sample), (s, RDFS.label, Literal(f"SAMPLE-{sc}", lang="en")), (s, D.hasSampleCode, Literal(sc))): abox.add(t)
        for _ in range(20):
            n += 1
            v = D[f"VAR-{n}"]; snp = rnd.random() < 0.75
            qd = rnd.uniform(0.5, 3.0) if rnd.random() < 0.12 else rnd.uniform(2.0, 35.0)
            fs = (rnd.uniform(61, 120) if snp else rnd.uniform(201, 320)) if rnd.random() < 0.08 else (rnd.uniform(0, 20) if snp else rnd.uniform(0, 150))
            sor = rnd.uniform(0.2, 5.0); mq = rnd.uniform(30.0, 70.0)
            for t in ((v, RDF.type, OWL.NamedIndividual), (v, RDF.type, D.SNP if snp else D.Indel), (v, RDFS.label, Literal(f"VAR-{n}", lang="en")), (v, D.hasVariantId, Literal(f"VAR-{n}")),
                      (v, D.locatedIn, D[rnd.choice(genes)]), (v, D.fromSample, s)): abox.add(t)
            if rnd.random() < 0.1: abox.add((v, D.hasExonEndPosition, Literal(True)))
            for cls, name, val in (("QualityByDepth", "QD", qd), ("FisherStrandBias", "FS", fs), ("StrandOddsRatio", "SOR", sor), ("MappingQuality", "MQ", mq)):
                a = D[f"VAR-{n}_{cls}"]
                for t in ((a, RDF.type, OWL.NamedIndividual), (a, RDF.type, D[cls]), (a, RDFS.label, Literal(f"{cls} of VAR-{n}", lang="en")), (a, D.hasNumericValue, dec(val)), (a, D.hasAnnotationName, Literal(name)), (a, D.isAnnotationOf, v)): abox.add(t)
                abox.add((v, D.hasAnnotation, a))
    for vid in (103, 131, 152):   # три патогенні в когорті
        abox.add((D[f"VAR-{vid}"], D.hasClinicalSignificance, D.Pathogenic))
    # VAR-001..004 (з ЛР7) також належать зразку A
    for k in range(1, 5): abox.add((D[f"VAR-00{k}"], D.fromSample, D["SAMPLE-A"]))


def main():
    tbox, abox = load_lab7()
    cohort(abox, tbox)
    u = Graph()
    for g in (tbox, abox):
        for t in g: u.add(t)
    ok, inf, msg = infer(u)
    assert ok, msg[:200]
    # залишаємо виведені твердження: типи індивідів і класифікацію класів
    inferred = Graph()
    for s, p, o in inf:
        if p == RDF.type and (s, RDF.type, OWL.NamedIndividual) not in abox: continue
        inferred.add((s, p, o))
    for g in (tbox, abox, inferred):
        for pfx, ns in (("dkh", D), ("owl", OWL), ("rdfs", RDFS), ("xsd", XSD)): g.bind(pfx, ns)
    (ROOT / "data/graphs").mkdir(exist_ok=True)
    tbox.serialize(ROOT / "data/graphs/tbox.ttl", format="turtle"); abox.serialize(ROOT / "data/graphs/abox.ttl", format="turtle"); inferred.serialize(ROOT / "data/graphs/inferred.ttl", format="turtle")
    kb = Graph()
    for pfx, ns in (("dkh", D), ("owl", OWL), ("rdfs", RDFS), ("xsd", XSD), ("skos", Namespace("http://www.w3.org/2004/02/skos/core#"))): kb.bind(pfx, ns)
    for g in (tbox, abox, inferred):
        for t in g: kb.add(t)
    kb.serialize(ROOT / "data/kb.ttl", format="turtle")
    print(json.dumps({"tbox": len(tbox), "abox": len(abox), "inferred": len(inferred), "kb_union": len(kb)}))


if __name__ == "__main__":
    main()
