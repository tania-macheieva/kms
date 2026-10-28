"""Генерує models/class_table.csv, models/property_dictionary.csv, models/onto.owl (Turtle) з scripts/onto_model.py."""
import csv
import sys
from pathlib import Path

from rdflib import BNode, Graph, Literal, Namespace, URIRef
from rdflib.collection import Collection
from rdflib.namespace import DCTERMS, OWL, RDF, RDFS, SKOS, XSD

sys.path.insert(0, str(Path(__file__).resolve().parent))
from onto_model import BASE, C, DEFINED, P, SIB_DISJOINT, TOP_DISJOINT   # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
D = Namespace(BASE)
EX5 = Namespace("http://example.org/knowledge-hub/biomed/")
MESH = "http://id.nlm.nih.gov/mesh/"
g = Graph()
for k, v in (("dkh", D), ("owl", OWL), ("rdfs", RDFS), ("skos", SKOS), ("dct", DCTERMS), ("xsd", XSD), ("ex5", EX5)):
    g.bind(k, v)
ONTO = URIRef(BASE.rstrip("#"))
g.add((ONTO, RDF.type, OWL.Ontology))
g.add((ONTO, DCTERMS.title, Literal("Domain Knowledge Hub: онтологія контролю якості геномних варіантів і каскадного тестування", lang="uk")))
g.add((ONTO, OWL.versionInfo, Literal("0.1.0")))
g.add((ONTO, OWL.versionIRI, URIRef(BASE.rstrip("#") + "/0.1.0")))
g.add((ONTO, DCTERMS.creator, Literal("Студент (власник моделі); чернетки — Claude (LLM), перевірка — студент")))
g.add((ONTO, DCTERMS.source, Literal("GATK Team, Hard-filtering germline short variants; CDC, About Cascade Testing; таксономія ЛР5; карта ЛР6 v2")))
g.add((ONTO, DCTERMS.description, Literal("Навчальна онтологія; статус довіри: чернетка, не перевірена експертом-медиком; не для клінічного використання.", lang="uk")))
g.add((ONTO, SKOS.note, Literal("Повторне використання: skos:closeMatch до таксономії ЛР5 (ex5:), skos:exactMatch/closeMatch до MeSH (URI перевірено MeSH Lookup API у ЛР5).")))

# --- класи
tax = {r["label"].lower(): r["id"] for r in csv.DictReader(open(ROOT / "models/taxonomy_final.csv", encoding="utf-8-sig"))}
mesh = {r["concept_label"].lower(): r for r in csv.DictReader(open(ROOT / "data/external_links.csv", encoding="utf-8-sig"))}
cid = {c[0] for c in C}
rows = []
for (i, en, uk, parent, genus, diff, l5, src, kp) in C:
    u = D[i]
    g.add((u, RDF.type, OWL.Class)); g.add((u, RDFS.label, Literal(en, lang="en"))); g.add((u, RDFS.label, Literal(uk, lang="uk")))
    d = f"{uk[0].upper() + uk[1:]} — це {genus}, {diff}." if parent or genus != "сутність" else f"{uk[0].upper() + uk[1:]} — це {genus}, {diff}."
    g.add((u, SKOS.definition, Literal(d, lang="uk")))
    if parent:
        g.add((u, RDFS.subClassOf, D[parent]))
    ext = ""
    key = l5.lower() if l5 else en.lower()
    if key in tax:
        g.add((u, SKOS.closeMatch, EX5[tax[key]])); ext = "ex5:" + tax[key]
    if key in mesh:
        m = mesh[key]; g.add((u, SKOS.exactMatch if m["match_type"] == "exactMatch" else SKOS.closeMatch, URIRef(m["external_uri"]))); ext += " " + m["external_uri"].replace("http://id.nlm.nih.gov/mesh/", "MeSH:")
    rows.append({"id": i, "label_en": en, "label_uk": uk, "definition": d, "genus": genus, "differentia": diff, "parent": parent or "owl:Thing",
                 "class_kind": "defined (≡)" if i in DEFINED else "primitive (⊑)", "key_properties": kp, "reuse_mapping": ext.strip(), "source": src})
with open(ROOT / "models/class_table.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, list(rows[0])); w.writeheader(); w.writerows(rows)

# --- допоміжні конструктори
def union(names):
    b = BNode(); Collection(g, b2 := BNode(), [D[n] for n in names]); g.add((b, RDF.type, OWL.Class)); g.add((b, OWL.unionOf, b2)); return b
def cls(x): return x if isinstance(x, (BNode, URIRef)) else D[x]
def some(p, c):
    r = BNode(); g.add((r, RDF.type, OWL.Restriction)); g.add((r, OWL.onProperty, D[p])); g.add((r, OWL.someValuesFrom, cls(c))); return r
def only(p, c):
    r = BNode(); g.add((r, RDF.type, OWL.Restriction)); g.add((r, OWL.onProperty, D[p])); g.add((r, OWL.allValuesFrom, cls(c))); return r
def card(p, n, kind, c=None):
    r = BNode(); g.add((r, RDF.type, OWL.Restriction)); g.add((r, OWL.onProperty, D[p]))
    g.add((r, {"min": OWL.minQualifiedCardinality, "max": OWL.maxQualifiedCardinality, "exact": OWL.qualifiedCardinality}[kind], Literal(n, datatype=XSD.nonNegativeInteger))); g.add((r, OWL.onClass, D[c])); return r
def hasval(p, lit):
    r = BNode(); g.add((r, RDF.type, OWL.Restriction)); g.add((r, OWL.onProperty, D[p])); g.add((r, OWL.hasValue, lit)); return r
def nominal(p, ind):
    b = BNode(); Collection(g, l := BNode(), [D[ind]]); g.add((b, RDF.type, OWL.Class)); g.add((b, OWL.oneOf, l)); return some(p, b)
def inter(parts):
    b = BNode(); Collection(g, l := BNode(), parts); g.add((b, RDF.type, OWL.Class)); g.add((b, OWL.intersectionOf, l)); return b
def numrange(base, op, val):
    b = BNode(); g.add((b, RDF.type, RDFS.Datatype)); g.add((b, OWL.onDatatype, base))
    facet = {"<": XSD.maxExclusive, ">": XSD.minExclusive, ">=": XSD.minInclusive}[op]
    fl = BNode(); g.add((fl, facet, Literal(val, datatype=base))); Collection(g, l := BNode(), [fl]); g.add((b, OWL.withRestrictions, l)); return b
def sub(c, expr): g.add((D[c], RDFS.subClassOf, expr))
def equiv(c, expr): g.add((D[c], OWL.equivalentClass, expr))
def dec(x): return Literal(x, datatype=XSD.decimal)

# --- властивості
for (i, en, uk, kind, dom, rng, chars, subof, inv, defn) in P:
    u = D[i]
    g.add((u, RDF.type, OWL.ObjectProperty if kind == "object" else OWL.DatatypeProperty))
    g.add((u, RDFS.label, Literal(en, lang="en"))); g.add((u, RDFS.label, Literal(uk, lang="uk"))); g.add((u, SKOS.definition, Literal(defn, lang="uk")))
    for ch in filter(None, chars.split("|")):
        g.add((u, RDF.type, {"transitive": OWL.TransitiveProperty, "symmetric": OWL.SymmetricProperty, "functional": OWL.FunctionalProperty}[ch]))
    for s in filter(None, subof.split("|")): g.add((u, RDFS.subPropertyOf, D[s]))
    if inv and kind == "object" and (i < inv or True) and (u, OWL.inverseOf, None) not in g:
        if (D[inv], OWL.inverseOf, u) not in g: g.add((u, OWL.inverseOf, D[inv]))
    g.add((u, RDFS.domain, union(dom.split("|")) if "|" in dom else D[dom]))
    if kind == "object":
        g.add((u, RDFS.range, union(rng.split("|")) if "|" in rng else D[rng]))
    else:
        g.add((u, RDFS.range, XSD[rng]))
def chain(p, a, b):
    l = BNode(); Collection(g, l, [D[a], D[b]]); g.add((D[p], OWL.propertyChainAxiom, l))
chain("hasGrandparent", "hasParent", "hasParent"); chain("hasAuntOrUncle", "hasParent", "hasSibling"); chain("hasCousin", "hasAuntOrUncle", "hasChild")
with open(ROOT / "models/property_dictionary.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f); w.writerow(["id", "label", "type", "domain", "range", "characteristics", "subPropertyOf", "inverseOf", "definition"])
    for (i, en, uk, kind, dom, rng, chars, subof, inv, defn) in P:
        w.writerow([i, en, kind, dom.replace("|", " ⊔ "), (rng if kind == "data" else rng.replace("|", " ⊔ ")), chars.replace("|", ", ") or "—", subof.replace("|", ", ") or "—", inv or "—", defn])

# --- диз'юнктності
def all_disjoint(names):
    b = BNode(); Collection(g, l := BNode(), [D[n] for n in names]); g.add((b, RDF.type, OWL.AllDisjointClasses)); g.add((b, OWL.members, l))
all_disjoint(TOP_DISJOINT)
for grp in SIB_DISJOINT: all_disjoint(grp)

# --- контрольований словник клінічних значень
for n, en in (("Pathogenic", "pathogenic"), ("Benign", "benign")):
    g.add((D[n], RDF.type, OWL.NamedIndividual)); g.add((D[n], RDF.type, D.ClinicalSignificance)); g.add((D[n], RDFS.label, Literal(en, lang="en")))

# --- означені класи
equiv("PathogenicVariant", inter([D.GeneticVariant, nominal("hasClinicalSignificance", "Pathogenic")]))
equiv("ExonEndVariant", inter([D.GeneticVariant, hasval("hasExonEndPosition", Literal(True))]))
def ann_cond(ann, op, val, base=XSD.decimal):
    r = BNode(); g.add((r, RDF.type, OWL.Restriction)); g.add((r, OWL.onProperty, D.hasNumericValue)); g.add((r, OWL.someValuesFrom, numrange(base, op, val)))
    return some("hasAnnotation", inter([D[ann], r]))
equiv("LowQDAnnotation", inter([D.QualityByDepth, (lambda r: (g.add((r, RDF.type, OWL.Restriction)), g.add((r, OWL.onProperty, D.hasNumericValue)), g.add((r, OWL.someValuesFrom, numrange(XSD.decimal, "<", "2.0"))), r)[-1])(BNode())]))
equiv("LowQDVariant", inter([D.GeneticVariant, some("hasAnnotation", D.LowQDAnnotation)]))
equiv("HighFSSnpVariant", inter([D.SNP, ann_cond("FisherStrandBias", ">", "60.0")]))
equiv("HighFSIndelVariant", inter([D.Indel, ann_cond("FisherStrandBias", ">", "200.0")]))
fl = [D.LowQDVariant, D.HighFSSnpVariant, D.HighFSIndelVariant, inter([D.GeneticVariant, ann_cond("StrandOddsRatio", ">", "3.0")]),
      inter([D.GeneticVariant, ann_cond("MappingQuality", "<", "40.0")]), inter([D.GeneticVariant, ann_cond("MQRankSum", "<", "-12.5")]), inter([D.GeneticVariant, ann_cond("ReadPosRankSum", "<", "-8.0")])]
b = BNode(); Collection(g, l := BNode(), fl); g.add((b, RDF.type, OWL.Class)); g.add((b, OWL.unionOf, l)); equiv("FlaggedVariant", b)
for cl, prop, pr in (("FirstDegreeRelative", "isFirstDegreeRelativeOf", "0.5"), ("SecondDegreeRelative", "isSecondDegreeRelativeOf", "0.25"), ("ThirdDegreeRelative", "isThirdDegreeRelativeOf", "0.125")):
    equiv(cl, inter([D.Person, some(prop, D.Proband)])); sub(cl, hasval("hasInheritanceProbability", dec(pr)))
for cl, op, v in (("AdultRelative", ">=", "18"), ("MinorRelative", "<", "18")):
    r = BNode(); g.add((r, RDF.type, OWL.Restriction)); g.add((r, OWL.onProperty, D.hasAgeYears)); g.add((r, OWL.someValuesFrom, numrange(XSD.integer, op, v)))
    equiv(cl, inter([D.Relative, r]))

# --- аксіоми існування / універсальності / кардинальності
AX = []
def ax(c, expr, text): sub(c, expr); AX.append((c, text))
for a in ("QualityByDepth", "FisherStrandBias", "StrandOddsRatio", "MappingQuality", "RankSumAnnotation"):
    ax("HardFiltering", some("usesInput", a), f"∃ usesInput.{a}")
ax("VQSR", some("requires", "LargeVariantSet"), "∃ requires.LargeVariantSet"); ax("VQSR", some("requires", "CuratedKnownVariants"), "∃ requires.CuratedKnownVariants")
ax("CascadeTesting", some("requires", "PathogenicVariant"), "∃ requires.PathogenicVariant"); ax("CascadeTesting", only("appliesTo", "Relative"), "∀ appliesTo.Relative")
ax("CascadeTesting", some("recommendedFor", "FirstDegreeRelative"), "∃ recommendedFor.FirstDegreeRelative")
ax("GenePanel", some("hasMember", "Gene"), "∃ hasMember.Gene"); ax("GenePanel", only("hasMember", "Gene"), "∀ hasMember.Gene")
ax("PathogenicVariant", some("increasesRiskOf", "BreastCancer"), "∃ increasesRiskOf.BreastCancer"); ax("PathogenicVariant", some("increasesRiskOf", "OvarianCancer"), "∃ increasesRiskOf.OvarianCancer")
ax("HardFiltering", some("recommendedFor", "GenePanel"), "∃ recommendedFor.GenePanel"); ax("StrandOddsRatio", some("recommendedFor", "ExonEndVariant"), "∃ recommendedFor.ExonEndVariant")
ax("VCFFile", some("derivedFrom", "BAMFile"), "∃ derivedFrom.BAMFile"); ax("BAMFile", some("generatedBy", "Sequencer"), "∃ generatedBy.Sequencer"); ax("Exon", some("partOf", "Gene"), "∃ partOf.Gene")
ax("GenePanel", card("hasMember", 2, "min", "Gene"), "hasMember ≥ 2 Gene"); ax("CascadeTesting", card("hasProband", 1, "exact", "Proband"), "hasProband = 1 Proband"); ax("CascadeTesting", hasval("hasMinTestingAge", Literal(18)), "hasMinTestingAge = 18"); ax("Person", card("hasParent", 2, "max", "Person"), "hasParent ≤ 2 Person")
ax("GeneticVariant", card("hasClinicalSignificance", 1, "max", "ClinicalSignificance"), "hasClinicalSignificance ≤ 1 ClinicalSignificance")
(ROOT / "docs/evidence").mkdir(parents=True, exist_ok=True)
(ROOT / "docs/evidence/axioms.txt").write_text("Аксіоми існування/універсальності/кардинальності (SubClassOf):\n" + "\n".join(f"  {c} ⊑ {t}" for c, t in AX) + "\n", encoding="utf-8")
g.add((D.guardClass, RDF.type, OWL.AnnotationProperty)); g.add((D.guardClass, RDFS.label, Literal("guard class", lang="en")))
g.serialize(ROOT / "models/onto.owl", format="turtle")
print(len(C), "класів;", sum(p[3] == "object" for p in P), "object;", sum(p[3] == "data" for p in P), "data; аксіом:", len(AX), "; тріплів:", len(g))
