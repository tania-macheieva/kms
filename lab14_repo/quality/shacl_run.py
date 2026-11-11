"""RDF export of a store (graph CSVs + chunks + alternatives) and SHACL validation (pySHACL). CLI: python quality/shacl_run.py store_clean"""
import sys, csv, json, pathlib, collections
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from rdflib import Graph, Literal, Namespace, RDF, URIRef, XSD
from quality.common import ROOT, chunks, read_jsonl
DKH = Namespace("http://dkh.example/")
def lit(k, v):
    if k in ("ageYears", "minTestingAge") and v.strip().lstrip("-").isdigit(): return Literal(int(v), datatype=XSD.integer)
    if k in ("ageYears",) and v.strip(): return Literal(v)            # malformed age stays a plain string -> S01 datatype violation
    if k == "value":
        try: return Literal(float(v), datatype=XSD.double)
        except ValueError: return Literal(v)
    return Literal(v)
def to_rdf(sd):
    sd = pathlib.Path(sd); g = Graph(); key = {}
    for f in sorted((sd / "graph").glob("nodes_*.csv")):
        lab = f.stem.split("_", 1)[1]; rows = list(csv.DictReader(open(f))); k0 = list(rows[0])[0]
        for r in rows:
            n = DKH[f"{lab}/{r[k0]}"]; key[(r[k0])] = n; g.add((n, RDF.type, DKH[lab]))
            for k, v in r.items():
                if v not in ("", None): g.add((n, DKH[k], lit(k, v)))
    for f in sorted((sd / "graph").glob("rels_*.csv")):
        typ = f.stem.split("__")[0].replace("rels_", "")
        if typ == "DEFERRED_FOR": continue
        for r in csv.DictReader(open(f)):
            if r["from"] in key and r["to"] in key: g.add((key[r["from"]], DKH[typ], key[r["to"]]))
    for c in chunks(sd):
        n = DKH["Chunk/" + c["chunk_id"]]; g.add((n, RDF.type, DKH.Chunk))
        for k in ("doc_id", "title", "section", "text", "sensitivity", "lang", "date", "source_url"): g.add((n, DKH[k], Literal(c[k])))
    if (sd / "alternatives.jsonl").exists():
        for c in read_jsonl(sd / "alternatives.jsonl"):
            n = DKH["Claim/" + c["claim_id"]]; g.add((n, RDF.type, DKH.Claim))
            for k in ("status", "source", "decided_by", "validFrom", "validTo"):
                if c.get(k): g.add((n, DKH[k], Literal(c[k])))
    return g
def validate(sd):
    from pyshacl import validate as v
    g = to_rdf(sd); sh = Graph().parse(ROOT / "quality/shapes.ttl"); ok, rg, txt = v(g, shacl_graph=sh, inference="none", advanced=True)
    by = collections.Counter(); msgs = []
    from rdflib.namespace import SH
    for r in rg.subjects(RDF.type, SH.ValidationResult):
        m = str(rg.value(r, SH.resultMessage)); by[m.split(":")[0]] += 1; msgs.append((m, str(rg.value(r, SH.focusNode))))
    return ok, dict(by), msgs, len(g)
if __name__ == "__main__":
    ok, by, msgs, n = validate(ROOT / sys.argv[1]); print("triples", n, "conforms", ok, by); [print(" ", m) for m in msgs[:8]]
