"""Порівняння моєї онтології з чернеткою LLM: класи, властивості, автоматичні перевірки дефектів, CQ → docs/evidence/onto_compare.json."""
import csv
import json
import re
import sys
from pathlib import Path

from rdflib import BNode, Graph, Literal, URIRef
from rdflib.namespace import OWL, RDF, RDFS

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from reasoning import infer   # noqa: E402
from run_cq import load       # noqa: E402


def labels(g, kind):
    out = {}
    for c in g.subjects(RDF.type, kind):
        if isinstance(c, BNode): continue
        for l in g.objects(c, RDFS.label):
            if isinstance(l, Literal) and l.language == "en":
                out[re.sub(r"[_\s]+", " ", str(l).lower()).strip()] = c
    return out


def new_types(g, inf, inds):
    """Нові (відсутні у вхідних даних) прямі типи індивідів: типи, що є надкласами інших типів, відкидаються."""
    sub = Graph()
    for t in list(g.triples((None, RDFS.subClassOf, None))) + list(inf.triples((None, RDFS.subClassOf, None))): sub.add(t)
    out = 0
    for a in inds:
        ts = set(inf.objects(a, RDF.type))
        ts = {t for t in ts if not any(t in set(sub.transitive_objects(u, RDFS.subClassOf)) - {u} for u in ts if u != t)}
        out += sum(1 for t in ts if (a, RDF.type, t) not in g)
    return out


def main():
    mine, llm = load("mine"), load("llm")
    R = {}
    # --- класи
    cm, cl = labels(mine, OWL.Class), labels(llm, OWL.Class)
    all_cls_llm = {c for c in llm.subjects(RDF.type, OWL.Class) if not isinstance(c, BNode)}
    all_cls_mine = {c for c in mine.subjects(RDF.type, OWL.Class) if not isinstance(c, BNode)}
    ALIAS = {"quality measure": "measure of quality", "data artifact": "data and artifact", "procedure": "method and procedure", "filter threshold": "threshold", "quality annotation": "variant call annotation"}
    exact = sorted(set(cm) & set(cl)); alias = sorted(k for k, v in ALIAS.items() if k in cm and v in cl and k not in cl)
    match = exact + alias
    only_m = sorted(set(cm) - set(cl) - set(alias)); only_l = sorted(set(cl) - set(cm) - {ALIAS[k] for k in alias})
    R["classes"] = {"mine": len(all_cls_mine), "llm": len(all_cls_llm), "matched_by_label": len(match), "matched_exact": len(exact), "matched_alias": alias, "mine_only": len(only_m), "llm_only": len(only_l),
                    "mine_only_list": only_m, "llm_only_sample": only_l[:30], "llm_label_missing": len(all_cls_llm) - len(cl) if False else sum(1 for c in all_cls_llm if not list(llm.objects(c, RDFS.label)))}
    # --- властивості
    def props(g):
        o = {re.sub(r"[_\s]+", " ", str(l).lower()): p for p in g.subjects(RDF.type, OWL.ObjectProperty) for l in g.objects(p, RDFS.label) if getattr(l, "language", None) == "en"}
        d = {re.sub(r"[_\s]+", " ", str(l).lower()): p for p in g.subjects(RDF.type, OWL.DatatypeProperty) for l in g.objects(p, RDFS.label) if getattr(l, "language", None) == "en"}
        return o, d
    (mo, md), (lo, ld) = props(mine), props(llm)
    R["properties"] = {"mine_object": len(mo), "mine_data": len(md), "llm_object": len(lo), "llm_data": len(ld), "object_matched": len(set(mo) & set(lo)), "data_matched": len(set(md) & set(ld)),
                       "object_mine_only": sorted(set(mo) - set(lo)), "object_llm_only": sorted(set(lo) - set(mo))}
    # --- дефекти чернетки (автоматично)
    d = {}
    d["E_label_is_IRI"] = sorted(str(s).split("#")[-1] for s, o in llm.subject_objects(RDFS.label) if isinstance(o, URIRef))
    declared = {"transitive": len(list(llm.subjects(RDF.type, OWL.TransitiveProperty))), "symmetric": len(list(llm.subjects(RDF.type, OWL.SymmetricProperty))), "functional": len(list(llm.subjects(RDF.type, OWL.FunctionalProperty)))}
    d["characteristics_actually_declared"] = declared
    allp = list(llm.subjects(RDF.type, OWL.ObjectProperty))
    d["object_props_total"] = len(allp)
    d["object_props_without_domain_or_range"] = sum(1 for p in allp if not list(llm.objects(p, RDFS.domain)) or not list(llm.objects(p, RDFS.range)))
    d["object_props_without_domain_and_range_both"] = sum(1 for p in allp if not list(llm.objects(p, RDFS.domain)) and not list(llm.objects(p, RDFS.range)))
    ok_l, inf_l, cls_out_l = infer(llm)
    d["hermit_consistent"] = ok_l
    d["unsatisfiable_classes"] = sum(1 for l in cls_out_l.splitlines() if "owl:Nothing" in l or "Nothing>" in l)
    ind_l = {s for s in llm.subjects(RDF.type, OWL.NamedIndividual)}
    d["draft_new_inferred_types_on_individuals"] = new_types(llm, inf_l, ind_l)
    cls_names = {str(c).split("#")[-1] for c in all_cls_llm}
    d["classes_with_single_individual_that_are_individuals_in_reality"] = [n for n in ("BRCA1", "BRCA2") if n in cls_names]
    d["asserted_filter_status_instead_of_inferred"] = len(list(llm.subject_objects(URIRef("http://example.org/onto/brca-gatk#has_filter_status"))))
    d["degree_class_asserted_not_inferred"] = sum(1 for s in ind_l for t in llm.objects(s, RDF.type) if str(t).split("#")[-1] in ("first_degree_relative", "second_degree_relative", "third_degree_relative"))
    d["ontology_metadata_triples"] = len([1 for _ in llm.predicate_objects(URIRef("http://example.org/onto/brca-gatk"))])
    d["skos_definition_used"] = len(list(llm.subjects(URIRef("http://www.w3.org/2004/02/skos/core#definition"), None)))
    R["draft_defects"] = d
    ok_m, inf_m, _ = infer(mine)
    ind_m = {s for s in mine.subjects(RDF.type, OWL.NamedIndividual)}
    R["mine"] = {"consistent": ok_m, "new_inferred_types_on_individuals": new_types(mine, inf_m, ind_m)}
    # --- CQ
    cq = {n: list(csv.DictReader(open(ROOT / f"docs/evidence/cq_results_{n}.csv", encoding="utf-8-sig"))) for n in ("mine", "llm")}
    R["cq"] = {n: {"passed": sum(int(r["passed"]) for r in rows), "total": len(rows)} for n, rows in cq.items()}
    (ROOT / "docs/evidence/onto_compare.json").write_text(json.dumps(R, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({k: v for k, v in R.items() if k != "cq"}, ensure_ascii=False, indent=1)[:3500]); print(R["cq"])


if __name__ == "__main__":
    main()
