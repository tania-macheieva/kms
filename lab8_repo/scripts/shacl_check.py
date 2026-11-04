"""SHACL-валідація (pySHACL): валідний набір (data/kb.ttl) і дефектний набір з 3 навмисними вадами.
Зберігає shapes/report_valid.ttl, shapes/report_defective.ttl, data/kb_defective.ttl, shapes/shacl_summary.json
і виконує демонстрацію «OWL vs SHACL»: HermiT щодо дефектного набору."""
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

import pyshacl
from rdflib import Graph, Literal, Namespace, RDF, URIRef
from rdflib.namespace import SH, XSD

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
D = Namespace("http://example.org/dkh/onto#")
SHAPES = Graph().parse(ROOT / "shapes/shapes.ttl")


def summarize(rg):
    rows = []
    for r in rg.subjects(RDF.type, SH.ValidationResult):
        rows.append({"severity": str(rg.value(r, SH.resultSeverity)).split("#")[-1], "focus": str(rg.value(r, SH.focusNode)).replace(str(D), "dkh:"),
                     "path": str(rg.value(r, SH.resultPath) or "").replace(str(D), "dkh:"), "component": str(rg.value(r, SH.sourceConstraintComponent)).split("#")[-1].replace("ConstraintComponent", ""),
                     "value": str(rg.value(r, SH.value) or "").replace(str(D), "dkh:"), "message": str(rg.value(r, SH.resultMessage) or "")})
    return sorted(rows, key=lambda x: (x["severity"], x["focus"], x["component"]))


def validate(data):
    # allow_warnings=True: «Warning» не робить набір невалідним, але потрапляє у звіт
    ok, rg, _ = pyshacl.validate(data, shacl_graph=SHAPES, inference="none", allow_warnings=True)
    return ok, rg


def make_defective():
    g = Graph().parse(ROOT / "data/kb.ttl", format="turtle")
    # Вада 1 (minCount): VAR-105 втрачає зв'язок із геном
    for o in list(g.objects(D["VAR-105"], D.locatedIn)): g.remove((D["VAR-105"], D.locatedIn, o))
    # Вада 2 (pattern): ідентифікатор VAR-106 порушує формат VAR-123
    g.remove((D["VAR-106"], D.hasVariantId, Literal("VAR-106"))); g.add((D["VAR-106"], D.hasVariantId, Literal("variant_106")))
    # Вада 3 (range): вік Marta — 391 рік
    for o in list(g.objects(D.Marta, D.hasAgeYears)): g.remove((D.Marta, D.hasAgeYears, o))
    g.add((D.Marta, D.hasAgeYears, Literal(391)))
    return g


def main():
    out = {}
    valid = Graph().parse(ROOT / "data/kb.ttl", format="turtle")
    ok, rg = validate(valid); rg.serialize(ROOT / "shapes/report_valid.ttl", format="turtle")
    out["valid"] = {"conforms": ok, "results": summarize(rg)}
    bad = make_defective(); bad.serialize(ROOT / "data/kb_defective.ttl", format="turtle")
    ok2, rg2 = validate(bad); rg2.serialize(ROOT / "shapes/report_defective.ttl", format="turtle")
    out["defective"] = {"conforms": ok2, "results": summarize(rg2)}
    # статистика форми
    shapes = list(SHAPES.subjects(RDF.type, SH.NodeShape)); props = list(SHAPES.subjects(SH.path, None))
    kinds = Counter()
    for p in props:
        for k in ("minCount", "maxCount", "datatype", "class", "minInclusive", "maxInclusive", "pattern", "in"):
            if (p, SH[k], None) in SHAPES: kinds[k] += 1
    out["stats"] = {"node_shapes": len(shapes), "property_shapes": len(props), "constraints_by_type": dict(kinds), "constraints_total": sum(kinds.values())}
    (ROOT / "shapes/shacl_summary.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({"valid_conforms": out["valid"]["conforms"], "valid_n": len(out["valid"]["results"]), "defective_conforms": ok2, "defective": [(r["severity"], r["focus"], r["component"]) for r in out["defective"]["results"]], "stats": out["stats"]}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
