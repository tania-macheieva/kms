"""Автоматичні перевірки SKOS-таксономії (models/taxonomy.ttl) та її CSV-джерела."""
import csv
import re
from collections import Counter
from pathlib import Path

import pytest
from rdflib import Graph, RDF, URIRef
from rdflib.namespace import SKOS

ROOT = Path(__file__).resolve().parent.parent
TTL = ROOT / "models/taxonomy.ttl"


@pytest.fixture(scope="module")
def g():
    graph = Graph()
    graph.parse(TTL, format="turtle")                    # C1: файл валідний (парситься rdflib)
    return graph


@pytest.fixture(scope="module")
def concepts(g):
    return sorted(set(g.subjects(RDF.type, SKOS.Concept)))


def en_labels(g, c):
    return [str(o) for o in g.objects(c, SKOS.prefLabel) if o.language == "en"]


def test_ttl_parses_and_has_scheme(g, concepts):
    assert len(concepts) >= 40
    assert len(list(g.subjects(RDF.type, SKOS.ConceptScheme))) == 1
    assert len(list(g.objects(None, SKOS.hasTopConcept))) >= 1


def test_every_concept_has_one_english_preflabel(g, concepts):
    bad = [c for c in concepts if len(en_labels(g, c)) != 1]
    assert not bad, bad


def test_every_preflabel_has_language_tag(g):
    assert all(o.language for o in g.objects(None, SKOS.prefLabel))
    assert all(o.language for o in g.objects(None, SKOS.altLabel))


def test_no_cycles_in_broader(g, concepts):
    for c in concepts:
        seen, cur = {c}, c
        while True:
            parents = list(g.objects(cur, SKOS.broader))
            if not parents:
                break
            cur = parents[0]
            assert cur not in seen, f"цикл через {c}"
            seen.add(cur)


def test_exactly_one_broader_except_top(g, concepts):
    tops = set(g.subjects(SKOS.topConceptOf, None))
    for c in concepts:
        n = len(list(g.objects(c, SKOS.broader)))
        assert n == (0 if c in tops else 1), (c, n)


def test_every_non_root_has_definition(g, concepts):
    tops = set(g.subjects(SKOS.topConceptOf, None))
    missing = [c for c in concepts if c not in tops and not list(g.objects(c, SKOS.definition))]
    assert not missing, missing


def test_preferred_labels_unique(g, concepts):
    labels = Counter(en_labels(g, c)[0].casefold() for c in concepts)
    assert [l for l, n in labels.items() if n > 1] == []


def test_share_of_other_is_zero(g, concepts):
    other = [c for c in concepts if re.search(r"\b(other|misc\w*|різне|інше)\b", en_labels(g, c)[0], re.I)]
    assert len(other) / len(concepts) == 0


def test_at_least_five_verified_external_links(g):
    links = list(g.subject_objects(SKOS.exactMatch)) + list(g.subject_objects(SKOS.closeMatch))
    assert len(links) >= 5
    rows = list(csv.DictReader(open(ROOT / "data/external_links.csv", encoding="utf-8")))
    verified = {r["external_uri"] for r in rows if r["verification_result"].startswith("verified")}
    assert all(str(o) in verified for _, o in links)       # кожен зв'язок має запис про верифікацію
    assert all(isinstance(o, URIRef) and str(o).startswith("http") for _, o in links)


def test_depth_and_principles_in_final_csv():
    rows = list(csv.DictReader(open(ROOT / "models/taxonomy_final.csv", encoding="utf-8-sig")))
    by_id = {r["id"]: r for r in rows}
    assert max(int(r["level"]) for r in rows) >= 3
    parents = {r["parent"] for r in rows if r["parent"]}
    for r in rows:
        if r["id"] in parents:
            assert r["principle"], f"немає принципу поділу для {r['label']}"        # принцип поділу на кожному внутрішньому вузлі
    for lvl in {int(r["level"]) for r in rows if r["id"] in parents}:
        assert any(r["principle"] for r in rows if int(r["level"]) == lvl and r["id"] in parents)
    assert by_id[rows[0]["id"]]["parent"] == ""


def test_no_part_of_division_principle():
    """Змішування is-a та part-of: у принципах поділу немає слів про частини/складові."""
    rows = list(csv.DictReader(open(ROOT / "models/taxonomy_final.csv", encoding="utf-8-sig")))
    bad = [r["label"] for r in rows if re.search(r"частин|складов|part[- ]of", r["principle"], re.I)]
    assert not bad, bad


def test_no_category_with_single_child():
    """Категорії (не терміни) мають ≥ 2 дітей; єдина дитина допустима лише під термінами (вужче поняття)."""
    rows = list(csv.DictReader(open(ROOT / "models/taxonomy_final.csv", encoding="utf-8-sig")))
    kids = Counter(r["parent"] for r in rows if r["parent"])
    bad = [r["label"] for r in rows if not r["term_id"] and kids.get(r["id"], 0) == 1]
    assert not bad, bad


def test_csv_and_skos_consistent(g, concepts):
    rows = list(csv.DictReader(open(ROOT / "models/taxonomy_final.csv", encoding="utf-8-sig")))
    assert len(rows) == len(concepts)
