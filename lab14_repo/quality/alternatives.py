"""Alternative-claims register: every conflicting claim is kept with provenance, scope, validity and the decision that governs it.
Status: active (default answer) | alternative (valid in a stated scope) | superseded (no longer valid) | outdated_flag (chunk-level flag)."""
import csv, json, re, pathlib
from .common import ROOT, STORE, graph_csv
from . import conflicts as C
DEC = {r["conflict_id"]: r for r in csv.DictReader(open(ROOT / "quality/decisions.csv", encoding="utf-8"))}

def build(store=STORE):
    th = {r["annotation"]: r for r in graph_csv(store, "nodes_Threshold.csv") if r["variantType"] in ("all", "SNP")}; claims = []
    for cf in C.detect(store):
        d = DEC.get(cf["id"])
        if cf["type"] == "value":
            g, n = cf["items"]
            claims.append(dict(claim_id=f"{cf['id']}:default", conflict_id=cf["id"], subject=cf["subject"], value=g["value"], op=cf["op"], status="active", scope="default (vendor documentation)",
                               source=g["source"], origin=g["origin"], confidence=1.0, validFrom="2026-10-26", validTo=None, decision=cf["id"]))
            claims.append(dict(claim_id=f"{cf['id']}:local", conflict_id=cf["id"], subject=cf["subject"], value=n["value"], op=cf["op"], status="alternative", scope="local SOP / clinic protocol; not the vendor default",
                               source=n["source"], origin=n["origin"], confidence=0.6, validFrom="2026-09-01", validTo=None, decision=cf["id"]))
        elif cf["id"] == "CF-JAVA":
            a, b = cf["items"]
            claims.append(dict(claim_id="CF-JAVA:current", conflict_id=cf["id"], subject=cf["subject"], value="17", op="=", status="active", scope="GATK 4.x (current README)", source=a["source"], origin=a["origin"], confidence=1.0, validFrom="2026-10-26", validTo=None, decision=cf["id"]))
            claims.append(dict(claim_id="CF-JAVA:legacy", conflict_id=cf["id"], subject=cf["subject"], value="8", op="=", status="superseded", scope="GATK v4.2 legacy build notes", source=b["source"], origin=b["origin"], confidence=0.4, validFrom="2026-09-01", validTo="2026-10-26", decision=cf["id"]))
        elif cf["id"] == "CF-JAVA-TUT":
            a, b = cf["items"]
            claims.append(dict(claim_id="CF-JAVA-TUT:tutorial", conflict_id=cf["id"], subject=cf["subject"], value="1.8", op="=", status="outdated_flag", scope="Funcotator tutorial page", source=b["source"], origin=b["origin"], confidence=0.4, validFrom="2026-08-17", validTo=None, decision=cf["id"]))
    for c in claims: c["decided_by"] = DEC[c["conflict_id"]]["decided_by"]; c["decided_at"] = DEC[c["conflict_id"]]["decided_at"]; c["decision_status"] = DEC[c["conflict_id"]]["status"]
    return claims

def to_cypher(claims):
    q = []
    for c in claims:
        props = ", ".join(f"{k}: {json.dumps(v)}" for k, v in c.items() if v is not None)
        q.append(f"MERGE (c:Claim {{claim_id: {json.dumps(c['claim_id'])}}}) SET c += {{{props}}};")
        if c["source"].startswith("graph:Threshold:"):
            q.append(f"MATCH (c:Claim {{claim_id: {json.dumps(c['claim_id'])}}}), (t:Threshold {{id: {json.dumps(c['source'].split(':')[-1])}}}) MERGE (c)-[:ABOUT]->(t);")
    for cid in {c["conflict_id"] for c in claims}:
        q.append(f"MATCH (a:Claim {{conflict_id: {json.dumps(cid)}, status: 'active'}}), (b:Claim {{conflict_id: {json.dumps(cid)}}}) WHERE b.status <> 'active' MERGE (b)-[:ALTERNATIVE_TO {{decision: {json.dumps(cid)}}}]->(a);")
    return q
