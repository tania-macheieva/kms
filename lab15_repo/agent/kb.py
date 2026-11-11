"""Knowledge base handles: embedded FalkorDB graph built from hub/graph/*.csv, DuckDB (read-only view over hub/warehouse/*.parquet), claim register, lab-11 RAG."""
from __future__ import annotations
import csv, json, os, re, shutil, sys, tempfile, pathlib, hashlib
from .config import ROOT
HUB = ROOT / "hub"
def _coerce(v: str):
    if v == "": return None
    if v in ("True", "true"): return True
    if v in ("False", "false"): return False
    try: return int(v)
    except ValueError:
        try: return float(v)
        except ValueError: return v
class KB:
    def __init__(self, lab11: str | None = None):
        self.lab11 = pathlib.Path(lab11 or os.environ.get("LAB11_REPO", ROOT.parent / "lab11_repo")).resolve()
        self._g = self._tmp = self._con = self._rag = None; self.keys = {}
        self._cache_f = ROOT / "logs" / "search_cache.json"; self._scache = json.loads(self._cache_f.read_text(encoding="utf-8")) if self._cache_f.exists() else {}
    # ---- graph ----
    def build_graph(self):
        from redislite.falkordb_client import FalkorDB
        if self._tmp: shutil.rmtree(self._tmp, ignore_errors=True)
        self._tmp = tempfile.mkdtemp(prefix="dkh15_"); db = FalkorDB(self._tmp + "/g.db"); g = db.select_graph("hub")
        for f in sorted((HUB / "graph").glob("nodes_*.csv")):
            label = f.stem.split("_", 1)[1]
            with open(f, encoding="utf-8", newline="") as fh:
                rd = csv.DictReader(fh); key = rd.fieldnames[0]; self.keys[label] = key
                for r in rd: g.query(f"MERGE (n:{label} {{{key}: $k}}) SET n += $p", {"k": _coerce(r[key]), "p": {c: _coerce(v) for c, v in r.items() if c != key and v != ""}})
        for f in sorted((HUB / "graph").glob("rels_*.csv")):
            typ, ends = f.stem.split("_", 1)[1].split("__"); a, b = ends.split("_")
            with open(f, encoding="utf-8", newline="") as fh:
                for r in csv.DictReader(fh):
                    g.query(f"MATCH (x:{a} {{{self.keys[a]}: $f}}), (y:{b} {{{self.keys[b]}: $t}}) CREATE (x)-[r:{typ}]->(y) SET r += $p", {"f": _coerce(r["from"]), "t": _coerce(r["to"]), "p": {c: _coerce(v) for c, v in r.items() if c not in ("from", "to") and v != ""}})
        self._g = g; return g
    @property
    def graph(self): return self._g or self.build_graph()
    def reset_graph(self): self._g = None; return self.graph
    def schema(self) -> str:
        g = self.graph; lab = [r[0] for r in g.ro_query("MATCH (n) RETURN DISTINCT labels(n)[0] ORDER BY 1").result_set]
        out = []
        for l in lab:
            props = sorted({k for r in g.ro_query(f"MATCH (n:{l}) RETURN keys(n) LIMIT 20").result_set for k in r[0]}); out.append(f"({l} {{{', '.join(props)}}})")
        rels = sorted({f.stem.split("_", 1)[1].replace("__", " ").replace("_", "->", 1) if False else f.stem.split("_", 1)[1] for f in (HUB / "graph").glob("rels_*.csv")})
        rt = []
        for x in rels:
            t, e = x.split("__"); a, b = e.split("_"); rt.append(f"(:{a})-[:{t}]->(:{b})")
        return "NODES: " + "; ".join(out) + "\nRELATIONSHIPS: " + "; ".join(rt)
    def restricted_values(self) -> dict:
        """values that identify restricted data (person names, diagnosis ids) -> used by the output guard."""
        vals = {}
        for lab in ("Person", "Diagnosis"):
            f = HUB / "graph" / f"nodes_{lab}.csv"
            for r in csv.DictReader(open(f, encoding="utf-8")): vals[r[list(r)[0]]] = lab
        return vals
    # ---- warehouse ----
    @property
    def con(self):
        if self._con is None:
            import duckdb; c = duckdb.connect(":memory:")
            for f in sorted((HUB / "warehouse").glob("*.parquet")): c.execute(f"CREATE VIEW {f.stem} AS SELECT * FROM read_parquet('{f.as_posix()}')")
            self._con = c
        return self._con
    # ---- claims ----
    def claims(self):
        return [json.loads(l) for l in open(HUB / "alternatives.jsonl", encoding="utf-8") if l.strip()]
    # ---- docs (lab-11 RAG retriever) ----
    @property
    def rag(self):
        if self._rag is None:
            sys.path.insert(0, str(self.lab11)); cwd = os.getcwd(); os.chdir(self.lab11)
            try:
                from src.rag import RAG; self._rag = RAG(None, graph=None, log=False)
            finally: os.chdir(cwd)
        return self._rag
    def search(self, query: str, role: str, k: int):
        ck = hashlib.sha1(f"{query}|{role}|{k}".encode()).hexdigest()
        if ck in self._scache: return self._scache[ck]
        rag = self.rag; from src.rag import Config
        cwd = os.getcwd(); os.chdir(self.lab11)
        try: hits, ms = rag.retrieve(query, role, Config(name="A", rerank=True, k=k))
        finally: os.chdir(cwd)
        out = []
        for row, sc in hits:
            c = self.rag.ret.chunks[row]; m = self.rag.ret.metas[row]; out.append(dict(id=c.id, doc_id=c.doc_id, sensitivity=m["sensitivity"], score=round(float(sc), 4), text=c.text))
        self._scache[ck] = out; self._cache_f.parent.mkdir(exist_ok=True); self._cache_f.write_text(json.dumps(self._scache, ensure_ascii=False), encoding="utf-8"); return out
