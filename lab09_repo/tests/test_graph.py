import csv
import json
from pathlib import Path

import graphdb as gdb

ROOT = Path(__file__).resolve().parents[1]
J = lambda p: json.loads((ROOT / p).read_text(encoding="utf-8"))


def test_sizes_and_csv():
    n = sum(len(list(csv.DictReader(open(f, encoding="utf-8")))) for f in (ROOT / "data").glob("nodes_*.csv"))
    r = sum(len(list(csv.DictReader(open(f, encoding="utf-8")))) for f in (ROOT / "data").glob("rels_*.csv"))
    assert n >= 100 and r >= 200
    live = gdb.graph().ro_query("MATCH (n) RETURN count(n)").result_set[0][0], gdb.graph().ro_query("MATCH ()-[r]->() RETURN count(r)").result_set[0][0]
    assert live == (n, r)


def test_idempotent_constraints_indexes():
    e = J("docs/evidence/import.json")
    assert e["identical"] and e["first"]["nodes"] == e["second"]["nodes"] and e["first"]["rels"] == e["second"]["rels"]
    assert len(e["constraints"]) >= 2 and len(e["indexes"]) >= 2
    assert all("violation" in v["error"] for v in e["violation"].values())
    assert e["after_violation"]["nodes"] == e["first"]["nodes"]


def test_provenance_on_all_rels():
    q = "MATCH ()-[r]->() WHERE r.source IS NULL OR r.confidence IS NULL OR r.validFrom IS NULL RETURN count(r)"
    assert gdb.graph().ro_query(q).result_set[0][0] == 0


def test_schema_labels_and_types():
    labels = gdb.graph().ro_query("MATCH (n) RETURN count(DISTINCT labels(n))").result_set[0][0]
    types = gdb.graph().ro_query("MATCH ()-[r]->() RETURN count(DISTINCT type(r))").result_set[0][0]
    assert labels >= 6 and types >= 8


def test_queries_and_manual():
    qs = sorted((ROOT / "queries").glob("c*.cypher")); text = "\n".join(f.read_text(encoding="utf-8") for f in qs)
    assert len(qs) >= 8 and "shortestPath" in text and "OPTIONAL MATCH" in text and "*1..3" in text and "WITH" in text
    man = J("queries/results/manual_verification.json")
    assert len(man) >= 3 and all(v["match"] for v in man.values())


def test_gds_saved():
    g = J("docs/evidence/gds.json")
    assert len(g["pagerank"]["top10"]) == 10 and g["louvain"]["n"] >= 3
    assert gdb.graph().ro_query("MATCH (n) WHERE n.pagerank IS NULL OR n.community IS NULL RETURN count(n)").result_set[0][0] == 0
    b = g["bench"]; assert b["answers_equal"] and b["before_index"]["ms_median"] < b["before"]["ms_median"]
