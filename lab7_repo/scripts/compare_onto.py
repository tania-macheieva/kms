"""Порівняння моєї онтології з чернеткою LLM: класи (збіг/пропуски/зайві), властивості, аксіоми, перевірки HermiT → docs/evidence/onto_compare.json/.txt"""
import csv
import json
import re
import sys
from pathlib import Path

from rdflib import BNode, Graph, URIRef
from rdflib.namespace import OWL, RDF, RDFS, XSD

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from reasoning import run_hermit   # noqa: E402
from run_cq import load            # noqa: E402


def key(s): return re.sub(r"[^a-z0-9]", "", s.lower())


def stats(g):
    en = lambda x: next((str(l) for l in g.objects(x, RDFS.label) if getattr(l, "language", None) == "en"), None)
    classes = {en(c): c for c in g.subjects(RDF.type, OWL.Class) if isinstance(c, URIRef) and en(c)}
    nolabel = [c for c in g.subjects(RDF.type, OWL.Class) if isinstance(c, URIRef) and not en(c)]
    objp = [p for p in g.subjects(RDF.type, OWL.ObjectProperty)]
    datp = [p for p in g.subjects(RDF.type, OWL.DatatypeProperty)]
    R = list(g.subjects(RDF.type, OWL.Restriction))
    cnt = lambda pred: sum(1 for r in R if (r, pred, None) in g)
    props = {en(p): p for p in objp + datp if en(p)}
    ch = lambda t: sum(1 for p in objp if (p, RDF.type, t) in g)
    inds = [i for i in g.subjects(RDF.type, OWL.NamedIndividual) if not re.search(r"#(S0\d_|Situation_|Pathogenic$|Benign$)", str(i))]
    prop_preds = lambda i: sum(1 for p, o in g.predicate_objects(i) if p not in (RDF.type, RDFS.label))
    return {
        "classes": len(classes), "classes_without_en_label": len(nolabel), "object_properties": len(objp), "data_properties": len(datp),
        "object_props_with_domain": sum(1 for p in objp if (p, RDFS.domain, None) in g), "object_props_with_range": sum(1 for p in objp if (p, RDFS.range, None) in g),
        "data_props_with_range": sum(1 for p in datp if (p, RDFS.range, None) in g),
        "someValuesFrom": cnt(OWL.someValuesFrom), "allValuesFrom": cnt(OWL.allValuesFrom), "hasValue": cnt(OWL.hasValue),
        "cardinality": sum(cnt(x) for x in (OWL.minCardinality, OWL.maxCardinality, OWL.cardinality, OWL.minQualifiedCardinality, OWL.maxQualifiedCardinality, OWL.qualifiedCardinality)),
        "disjoint_axioms": len(list(g.subjects(RDF.type, OWL.AllDisjointClasses))) + len(list(g.subject_objects(OWL.disjointWith))),
        "equivalent_class_axioms": len(list(g.subject_objects(OWL.equivalentClass))),
        "transitive": ch(OWL.TransitiveProperty), "symmetric": ch(OWL.SymmetricProperty), "functional": ch(OWL.FunctionalProperty), "inverse": len(list(g.subject_objects(OWL.inverseOf))), "property_chains": len(list(g.subject_objects(OWL.propertyChainAxiom))),
        "individuals": len(inds), "avg_props_per_individual": round(sum(prop_preds(i) for i in inds) / max(1, len(inds)), 2),
    }, classes, props


def main():
    mine, llm = load("mine"), load("llm")
    sm, cm, pm = stats(mine); sl, cl, pl = stats(llm)
    km, kl = {key(k): k for k in cm}, {key(k): k for k in cl}
    matched = sorted(km[k] for k in km if k in kl); mine_only = sorted(km[k] for k in km if k not in kl); llm_only = sorted(kl[k] for k in kl if k not in km)
    tax = {key(r["label"]) for r in csv.DictReader(open(ROOT / "models/taxonomy_final.csv", encoding="utf-8-sig"))}
    llm_only_tax = [x for x in llm_only if key(x) in tax]; llm_only_new = [x for x in llm_only if key(x) not in tax]
    pkm, pkl = {key(k): k for k in pm}, {key(k): k for k in pl}
    pmatched = sorted(pkm[k] for k in pkm if k in pkl); pmine_only = sorted(pkm[k] for k in pkm if k not in pkl); plm_only = sorted(pkl[k] for k in pkl if k not in pkm)
    rc, out = run_hermit(llm.__class__() + llm, ["-c"])
    unsat = [l for l in out.splitlines() if "owl:Nothing" in l or "Nothing>" in l]
    res = {"mine": sm, "llm": sl, "classes_matched": len(matched), "classes_mine_only": mine_only, "classes_llm_only_total": len(llm_only), "classes_llm_only_from_lab5_taxonomy": len(llm_only_tax), "classes_llm_only_new": llm_only_new,
           "properties_matched": pmatched, "properties_mine_only": pmine_only, "properties_llm_only": plm_only, "llm_hermit_consistent": rc == 0, "llm_unsatisfiable": len(unsat)}
    (ROOT / "docs/evidence/onto_compare.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    L = [f"Класи: моя {sm['classes']}, чернетка LLM {sl['classes']}; збіг за назвою {len(matched)}; лише в моїй {len(mine_only)}; лише в LLM {len(llm_only)} (з них із таксономії ЛР5: {len(llm_only_tax)}, нових: {len(llm_only_new)})",
         "Лише в моїй: " + "; ".join(mine_only), "Нові в LLM: " + "; ".join(llm_only_new),
         f"Властивості: збіг {len(pmatched)}; лише в моїй {len(pmine_only)}: {pmine_only}; лише в LLM {len(plm_only)}", f"HermiT чернетки: узгоджена={rc == 0}, необґрунтованих класів={len(unsat)}", "", json.dumps({"mine": sm, "llm": sl}, ensure_ascii=False, indent=1)]
    (ROOT / "docs/evidence/onto_compare.txt").write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L[:6]))


if __name__ == "__main__":
    main()
