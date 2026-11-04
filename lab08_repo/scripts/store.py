"""Спільні функції для роботи з триплстором pyoxigraph (локальний персистентний store/)."""
from pathlib import Path

import pyoxigraph as ox

ROOT = Path(__file__).resolve().parents[1]
PREFIXES = {"dkh": "http://example.org/dkh/onto#", "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#", "rdfs": "http://www.w3.org/2000/01/rdf-schema#", "owl": "http://www.w3.org/2002/07/owl#",
            "xsd": "http://www.w3.org/2001/XMLSchema#", "skos": "http://www.w3.org/2004/02/skos/core#", "sh": "http://www.w3.org/ns/shacl#", "wd": "http://www.wikidata.org/entity/", "wdt": "http://www.wikidata.org/prop/direct/"}
GRAPHS = {"tbox": "data/graphs/tbox.ttl", "abox": "data/graphs/abox.ttl", "inferred": "data/graphs/inferred.ttl", "links": "data/links.ttl"}
G = lambda name: ox.NamedNode(f"urn:dkh:graph:{name}")


def prefix_header():
    return "".join(f"PREFIX {k}: <{v}>\n" for k, v in PREFIXES.items())


def open_store(path=None, fresh=False):
    p = Path(path or ROOT / "store")
    if fresh and p.exists():
        import shutil; shutil.rmtree(p)
    return ox.Store(str(p))


def load_graphs(store):
    counts = {}
    for name, rel in GRAPHS.items():
        f = ROOT / rel
        if not f.exists(): continue
        store.load(path=str(f), format=ox.RdfFormat.TURTLE, to_graph=G(name))
    return counts


def query(store, text, with_prefixes=True):
    q = (prefix_header() if with_prefixes else "") + text
    return store.query(q, use_default_graph_as_union=True)
