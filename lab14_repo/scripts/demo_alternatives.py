"""R3 C3: write the alternatives register to store_clean/alternatives.jsonl + Cypher, load it into an embedded FalkorDB next to the lab-9 graph and query it."""
import sys, json, shutil, tempfile, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from quality import alternatives as A
from quality.common import ROOT
(ROOT / "store_clean").mkdir(exist_ok=True)
cl = A.build(); open(ROOT / "store_clean/alternatives.jsonl", "w", encoding="utf-8").write("\n".join(json.dumps(c, ensure_ascii=False) for c in cl) + "\n")
q = A.to_cypher(cl); open(ROOT / "quality/alternatives.cypher", "w", encoding="utf-8").write("\n".join(q) + "\n")
from redislite.falkordb_client import FalkorDB
tmp = tempfile.mkdtemp(); db = FalkorDB(tmp + "/g.db"); g = db.select_graph("dkh_alt")
for l in ("Threshold",):   # a minimal copy of the Threshold nodes from the graph CSV so that ABOUT edges can be created
    import csv
    for r in csv.DictReader(open(ROOT / "store/graph/nodes_Threshold.csv")): g.query("MERGE (t:Threshold {id: $id}) SET t.annotation=$a, t.value=$v", {"id": r["id"], "a": r["annotation"], "v": float(r["value"])})
for s in q: g.query(s)
res = {}
res["claims"] = g.ro_query("MATCH (c:Claim) RETURN count(c)").result_set[0][0]
res["alternatives_of_QD"] = [list(r) for r in g.ro_query("MATCH (b:Claim)-[:ALTERNATIVE_TO]->(a:Claim {conflict_id:'CF-QD'}) RETURN b.value, b.status, b.scope, b.source, b.decided_by, b.decided_at, a.value").result_set]
res["active_per_conflict"] = [list(r) for r in g.ro_query("MATCH (c:Claim {status:'active'}) RETURN c.conflict_id, c.value, c.source ORDER BY c.conflict_id").result_set]
res["claims_about_threshold_QD_lt_2"] = [list(r) for r in g.ro_query("MATCH (c:Claim)-[:ABOUT]->(t:Threshold {id:'QD_lt_2'}) RETURN c.claim_id, c.value, c.status").result_set]
res["superseded"] = [list(r) for r in g.ro_query("MATCH (c:Claim) WHERE c.status IN ['superseded','outdated_flag'] RETURN c.claim_id, c.value, c.status, c.validTo").result_set]
shutil.rmtree(tmp, ignore_errors=True); json.dump(res, open(ROOT / "eval/alternatives_demo.json", "w"), indent=1, ensure_ascii=False); print(json.dumps(res, indent=1, ensure_ascii=False))
