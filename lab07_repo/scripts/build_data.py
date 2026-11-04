"""Генерує models/onto_data.ttl (індивіди + екземпляри ситуацій), models/situations.csv, models/model_meta.csv."""
import csv
import sys
from pathlib import Path

from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import DCTERMS, OWL, RDF, RDFS, XSD

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts")); sys.path.insert(0, str(ROOT / "data"))
from onto_model import BASE   # noqa: E402
from situations_src import S   # noqa: E402

D = Namespace(BASE)
g = Graph(); g.bind("dkh", D); g.bind("owl", OWL); g.bind("rdfs", RDFS); g.bind("xsd", XSD); g.bind("dct", DCTERMS)
ONTO = URIRef(BASE.rstrip("#") + "/data")
g.add((ONTO, RDF.type, OWL.Ontology)); g.add((ONTO, OWL.imports, URIRef(BASE.rstrip("#"))))
g.add((ONTO, DCTERMS.description, Literal("Синтетичні індивіди (вигадані особи й варіанти) для перевірки онтології; персональних даних немає.", lang="uk")))
def dec(x): return Literal(x, datatype=XSD.decimal)
def ind(name, types, label, **props):
    u = D[name]; g.add((u, RDF.type, OWL.NamedIndividual))
    for t in ([types] if isinstance(types, str) else types): g.add((u, RDF.type, D[t]))
    g.add((u, RDFS.label, Literal(label, lang="en")))
    for k, vals in props.items():
        for v in (vals if isinstance(vals, list) else [vals]):
            g.add((u, D[k], v if isinstance(v, Literal) else D[v]))
    return u
I = lambda n: Literal(n, datatype=XSD.integer)
# --- родина
ind("Olena", "Proband", "Olena", hasAgeYears=I(42), hasDiagnosis="Olena_BC", carries="VAR-001", hasParent=["Iryna", "Petro"], hasSibling="Marta")
ind("Olena_BC", "BreastCancer", "breast cancer (Olena)")
ind("Marta", [], "Marta", hasAgeYears=I(39), hasParent=["Iryna", "Petro"], hasSibling="Olena")
ind("Iryna", [], "Iryna", hasAgeYears=I(68), hasDiagnosis="Iryna_OC", hasParent="Maria", hasSibling="Halyna")
ind("Iryna_OC", "OvarianCancer", "ovarian cancer (Iryna)")
ind("Petro", [], "Petro", hasAgeYears=I(70))
ind("Sofiia", [], "Sofiia", hasAgeYears=I(17), hasParent="Olena")
ind("Halyna", [], "Halyna", hasAgeYears=I(65), hasParent="Maria", hasChild="Andrii")
ind("Andrii", [], "Andrii", hasAgeYears=I(40))
ind("Maria", [], "Maria", hasChild=["Iryna", "Halyna"])
for p in ("Marta", "Iryna", "Petro", "Sofiia", "Halyna", "Andrii", "Maria"): g.add((D[p], RDF.type, D.Person))
g.add((D.Maria, D.isDeceased, Literal(True)))  # Maria померла; вік не вказано
# --- гени, панель, файли
CHR = {"BRCA1": "17", "BRCA2": "13", "PALB2": "16", "TP53": "17"}
for gname in ("BRCA1", "BRCA2", "PALB2", "TP53"): ind(gname, "Gene", gname, isMemberOf="HBOC-panel", hasGeneSymbol=Literal(gname), onChromosome=Literal(CHR[gname]))
ind("HBOC-panel", "GenePanel", "HBOC-panel", hasMember=["BRCA1", "BRCA2", "PALB2", "TP53"])
ind("Sequencer1", "Sequencer", "Sequencer1")
ind("sample1_bam", "BAMFile", "sample1.bam", generatedBy="Sequencer1")
ind("sample1_vcf", "VCFFile", "sample1.vcf", derivedFrom="sample1_bam", generatedBy="Sequencer1")
# --- варіанти й анотації
ANN = {"QualityByDepth": "QD", "FisherStrandBias": "FS", "StrandOddsRatio": "SOR", "MappingQuality": "MQ"}
def var(name, vid, types, gene, ann, **extra):
    ind(name, types, name, hasVariantId=Literal(vid), locatedIn=gene, **extra)
    for i, (cls, val) in enumerate(ann):
        a = f"{name}_{cls}"; ind(a, cls, f"{cls} of {name}", hasNumericValue=dec(val), isAnnotationOf=name, hasAnnotationName=Literal(ANN[cls])); g.add((D[name], D.hasAnnotation, D[a]))
var("VAR-001", "VAR-001", ["SNP", "GermlineVariant"], "BRCA1", [("QualityByDepth", "25.0"), ("FisherStrandBias", "3.1"), ("StrandOddsRatio", "0.8"), ("MappingQuality", "60.0")], hasClinicalSignificance="Pathogenic")
var("VAR-002", "VAR-002", "SNP", "BRCA2", [("QualityByDepth", "1.5")], hasClinicalSignificance="Benign")
var("VAR-003", "VAR-003", "Indel", "BRCA2", [("FisherStrandBias", "150.0")])
var("VAR-004", "VAR-004", "SNP", "BRCA2", [("FisherStrandBias", "62.0"), ("StrandOddsRatio", "2.1")], hasExonEndPosition=Literal(True))
# --- пороги й фільтрація
TH = [("QD_lt_2", "QD", "<", "2.0", "all"), ("FS_gt_60_snp", "FS", ">", "60.0", "SNP"), ("FS_gt_200_indel", "FS", ">", "200.0", "INDEL"), ("SOR_gt_3", "SOR", ">", "3.0", "all"),
      ("MQ_lt_40", "MQ", "<", "40.0", "all"), ("MQRankSum_lt_-12.5", "MQRankSum", "<", "-12.5", "all"), ("ReadPosRankSum_lt_-8", "ReadPosRankSum", "<", "-8.0", "all")]
for n, a, op, v, t in TH:
    ind(n, "FilterThreshold", f"{a} {op} {v} ({t})", hasThresholdValue=dec(v), hasComparisonOperator=Literal(op), onAnnotationName=Literal(a), forVariantType=Literal(t))
ind("HF-01", "HardFiltering", "HF-01", appliesTo="sample1_vcf", hasThreshold=[t[0] for t in TH])
ind("CT-01", "CascadeTesting", "CT-01", requires="VAR-001", hasProband="Olena", hasMinTestingAge=I(18), appliesTo=["Marta", "Sofiia", "Halyna", "Andrii"])
# --- екземпляри ситуацій
rows, tpl = [], {}
for (sid, name, st0, ev, guard, gcls, st1, act, cons, sensor, src) in S:
    t = f"Situation_{sid}"
    ind(t, "SituationTemplate", f"{sid} {name}", hasGuard=Literal(guard))
    for prop, cl, key in (("hasInitialState", st0, "i"), ("triggeredBy", ev, "e"), ("hasNewState", st1, "n"), ("hasAction", act, "a")):
        iname = f"{sid}_{key}_{cl}"; ind(iname, cl, f"{sid}: {cl}"); g.add((D[t], D[prop], D[iname]))
    g.add((D[t], D.guardClass, D[gcls]))
    rows.append({"id": sid, "name": name, "initial_state": st0, "event": ev, "guard": guard, "new_state": st1, "action": act, "consequence": cons,
                 "initial_state_class": "dkh:" + st0, "event_class": "dkh:" + ev, "guard_class": "dkh:" + gcls, "new_state_class": "dkh:" + st1, "action_class": "dkh:" + act,
                 "sensor_or_source_class": ("dkh:" + sensor) if sensor != "—" else "—", "source": src})
g.serialize(ROOT / "models/onto_data.ttl", format="turtle")
with open(ROOT / "models/situations.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, list(rows[0])); w.writeheader(); w.writerows(rows)
META = [("model_name", "Domain Knowledge Hub — онтологія QC варіантів і каскадного тестування"), ("version", "0.1.0"), ("owner", "студент (власник моделі); контакт — у заголовку звіту"),
        ("created", "2026-10-25"), ("status_of_trust", "чернетка; перевірено автоматично (HermiT, CQ-тести); експертом-медиком не перевірено; не для клінічного використання"),
        ("sources", "GATK Team: Hard-filtering germline short variants; CDC: About Cascade Testing; ЛР4 (CQ), ЛР5 (таксономія), ЛР6 (карта v2)"),
        ("reused_vocabularies", "SKOS (мітки/зіставлення), MeSH (URI перевірено у ЛР5), таксономія ЛР5 (skos:closeMatch)"),
        ("llm_involvement", "Claude (claude-sonnet-5-5): чернетки класів, аксіом і ситуацій; журнал — llm_log/; твердження — claims/claims.csv"), ("namespace_note", "http://example.org/dkh/onto# — заглушка")]
with open(ROOT / "models/model_meta.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f); w.writerow(["field", "value"]); w.writerows(META)
inds = {s for s in g.subjects(RDF.type, OWL.NamedIndividual)}
cnt = {s: sum(1 for p, o in g.predicate_objects(s) if p not in (RDF.type, RDFS.label)) for s in inds}
print(len(inds), "індивідів; середня кількість властивостей:", round(sum(cnt.values()) / len(inds), 2))
