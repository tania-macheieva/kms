"""Entity linking of a question to graph nodes and extraction of a limited, role-filtered sub-graph, linearised with node IDs.

Graph: FalkorDB (falkordblite) built from graph_kb/ (lab 9). ID format used for citations: [G:<Label>:<key>].
Access: nodes of labels with sensitivity above the caller's role are never read into the context (and their existence is not revealed).
"""
from __future__ import annotations
import re, sys, time
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "graph_kb" / "scripts"))
import graphdb as gdb  # noqa: E402

KEY = {"Variant": "id", "Gene": "symbol", "Person": "name", "Annotation": "id", "Sample": "code", "Threshold": "id", "AnnotationType": "name", "GenePanel": "name",
       "Diagnosis": "id", "Procedure": "id", "DataFile": "id", "Instrument": "id", "Situation": "id", "Concept": "name"}
SENS = {"Person": "restricted", "Diagnosis": "restricted", "Variant": "internal", "Annotation": "internal", "Sample": "internal"}   # default: public
HUB_TYPES = {"HAS_ANNOTATION", "FROM_SAMPLE", "OF_TYPE", "INSTANCE_OF", "GENERATED_BY"}   # high fan-out relations, followed only at hop 1
RANK = {"public": 0, "internal": 1, "restricted": 2}
ROLE_MAX = {"reader": 0, "analyst": 1, "clinician": 2}
EXTRA_ALIASES = {  # hand-written synonyms (EN + UA); Cyrillic names are matched by stem
    ("Procedure", "HF-01"): ["hard filtering", "hard-filtering", "hard filters", "жорстка фільтрація", "жорсткої фільтрації", "жорстку фільтрацію"],
    ("Procedure", "CT-01"): ["cascade testing", "cascade test", "каскадне тестування", "каскадного тестування"],
    ("GenePanel", "HBOC-panel"): ["HBOC", "HBOC panel", "gene panel", "панель HBOC", "панелі HBOC"],
    ("DataFile", "sample1_bam"): ["sample1.bam", "sample1 bam"], ("DataFile", "sample1_vcf"): ["sample1.vcf", "sample1 vcf"],
    ("Diagnosis", "Iryna_OC"): ["ovarian cancer", "рак яєчників"], ("Diagnosis", "Olena_BC"): ["breast cancer", "рак молочної залози"],
    ("Instrument", "Sequencer1"): ["sequencer", "секвенатор"],
}
CYR = {"Olena": "Олен", "Iryna": "Ірин", "Petro": "Петр", "Marta": "Март", "Sofiia": "Софі", "Halyna": "Галин", "Andrii": "Андр", "Maria": "Марі"}
WB = r"(?<![A-Za-z0-9_Ѐ-ӿ]){}(?![A-Za-z0-9_])"


def nid(label, key): return f"G:{label}:{key}"


@dataclass
class GraphContext:
    text: str = ""
    seeds: list = field(default_factory=list)       # [(label, key, alias)]
    node_ids: set = field(default_factory=set)
    n_nodes: int = 0
    n_edges: int = 0
    truncated: int = 0
    denied: int = 0                                  # linked entities hidden from this role
    ms: float = 0.0


class GraphIndex:
    def __init__(self, graph=None):
        self.g = graph or gdb.graph(); self.alias = []   # (regex, label, key, alias)
        for label, key in KEY.items():
            for (props,) in self.g.ro_query(f"MATCH (n:{label}) RETURN properties(n)").result_set:
                k = str(props[key]); al = {k}
                if label == "Concept": al |= {re.sub(r"(?<=[a-z])(?=[A-Z])", " ", k), re.sub(r"(?<=[a-z])(?=[A-Z])", "-", k)}
                if label == "Person" and k in CYR: al.add(CYR[k] + r"[Ѐ-ӿа-яіїєґ]*")
                if label == "Diagnosis": al.add(props.get("kind", ""))
                if label == "DataFile": al.add(props.get("label", ""))
                if label == "Situation": al.add(str(props.get("name", "")).split(" ")[0])
                al |= set(EXTRA_ALIASES.get((label, k), []))
                for a in {x for x in al if x}:
                    pat = a if (label == "Person" and a.endswith("*")) or "[Ѐ" in a else re.escape(a)
                    self.alias.append((re.compile(WB.format(pat), re.I), label, k, a))
        self.alias.sort(key=lambda x: -len(x[3]))

    def link(self, question: str):
        """Longest-match entity linking; returns [(label, key, alias, start)] without overlapping spans."""
        taken, out = [], []
        for rx, label, key, a in self.alias:
            for m in rx.finditer(question):
                if all(m.end() <= s or m.start() >= e for s, e in taken):
                    taken.append((m.start(), m.end())); out.append((label, key, m.group(0), m.start()))
        out.sort(key=lambda x: x[3]); seen, res = set(), []
        for l, k, a, s in out:
            if (l, k) not in seen: seen.add((l, k)); res.append((l, k, a, s))
        return res


def _fmt_props(label, props):
    skip = {KEY[label]}; items = [f"{k}={v}" for k, v in props.items() if k not in skip and v not in (None, "") and k not in ("pagerank", "community")]
    return f"{label}(" + ", ".join(items) + ")" if items else label


class GraphContextBuilder:
    def __init__(self, index: GraphIndex | None = None, max_seeds=3, hops=2, max_nodes=24, max_edges=40, fanout=6):
        self.ix = index or GraphIndex(); self.g = self.ix.g
        self.max_seeds, self.hops, self.max_nodes, self.max_edges, self.fanout = max_seeds, hops, max_nodes, max_edges, fanout

    def _neighbors(self, label, key, direction):
        pat = f"(n:{label} {{{KEY[label]}: $k}})-[r]->(m)" if direction == "out" else f"(n:{label} {{{KEY[label]}: $k}})<-[r]-(m)"
        q = f"MATCH {pat} RETURN type(r), labels(m)[0], properties(m), properties(r) ORDER BY type(r), labels(m)[0]"
        return self.g.ro_query(q, {"k": key}).result_set

    def build(self, question: str, role: str = "reader") -> GraphContext:
        t0 = time.perf_counter(); cap = ROLE_MAX[role]; ctx = GraphContext()
        allowed = lambda label: RANK[SENS.get(label, "public")] <= cap
        links = self.ix.link(question); seeds = []
        for l, k, a, _ in links:
            if allowed(l): seeds.append((l, k, a))
            else: ctx.denied += 1
        seeds = seeds[: self.max_seeds]; ctx.seeds = seeds
        nodes, edges, trunc = {}, [], 0
        def props_of(label, key):
            r = self.g.ro_query(f"MATCH (n:{label} {{{KEY[label]}: $k}}) RETURN properties(n)", {"k": key}).result_set
            return r[0][0] if r else {}
        frontier = []
        for l, k, _ in seeds:
            if (l, k) not in nodes: nodes[(l, k)] = props_of(l, k); frontier.append((l, k))
        for hop in range(self.hops):
            nxt = []
            for (l, k) in frontier:
                for direction in ("out", "in"):
                    rows = self._neighbors(l, k, direction); per = {}
                    for rtype, ml, mprops, rprops in rows:
                        if not allowed(ml): continue
                        if hop >= 1 and (rtype in HUB_TYPES or (rtype == "LOCATED_IN" and direction == "in")): continue   # 2nd hop: do not fan out through hubs
                        per[rtype] = per.get(rtype, 0) + 1
                        if per[rtype] > self.fanout: trunc += 1; continue
                        mk = str(mprops[KEY[ml]])
                        if (ml, mk) not in nodes:
                            if len(nodes) >= self.max_nodes: trunc += 1; continue
                            nodes[(ml, mk)] = mprops; nxt.append((ml, mk))
                        if len(edges) >= self.max_edges: trunc += 1; continue
                        e = ((l, k, rtype, ml, mk) if direction == "out" else (ml, mk, rtype, l, k))
                        if e not in [x[0] for x in edges]: edges.append((e, rprops))
            frontier = nxt
        # linearise: one block per node, then its outgoing relations (with provenance)
        lines = []
        for (l, k), p in nodes.items():
            lines.append(f"[{nid(l, k)}] {_fmt_props(l, {**{KEY[l]: k}, **p})}")
            for (a, b, rt, c, d), rp in edges:
                if (a, b) == (l, k) and (c, d) in nodes:
                    prov = ", ".join(f"{x}={rp[x]}" for x in ("source", "confidence", "validFrom") if rp.get(x) is not None)
                    lines.append(f"    -{rt}-> [{nid(c, d)}] ({prov})")
        if trunc: lines.append(f"(sub-graph truncated: {trunc} more neighbours omitted by limits fanout={self.fanout}, max_nodes={self.max_nodes}, max_edges={self.max_edges})")
        ctx.text = "\n".join(lines); ctx.node_ids = {nid(l, k) for (l, k) in nodes}; ctx.n_nodes = len(nodes); ctx.n_edges = len(edges); ctx.truncated = trunc
        ctx.ms = (time.perf_counter() - t0) * 1000
        return ctx
