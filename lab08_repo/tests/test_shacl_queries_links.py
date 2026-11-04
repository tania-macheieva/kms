import json
from pathlib import Path

from rdflib import Graph
from rdflib.namespace import SKOS

ROOT = Path(__file__).resolve().parents[1]


def test_shacl_valid_and_defective():
    s = json.loads((ROOT / "shapes/shacl_summary.json").read_text(encoding="utf-8"))
    assert s["valid"]["conforms"] is True
    v = [r for r in s["defective"]["results"] if r["severity"] == "Violation"]
    assert not s["defective"]["conforms"] and len(v) >= 3
    assert s["stats"]["node_shapes"] >= 5 and s["stats"]["constraints_total"] >= 8


def test_queries_kinds_and_manual_match():
    files = sorted((ROOT / "queries").glob("q*.rq")); text = "\n".join(f.read_text(encoding="utf-8") for f in files)
    assert len(files) >= 8
    for kw in ("SELECT", "ASK", "CONSTRUCT", "COUNT", "OPTIONAL", "FILTER", "SERVICE"): assert kw in text
    assert "hasParent+" in text or ")+" in text
    man = json.loads((ROOT / "queries/results/manual_verification.json").read_text(encoding="utf-8"))
    assert len(man) >= 3 and all(v["match"] for v in man.values())


def test_links():
    g = Graph().parse(ROOT / "data/links.ttl", format="turtle")
    n = sum(1 for _ in g.triples((None, SKOS.closeMatch, None))) + sum(1 for _ in g.triples((None, SKOS.relatedMatch, None))) + sum(1 for _ in g.triples((None, SKOS.exactMatch, None)))
    assert n >= 5
    import csv
    rows = list(csv.DictReader(open(ROOT / "data/links_decisions.csv", encoding="utf-8-sig")))
    assert any(r["decision"] == "rejected" for r in rows)
