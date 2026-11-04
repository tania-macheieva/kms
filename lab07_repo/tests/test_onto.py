"""Тести ЛР7: таблиця класів, OWL, індивіди, HermiT, ситуації, CQ, claims."""
import csv
import json
import re
import shutil
import sys
from pathlib import Path

import pytest
from rdflib import BNode, Graph, URIRef
from rdflib.namespace import OWL, RDF, RDFS

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
HAVE_JAVA = shutil.which("java") is not None


def rd(p): return list(csv.DictReader(open(ROOT / p, encoding="utf-8-sig")))
@pytest.fixture(scope="module")
def onto(): return Graph().parse(ROOT / "models/onto.owl", format="turtle")
@pytest.fixture(scope="module")
def data(): return Graph().parse(ROOT / "models/onto_data.ttl", format="turtle")


def test_class_table():
    t = rd("models/class_table.csv")
    assert len(t) >= 30 and all(r["definition"] and r["genus"] and r["differentia"] for r in t)


def test_property_dictionary():
    p = rd("models/property_dictionary.csv")
    assert sum(r["type"] == "object" for r in p) >= 10 and sum(r["type"] == "data" for r in p) >= 5
    assert all(r["domain"] and r["range"] for r in p)


def test_definition_check_clean():
    import check_definitions
    issues, cycles = check_definitions.check()
    assert not issues and not cycles


def test_reuse_mapping(onto):
    from rdflib.namespace import SKOS
    assert any(str(o).startswith("http://id.nlm.nih.gov/mesh/") for o in onto.objects(None, SKOS.exactMatch)) and len(list(onto.subject_objects(SKOS.closeMatch))) >= 10


def test_onto_structure(onto):
    classes = [c for c in onto.subjects(RDF.type, OWL.Class) if isinstance(c, URIRef)]
    assert len(classes) >= 30
    assert len(list(onto.subjects(RDF.type, OWL.AllDisjointClasses))) >= 5
    R = list(onto.subjects(RDF.type, OWL.Restriction))
    assert sum(1 for r in R if (r, OWL.someValuesFrom, None) in onto or (r, OWL.allValuesFrom, None) in onto) >= 3
    assert sum(1 for r in R if any((r, p, None) in onto for p in (OWL.minQualifiedCardinality, OWL.maxQualifiedCardinality, OWL.qualifiedCardinality))) >= 2
    ob = list(onto.subjects(RDF.type, OWL.ObjectProperty)); da = list(onto.subjects(RDF.type, OWL.DatatypeProperty))
    assert len(ob) >= 10 and len(da) >= 5
    chars = sum(1 for p in ob if (p, RDF.type, OWL.TransitiveProperty) in onto or (p, RDF.type, OWL.SymmetricProperty) in onto or (p, OWL.inverseOf, None) in onto)
    assert chars >= 2


def test_individuals(data):
    inds = [i for i in data.subjects(RDF.type, OWL.NamedIndividual) if not re.search(r"#(S0\d_|Situation_)", str(i))]
    assert len(inds) >= 20
    avg = sum(sum(1 for p, o in data.predicate_objects(i) if p not in (RDF.type, RDFS.label)) for i in inds) / len(inds)
    assert avg >= 3


@pytest.mark.skipif(not HAVE_JAVA, reason="потрібна Java для HermiT")
def test_hermit_consistent_and_inferences():
    from rdflib import Graph as G
    from reasoner_run import merged_graph
    from reasoning import infer
    ok, inf, _ = infer(merged_graph())
    assert ok
    assert sum(1 for _ in inf.subject_objects(RDF.type)) >= 3
    assert "Суперечність 1" in (ROOT / "docs/reasoner_log.md").read_text(encoding="utf-8")


@pytest.mark.skipif(not HAVE_JAVA, reason="потрібна Java для HermiT")
def test_contradiction_detected():
    from reasoner_run import D, merged_graph
    from reasoning import infer
    assert infer(merged_graph(extra=[(D["VAR-003"], RDF.type, D.SNP)]))[0] is False


def test_situations(onto):
    s = rd("models/situations.csv")
    assert len(s) >= 5 and all(all(v for v in r.values()) for r in s)
    ids = {str(c).split("#")[-1] for c in onto.subjects(RDF.type, OWL.Class)}
    for r in s:
        for k in ("initial_state_class", "event_class", "guard_class", "new_state_class", "action_class"):
            assert r[k].split(":")[1] in ids
    meta = {r["field"] for r in rd("models/model_meta.csv")}
    assert {"version", "owner", "sources", "status_of_trust"} <= meta


@pytest.mark.skipif(not HAVE_JAVA, reason="потрібна Java для HermiT")
def test_situation_queries():
    import verify_situations
    assert verify_situations.run()[0]


@pytest.mark.skipif(not HAVE_JAVA, reason="потрібна Java для HermiT")
def test_cq_mine_and_llm():
    import run_cq
    out, share, ok = run_cq.run("mine"); assert ok and len(out) >= 10 and share >= 0.9
    out2, share2, ok2 = run_cq.run("llm"); assert ok2 and len(out2) >= 10


@pytest.mark.skipif(not HAVE_JAVA, reason="потрібна Java для HermiT")
def test_cq_detects_missing_axiom():
    """Чутливість CQ: без аксіоми VQSR requires … CQ05 має провалитись."""
    import json as j
    import run_cq
    from reasoning import infer
    g = run_cq.load("mine")
    vq = next(s for s in g.subjects(RDFS.label, None) if str(s).endswith("#VQSR"))
    for r in list(g.objects(vq, RDFS.subClassOf)):
        if isinstance(r, BNode) and (r, OWL.onProperty, None) in g and str(g.value(r, OWL.onProperty)).endswith("#requires"): g.remove((vq, RDFS.subClassOf, r))
    ok, inf, _ = infer(g); g += inf
    q = (ROOT / "tests/cq_sparql/CQ05.rq").read_text(encoding="utf-8")
    got = {str(r["answer"]) for r in g.query(q)}
    assert got != set(j.loads(re.search(r"# expect: (.*)", q).group(1)))


def test_claims_and_logs():
    c = rd("claims/claims.csv")
    assert c and all(x["status"] in {"verified", "rejected", "pending"} and x["verification_level"] in {"V1", "V2", "V3", "V4"} for x in c)
    assert sum(x["status"] == "rejected" for x in c) >= 3
    assert (ROOT / "llm_log/log.csv").exists()


def test_no_api_keys():
    pat = re.compile(r"(sk-[A-Za-z0-9]{20,}|api[_-]?key\s*=\s*['\"][^'\"]+)", re.I)
    for f in list((ROOT / "scripts").glob("*.py")) + list((ROOT / "tests").glob("*.py")):
        assert not pat.search(f.read_text(encoding="utf-8")), f
