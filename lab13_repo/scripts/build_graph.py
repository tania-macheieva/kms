"""R5: normalise + link extracted entities, write RDF (Turtle, reified statements with provenance) and Cypher, load into FalkorDB(lite), run the evidence query.
Input: post-hoc hybrid extraction over ALL passages (entities: method B; HAS_OPTION: method A; other relations: method B)."""
import sys, json, csv, collections, pathlib, re
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from common import *
rd = lambda p: [json.loads(l) for l in open(ROOT / p, encoding="utf-8")]
P = {p["id"]: p for p in load_passages()}
A = rd("results/rules_dev.jsonl") + rd("results/rules_test.jsonl"); B = rd("results/llm_dev_v2.jsonl") + rd("results/llm_test_v2.jsonl")
rows = [r for r in B if r["kind"] == "entity"] + [r for r in A if r["kind"] == "relation" and r["relation"] == "HAS_OPTION"] + \
       [r for r in B if r["kind"] == "relation" and r["relation"] != "HAS_OPTION"]
aliases = {norm(r["alias"]): r["canonical"] for r in csv.DictReader(open(ROOT / "data/aliases.csv"))}
links = {(norm(r["canonical"]), r["type"]): r for r in csv.DictReader(open(ROOT / "data/ontology_links.csv"))}

def confidence(r):
    if r["method"] == "rules": return float(r.get("confidence") or 0.5)
    if r["kind"] == "relation":
        txt = P[r["passage_id"]]["text"]; ok = r["evidence"] in txt and (norm(r["object"]) in norm(r["evidence"]) or norm(r["subject"]) in norm(r["evidence"]))
        return 0.8 if ok else 0.4
    return 0.8
# canonical entities (typed): key=(norm canonical, type)
surf = collections.defaultdict(collections.Counter); ent_docs = collections.defaultdict(set)
def canon(text):
    n = norm(text); c = aliases.get(n)
    return (c if c else text.strip("`")), norm(c if c else text)
for r in rows:
    if r["kind"] == "entity":
        c, k = canon(r["text"]); surf[(k, r["type"])][r["text"].strip("`")] += 1; ent_docs[(k, r["type"])].add(r["document"])
for r in rows:
    if r["kind"] == "relation":
        ts, to = REL_TYPES[r["relation"]]
        for t, ty in ((r["subject"], ts), (r["object"], to)):
            c, k = canon(t); surf[(k, ty)][t.strip("`")] += 1; ent_docs[(k, ty)].add(r["document"])
ents = {}
for (k, ty), cnt in surf.items():
    name = next((v["canonical"] for v in csv.DictReader(open(ROOT / "data/aliases.csv")) if norm(v["canonical"]) == k), None) or cnt.most_common(1)[0][0]
    lk = links.get((k, ty)) or next((v for (kk, tt), v in links.items() if kk == k and tt == ty), None)
    ents[(k, ty)] = {"id": f"E{len(ents)+1:04d}", "name": name, "type": ty, "key": k, "aliases": sorted(set(cnt) - {name}), "n_docs": len(ent_docs[(k, ty)]),
                     "onto_class": lk["onto_class"] if lk else "", "link_rule": lk["rule"] if lk else ""}
with open(ROOT / "data/entities_linked.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["id", "name", "type", "aliases", "n_docs", "onto_class", "link_rule"])
    for e in sorted(ents.values(), key=lambda e: (-e["n_docs"], e["name"])): w.writerow([e["id"], e["name"], e["type"], "|".join(e["aliases"]), e["n_docs"], e["onto_class"], e["link_rule"]])
# statements
stm = {}
for r in rows:
    if r["kind"] != "relation": continue
    ts, to = REL_TYPES[r["relation"]]
    s, o = ents[(canon(r["subject"])[1], ts)], ents[(canon(r["object"])[1], to)]
    k = (s["id"], r["relation"], o["id"], r["passage_id"])
    if k not in stm:
        stm[k] = dict(s=s, o=o, rel=r["relation"], document=r["document"], passage=r["passage_id"], start=r["start"], end=r["end"], doc_start=r["doc_start"],
                      evidence=r["evidence"], model=r["model"], prompt=r["prompt_version"], method=r["method"], conf=confidence(r))
stm = list(stm.values())
# Turtle
from rdflib import Graph, Namespace, Literal, RDF, RDFS, XSD
EX = Namespace("http://example.org/dkh13/"); g = Graph(); g.bind("ex", EX)
for e in ents.values():
    u = EX[e["id"]]; g.add((u, RDF.type, EX[e["type"]])); g.add((u, RDFS.label, Literal(e["name"])))
    if e["onto_class"]: g.add((u, EX.ontologyClass, EX["lab7_" + e["onto_class"]]))
    for a in e["aliases"]: g.add((u, EX.alias, Literal(a)))
for i, s in enumerate(stm, 1):
    st = EX[f"stmt{i:04d}"]; g.add((EX[s["s"]["id"]], EX[s["rel"]], EX[s["o"]["id"]]))
    g.add((st, RDF.type, EX.Statement)); g.add((st, RDF.subject, EX[s["s"]["id"]])); g.add((st, RDF.predicate, EX[s["rel"]])); g.add((st, RDF.object, EX[s["o"]["id"]]))
    for p_, v, dt in (("source", s["document"], None), ("passage", s["passage"], None), ("evidence", s["evidence"], None), ("model", s["model"], None), ("promptVersion", s["prompt"], None),
                      ("method", s["method"], None), ("startOffset", s["start"], XSD.integer), ("endOffset", s["end"], XSD.integer), ("docStartOffset", s["doc_start"], XSD.integer), ("confidence", s["conf"], XSD.decimal)):
        g.add((st, EX[p_], Literal(v, datatype=dt) if dt else Literal(v)))
g.serialize(ROOT / "data/graph_load.ttl", format="turtle")
# Cypher
q = lambda s: json.dumps(s, ensure_ascii=False)
lines = ["// generated by scripts/build_graph.py -- Neo4j/FalkorDB compatible openCypher", "CREATE INDEX FOR (n:Entity) ON (n.id);"]
for e in ents.values():
    lines.append(f"MERGE (n:Entity {{id:{q(e['id'])}}}) SET n.name={q(e['name'])}, n.type={q(e['type'])}, n.ontology_class={q(e['onto_class'])}, n.n_docs={e['n_docs']};")
for s in stm:
    lines.append(f"MATCH (a:Entity {{id:{q(s['s']['id'])}}}), (b:Entity {{id:{q(s['o']['id'])}}}) CREATE (a)-[:{s['rel']} {{source:{q(s['document'])}, passage:{q(s['passage'])}, start:{s['start']}, end:{s['end']}, "
                 f"doc_start:{s['doc_start']}, evidence:{q(s['evidence'])}, model:{q(s['model'])}, prompt_version:{q(s['prompt'])}, method:{q(s['method'])}, confidence:{s['conf']}}}]->(b);")
(ROOT / "data/graph_load.cypher").write_text("\n".join(lines) + "\n", encoding="utf-8")
# load into FalkorDB(lite) and run evidence query
from redislite.falkordb_client import FalkorDB
import shutil
dbp = ROOT / "fdb"; shutil.rmtree(dbp, ignore_errors=True); dbp.mkdir()
db = FalkorDB(str(dbp / "graph.db")); gr = db.select_graph("lab13")
for l in lines[1:]:
    try: gr.query(l)
    except Exception as ex:
        if "already indexed" not in str(ex): raise
EVQ = "MATCH (a:Entity)-[r:HAS_OPTION|PERFORMS|ACCEPTS|PRODUCES|INVOKES|COMPUTES_METRIC|USES_RESOURCE]->(b:Entity) RETURN a.name, type(r), b.name, r.source, r.start, r.end, r.model, r.confidence, r.evidence ORDER BY r.confidence DESC, a.name LIMIT 8"
EVQ2 = "MATCH (a:Entity)-[r:PERFORMS]->(b:Entity) RETURN a.name, b.name, r.source, r.start, r.end, r.model, r.confidence, r.evidence ORDER BY r.confidence DESC"
res = {"nodes": gr.ro_query("MATCH (n) RETURN count(n)").result_set[0][0], "relationships": gr.ro_query("MATCH ()-[r]->() RETURN count(r)").result_set[0][0],
       "rel_by_type": dict(gr.ro_query("MATCH ()-[r]->() RETURN type(r), count(r)").result_set),
       "evidence_query": EVQ2, "evidence_rows": gr.ro_query(EVQ2).result_set[:8],
       "entities_by_type": dict(collections.Counter(e["type"] for e in ents.values())),
       "linked_entities": sum(bool(e["onto_class"]) for e in ents.values()), "aliases_merged": sum(len(e["aliases"]) for e in ents.values()),
       "entities_ge2_docs": sum(e["n_docs"] >= 2 for e in ents.values()), "statements": len(stm), "ttl_triples": len(g)}
json.dump(res, open(ROOT / "eval/graph_stats.json", "w"), indent=1, ensure_ascii=False, default=str)
print(json.dumps({k: v for k, v in res.items() if k != "evidence_rows"}, indent=1)); print(res["evidence_rows"][:3])
