"""Демонстрація шарів безпеки text-to-Cypher → docs/evidence/t2c_safety.json"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import t2c  # noqa: E402

cases = [("запис через CREATE", "MATCH (n:Gene) CREATE (:Hack {x: 1}) RETURN n.symbol"), ("видалення", "MATCH (n) DETACH DELETE n"), ("SET властивості", "MATCH (v:Variant {id:'VAR-001'}) SET v.type = 'X' RETURN v"),
         ("виклик процедури", "CALL db.constraints()"), ("вигадана мітка", "MATCH (x:Mutation) RETURN x"), ("вигадана властивість", "MATCH (v:Variant) RETURN v.qualityScore"), ("вигаданий тип зв'язку", "MATCH (a)-[:KNOWS]->(b) RETURN a")]
out = []
for name, q in cases:
    safe, msg = t2c.check_safe(q); sch, bad = t2c.check_schema(q) if safe else (None, [])
    out.append({"case": name, "query": q, "static_safe": safe, "static_msg": msg, "schema_ok": sch, "schema_msg": bad})
# другий шар: обходимо статичний фільтр і шлемо запис прямо в RO_QUERY
try: t2c.gdb.graph().ro_query("CREATE (:Hack {x: 1})"); rw = "(помилки немає — запис пройшов!)"
except Exception as e: rw = str(e)
cnt = t2c.gdb.graph().ro_query("MATCH (n:Hack) RETURN count(n)").result_set[0][0]
lim = t2c.with_limit("MATCH (n) RETURN n.name")
res = {"cases": out, "ro_query_write_error": rw, "hack_nodes_after": cnt, "limit_appended": lim.split("\n")[-1]}
t2c.ROOT.joinpath("docs/evidence/t2c_safety.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
print(json.dumps(res, ensure_ascii=False)[:900])
