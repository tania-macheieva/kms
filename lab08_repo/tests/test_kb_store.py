import json
from pathlib import Path

from rdflib import Graph

from store import GRAPHS, open_store, query

ROOT = Path(__file__).resolve().parents[1]


def test_kb_valid_and_big():
    g = Graph().parse(ROOT / "data/kb.ttl", format="turtle")
    assert len(g) >= 300


def test_store_counts_match_files():
    st = open_store(); meta = json.loads((ROOT / "data/load_meta.json").read_text(encoding="utf-8"))
    r = list(query(st, "SELECT (COUNT(*) AS ?n) WHERE { ?s ?p ?o }"))[0]["n"].value
    assert int(r) > 0
    assert set(meta["graphs"]) >= set(GRAPHS) and sum(meta["graphs"].values()) == meta["total_quads"] == int(r)


def test_jsonld_entities():
    d = json.loads((ROOT / "data/kb.jsonld").read_text(encoding="utf-8"))
    assert len(d["@graph"]) >= 20
