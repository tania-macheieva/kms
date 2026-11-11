"""CI checks of the knowledge store. Tools: pySHACL (Q01), SPARQL/rdflib (Q02-Q04), JSON Schema (Q05-Q07), SQL/DuckDB (Q08-Q10),
metric thresholds (Q11, 14 parametrised) and plain pytest (Q12). QUALITY_STORE selects the snapshot (default store_clean)."""
import json, glob, pathlib, pytest, duckdb, jsonschema
from quality.common import ROOT, read_jsonl
from quality import shacl_run, dedup as D
CSV = "header=true, all_varchar=true, delim=',', quote='\"', escape='\"', strict_mode=false"

def test_Q01_shacl_conforms(store):
    ok, by, msgs, _ = shacl_run.validate(store); assert ok, f"SHACL violations {by}: {msgs[:3]}"

def test_Q02_sparql_no_orphan_variants(rdf):
    q = "PREFIX d: <http://dkh.example/> SELECT ?v WHERE { ?v a d:Variant . FILTER NOT EXISTS { ?v d:LOCATED_IN ?g } }"; assert len(list(rdf.query(q))) == 0
def test_Q03_sparql_hardfiltering_has_thresholds(rdf):
    q = 'PREFIX d: <http://dkh.example/> SELECT ?p WHERE { ?p a d:Procedure ; d:kind "HardFiltering" . FILTER NOT EXISTS { ?p d:HAS_THRESHOLD ?t } }'; assert len(list(rdf.query(q))) == 0
def test_Q04_sparql_annotation_names_unique_per_variant(rdf):
    q = "PREFIX d: <http://dkh.example/> SELECT ?v ?n (COUNT(?a) AS ?c) WHERE { ?v d:HAS_ANNOTATION ?a . ?a d:name ?n } GROUP BY ?v ?n HAVING (COUNT(?a) > 1)"; assert len(list(rdf.query(q))) == 0

def test_Q05_jsonschema_chunks(chunks_):
    v = jsonschema.Draft202012Validator(json.load(open(ROOT / "schema/chunk.schema.json"))); bad = [(c["chunk_id"], e.message[:60]) for c in chunks_ for e in v.iter_errors(c)]; assert not bad, bad[:3]
def test_Q06_jsonschema_alternatives(store):
    f = store / "alternatives.jsonl"; assert f.exists(), "no alternatives register"
    v = jsonschema.Draft202012Validator(json.load(open(ROOT / "schema/alternative.schema.json"))); bad = [(c["claim_id"], e.message[:60]) for c in read_jsonl(f) for e in v.iter_errors(c)]; assert not bad, bad[:3]
def test_Q07_jsonschema_fixtures(store):
    v = jsonschema.Draft202012Validator(json.load(open(ROOT / "schema/fixture.schema.json"))); bad = [n["id"] for n in json.load(open(store / "fixtures.json")) for e in v.iter_errors(n)]; assert not bad, bad

def test_Q08_sql_unique_chunk_ids(store):
    n = duckdb.sql(f"SELECT count(*) - count(DISTINCT chunk_id) FROM read_json_auto('{store}/corpus.jsonl')").fetchall()[0][0]; assert n == 0
def test_Q09_sql_applies_to_person_integrity(store):
    r, p = f"{store}/graph/rels_APPLIES_TO__Procedure_Person.csv", f"{store}/graph/nodes_Person.csv"
    n = duckdb.sql(f"SELECT count(*) FROM read_csv('{r}', {CSV}) r LEFT JOIN read_csv('{p}', {CSV}) p ON r.\"to\" = p.name WHERE p.name IS NULL").fetchall()[0][0]; assert n == 0
def test_Q10_sql_relationship_provenance(store):
    bad = 0
    for f in glob.glob(f"{store}/graph/rels_*.csv"):
        bad += duckdb.sql(f"SELECT count(*) FROM read_csv('{f}', {CSV}) WHERE coalesce(trim(source),'') = '' OR coalesce(trim(validFrom),'') = ''").fetchall()[0][0]
    assert bad == 0, f"{bad} relationships without source/validFrom"

THR = json.load(open(ROOT / "quality/thresholds.json"))
@pytest.mark.parametrize("m", sorted(THR))
def test_Q11_metric_threshold(m, profile):
    if m not in profile: pytest.skip("metric not computed")
    v = profile[m]; assert v["ok"], f"{m}={v['value']} violates {v['op']} {v['threshold']} ({v['severity']})"

def test_Q12_merge_is_reversible(store, chunks_):
    merged = [c for c in chunks_ if c.get("merged_from")]; allun = chunks_
    for c in merged: allun = D.unmerge(allun, c["chunk_id"])
    assert len({c["chunk_id"] for c in allun}) == len(chunks_) + sum(len(c["merged_from"]) for c in merged)
    for c in merged:
        for m in c["merged_from"]: assert {"chunk_id", "text", "doc_id", "start", "end"} <= set(m)   # full provenance kept
