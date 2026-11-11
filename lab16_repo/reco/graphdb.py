"""Item graph in FalkorDB(-lite): (Chunk)-[:IN_DOC]->(Doc), (Chunk)-[:NEXT]->(Chunk) (next section), (Chunk)-[:MENTIONS]->(Entity), (Entity)-[:SAME_AS]->(Gene|AnnotationType) of the Hub graph."""
from __future__ import annotations
import csv, tempfile, shutil, collections
from .data import HUB
class ItemGraph:
    def __init__(self, items, ent_of, idf, types, path=None):
        from redislite.falkordb_client import FalkorDB
        self._tmp = path or tempfile.mkdtemp(prefix="dkh16_"); self.db = FalkorDB(self._tmp + "/g.db"); self.g = self.db.select_graph("reco"); self.items = items; self.pos = {it["id"]: i for i, it in enumerate(items)}
        g = self.g; g.query("CREATE INDEX FOR (c:Chunk) ON (c.id)"); g.query("CREATE INDEX FOR (e:Entity) ON (e.name)"); g.query("CREATE INDEX FOR (d:Doc) ON (d.id)")
        docs = collections.OrderedDict()
        rows = [dict(id=it["id"], doc=it["doc"], sens=it["sensitivity"], ver=it["verified"], date=it["date"], title=it["title"], sec=it["section"]) for it in items]
        g.query("UNWIND $r AS r CREATE (c:Chunk {id: r.id, doc: r.doc, sensitivity: r.sens, verified: r.ver, date: r.date, title: r.title, section: r.sec})", {"r": rows})
        g.query("UNWIND $r AS r MERGE (d:Doc {id: r.doc})", {"r": rows}); g.query("MATCH (c:Chunk), (d:Doc {id: c.doc}) CREATE (c)-[:IN_DOC]->(d)")
        byd = collections.defaultdict(list)
        for it in items: byd[it["doc"]].append(it["id"])
        nxt = [dict(a=a, b=b) for ids in byd.values() for a, b in zip(sorted(ids), sorted(ids)[1:])]
        if nxt: g.query("UNWIND $r AS r MATCH (a:Chunk {id: r.a}), (b:Chunk {id: r.b}) CREATE (a)-[:NEXT]->(b)", {"r": nxt})
        ents = [dict(name=n, type=types[n], idf=idf[n]) for n in idf]; g.query("UNWIND $r AS r CREATE (:Entity {name: r.name, type: r.type, idf: r.idf})", {"r": ents})
        men = [dict(c=items[i]["id"], e=n) for i, e in enumerate(ent_of) for n in e]; g.query("UNWIND $r AS r MATCH (c:Chunk {id: r.c}), (e:Entity {name: r.e}) CREATE (c)-[:MENTIONS]->(e)", {"r": men})
        for lab, f, key in (("Gene", "nodes_Gene.csv", "symbol"), ("AnnotationType", "nodes_AnnotationType.csv", "name")):     # link to the Hub knowledge graph (labs 9/14)
            names = [r[key] for r in csv.DictReader(open(HUB / "graph" / f, encoding="utf-8"))]
            g.query(f"UNWIND $n AS n CREATE (:{lab} {{{key}: n}})", {"n": names}); g.query(f"MATCH (e:Entity), (h:{lab} {{{key}: e.name}}) CREATE (e)-[:SAME_AS]->(h)")
    def q(self, cypher, **params): return self.g.ro_query(cypher, params).result_set
    def stats(self):
        return dict(chunks=self.q("MATCH (c:Chunk) RETURN count(c)")[0][0], entities=self.q("MATCH (e:Entity) RETURN count(e)")[0][0], mentions=self.q("MATCH ()-[r:MENTIONS]->() RETURN count(r)")[0][0], next=self.q("MATCH ()-[r:NEXT]->() RETURN count(r)")[0][0], same_as=self.q("MATCH ()-[r:SAME_AS]->() RETURN count(r)")[0][0])
    def add_item(self, it, ents, idf, types):
        """cold-start for a new document: insert node + edges without any interaction"""
        g = self.g; g.query("CREATE (:Chunk {id: $id, doc: $doc, sensitivity: $s, verified: $v, date: $d, title: $t, section: $sec})", dict(id=it["id"], doc=it["doc"], s=it["sensitivity"], v=it["verified"], d=it["date"], t=it["title"], sec=it["section"]))
        g.query("MERGE (d:Doc {id: $doc})", dict(doc=it["doc"])); g.query("MATCH (c:Chunk {id: $id}), (d:Doc {id: $doc}) CREATE (c)-[:IN_DOC]->(d)", dict(id=it["id"], doc=it["doc"]))
        ids = sorted(r[0] for r in self.q("MATCH (c:Chunk {doc: $doc}) RETURN c.id", doc=it["doc"]))      # NEXT edges to the neighbours (by section order) already in the graph
        k = ids.index(it["id"]); 
        if k > 0: g.query("MATCH (a:Chunk {id: $a}), (b:Chunk {id: $b}) CREATE (a)-[:NEXT]->(b)", dict(a=ids[k - 1], b=it["id"]))
        if k + 1 < len(ids): g.query("MATCH (a:Chunk {id: $a}), (b:Chunk {id: $b}) CREATE (a)-[:NEXT]->(b)", dict(a=it["id"], b=ids[k + 1]))
        for n in ents:
            if n not in idf: continue
            g.query("MATCH (c:Chunk {id: $id}), (e:Entity {name: $n}) CREATE (c)-[:MENTIONS]->(e)", dict(id=it["id"], n=n))
    def close(self): shutil.rmtree(self._tmp, ignore_errors=True)
