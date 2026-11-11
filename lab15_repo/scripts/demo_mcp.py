"""MCP client demo (R2 C1): starts mcp_server over stdio, lists the tools, calls them, shows role denial and the write attempt being rejected -> logs/mcp_demo.json
   python scripts/demo_mcp.py [reader|analyst]"""
import asyncio, sys, json, os, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
async def main(role):
    env = dict(os.environ, DKH_ROLE=role); p = StdioServerParameters(command=sys.executable, args=["-m", "mcp_server.server"], cwd=str(ROOT), env=env); out = dict(role=role, calls=[])
    async with stdio_client(p, errlog=open(os.devnull, "w")) as (r, w):
        async with ClientSession(r, w) as s:
            await s.initialize(); lt = await s.list_tools(); out["tools"] = [t.name for t in lt.tools]; print("tools:", out["tools"])
            demo = [("graph_query", dict(cypher="MATCH (p:GenePanel)-[:HAS_MEMBER]->(g:Gene) RETURN p.name, collect(g.symbol)")), ("sql_metric", dict(metric="call_count", by=["year"])), ("get_claims", dict(conflict_id="CF-QD")),
                    ("search_docs", dict(query="hard filtering QD threshold", k=2)), ("graph_query", dict(cypher="MATCH (p:Person) RETURN p.name")), ("graph_query", dict(cypher="MATCH (g:Gene) DETACH DELETE g")), ("sql_metric", dict(metric="call_count; DROP TABLE x"))]
            for name, args in demo:
                try:
                    res = await s.call_tool(name, args); txt = " ".join(c.text for c in res.content if hasattr(c, "text"))
                except Exception as e: txt = f"EXC {type(e).__name__}: {str(e)[:150]}"
                out["calls"].append(dict(tool=name, args=args, result=txt[:300])); print(f"{name} {json.dumps(args)[:70]} -> {txt[:140]!r}")
    json.dump(out, open(ROOT / f"logs/mcp_demo_{role}.json", "w"), ensure_ascii=False, indent=1)
asyncio.run(main(sys.argv[1] if len(sys.argv) > 1 else "reader"))
