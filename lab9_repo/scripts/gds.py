"""Аналіз графа та продуктивність (Результат 4). Збереження pagerank/community у вузлах; PROFILE та оптимізація на синтетичному графі.
Рушій: FalkorDB. PageRank — нативний (CALL algo.pageRank); Louvain у FalkorDB відсутній → networkx.louvain_communities (seed 42) на вигрузці графа
(це не Neo4j GDS; результати збережено назад у граф)."""
import json
import statistics
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

import networkx as nx
from networkx.algorithms.community import louvain_communities, modularity

sys.path.insert(0, str(Path(__file__).parent))
import graphdb as gdb  # noqa: E402

ROOT = gdb.ROOT
KEYS = ["name", "id", "symbol", "code"]
SEED = 42


def name_of(labels, props):
    for k in KEYS:
        if k in props: return f"{labels[0]}:{props[k]}"
    return labels[0]


def export():
    g = gdb.graph()
    nodes = {}
    for nid, labels, props in g.ro_query("MATCH (n) RETURN id(n), labels(n), properties(n)").result_set: nodes[nid] = {"labels": labels, "name": name_of(labels, props)}
    edges = [(a, b, t) for a, b, t in g.ro_query("MATCH (a)-[r]->(b) RETURN id(a), id(b), type(r)").result_set]
    return nodes, edges


def pagerank_native():
    return {nid: s for nid, s in gdb.ro("CALL algo.pageRank(null, null) YIELD node, score RETURN id(node), score").result_set}


def profile(q, reps=5):
    g = gdb.graph(); ops = []
    def walk(o, d=0):
        ops.append((d, o.name, str(o.args or ""), o.records_produced, round(o.execution_time, 3)))
        for c in o.children: walk(c, d + 1)
    walk(g.profile(q).structured_plan)
    ts = []
    for _ in range(reps):
        t = time.perf_counter(); g.ro_query(q); ts.append((time.perf_counter() - t) * 1000)
    return {"ops": ops, "ms_median": round(statistics.median(ts), 2)}


def bench_graph(n):
    g = gdb.graph("bench")
    try: g.delete()
    except Exception: pass
    g = gdb.graph("bench")
    # детермінована «псевдовипадковість» без генератора: значення залежать лише від i (відтворюється без seed)
    g.query(f"""UNWIND range(0, {n - 1}) AS i
      CREATE (v:Variant {{id: 'B-' + toString(i), type: CASE WHEN i % 5 = 0 THEN 'Indel' ELSE 'SNP' END}})
      WITH v, i UNWIND [['QD', 3500, 13], ['FS', 8000, 29], ['SOR', 600, 7], ['MQ', 4000, 41]] AS spec
      CREATE (v)-[:HAS_ANNOTATION]->(:Annotation {{name: spec[0], value: toFloat((i * 7919 + spec[2]) % spec[1]) / 100.0}})""")
    return g


Q_BEFORE = "MATCH (v:Variant)-[:HAS_ANNOTATION]->(a:Annotation) WHERE v.type = 'SNP' AND a.name = 'QD' AND a.value < 2.0 RETURN count(v)"
Q_REWRITE = "MATCH (a:Annotation {name: 'QD'}) WHERE a.value < 2.0 MATCH (v:Variant {type: 'SNP'})-[:HAS_ANNOTATION]->(a) RETURN count(v)"


def main():
    out = {}
    nodes, edges = export()
    pr = pagerank_native()
    # --- перевірка PageRank: networkx на тому самому орієнтованому графі
    D = nx.MultiDiGraph(); D.add_nodes_from(nodes); D.add_edges_from((a, b) for a, b, _ in edges)
    nxpr = nx.pagerank(nx.DiGraph(D), alpha=0.85)
    top = sorted(pr.items(), key=lambda kv: -kv[1])[:10]; topx = sorted(nxpr.items(), key=lambda kv: -kv[1])[:10]
    out["pagerank"] = {"top10": [[nodes[n]["name"], round(s, 5)] for n, s in top], "networkx_top10": [[nodes[n]["name"], round(s, 5)] for n, s in topx],
                       "overlap_top10": len({n for n, _ in top} & {n for n, _ in topx}), "sum": round(sum(pr.values()), 4)}
    # --- Louvain
    U = nx.Graph(); U.add_nodes_from(nodes); U.add_edges_from((a, b) for a, b, _ in edges)
    comms = sorted(louvain_communities(U, seed=SEED, resolution=1.0), key=lambda c: (-len(c), min(c)))
    cid = {n: i for i, c in enumerate(comms) for n in c}
    info = []
    for i, c in enumerate(comms):
        lab = Counter(nodes[n]["labels"][0] for n in c); gen = Counter(nodes[n]["name"] for n in c if nodes[n]["labels"][0] in ("Gene", "Sample", "Person", "Procedure", "Concept", "Threshold", "AnnotationType", "GenePanel"))
        info.append({"id": i, "size": len(c), "labels": dict(lab), "key_nodes": sorted(gen)[:8]})
    out["louvain"] = {"n": len(comms), "modularity": round(modularity(U, comms), 4), "communities": info}
    # --- збереження в граф
    rows = [{"id": n, "pr": pr.get(n, 0.0), "c": cid[n]} for n in nodes]
    gdb.run("UNWIND $rows AS r MATCH (n) WHERE id(n) = r.id SET n.pagerank = r.pr, n.community = r.c", {"rows": rows})
    out["saved"] = {"nodes_with_pagerank": gdb.ro("MATCH (n) WHERE n.pagerank IS NOT NULL RETURN count(n)").result_set[0][0], "nodes_with_community": gdb.ro("MATCH (n) WHERE n.community IS NOT NULL RETURN count(n)").result_set[0][0],
                    "check": gdb.ro("MATCH (n) RETURN n.community AS c, count(n) AS size ORDER BY size DESC LIMIT 5").result_set}
    out["person_pagerank"] = gdb.ro("MATCH (p:Person) RETURN p.name, p.pagerank, p.community ORDER BY p.pagerank DESC").result_set
    # --- PROFILE на реальному графі
    q1 = open(ROOT / "queries/c01_snp_low_qd.cypher").read(); q9 = open(ROOT / "queries/c09_impact_threshold.cypher").read()
    out["profile_real"] = {"c01": profile(q1), "c09": profile(q9)}
    # --- оптимізація на синтетичному графі
    N = int(sys.argv[1]) if len(sys.argv) > 1 else 20000
    bg = bench_graph(N)
    out["bench"] = {"variants": N, "nodes": bg.ro_query("MATCH (n) RETURN count(n)").result_set[0][0], "rels": bg.ro_query("MATCH ()-[r]->() RETURN count(r)").result_set[0][0]}
    gdb.GRAPH_BACKUP = gdb.GRAPH; gdb.GRAPH = "bench"
    out["bench"]["before"] = profile(Q_BEFORE); out["bench"]["rewrite"] = profile(Q_REWRITE)
    bg.create_node_range_index("Annotation", "name", "value")
    for _ in range(50):
        if all(r[7] == "OPERATIONAL" for r in bg.ro_query("CALL db.indexes()").result_set): break
        time.sleep(0.2)
    out["bench"]["rewrite_index"] = profile(Q_REWRITE); out["bench"]["before_index"] = profile(Q_BEFORE)
    a1 = bg.ro_query(Q_BEFORE).result_set; a2 = bg.ro_query(Q_REWRITE).result_set
    out["bench"]["answers_equal"] = a1 == a2; out["bench"]["answer"] = a1[0][0]
    gdb.GRAPH = gdb.GRAPH_BACKUP
    bg.delete()
    (ROOT / "docs/evidence/gds.json").write_text(json.dumps(out, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    print(json.dumps({k: out[k] for k in ("louvain",)}, ensure_ascii=False)[:1500]); print(out["pagerank"]["top10"], out["pagerank"]["overlap_top10"]); print({k: (v["ms_median"] if isinstance(v, dict) else v) for k, v in out["bench"].items()})


if __name__ == "__main__":
    main()
