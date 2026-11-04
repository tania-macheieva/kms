"""Спільна функція: HermiT-виведення для будь-якої онтології (моєї чи чернетки LLM) → граф виведених трипл­етів."""
import re
import subprocess
import tempfile
from pathlib import Path

import owlready2
from rdflib import Graph, URIRef
from rdflib.namespace import OWL, RDF, RDFS

HJ = Path(owlready2.__file__).parent / "hermit"
CP = f"{HJ}:{HJ}/HermiT.jar"


def run_hermit(g, args):
    d = tempfile.mkdtemp(); f = Path(d) / "m.owl"; g.serialize(f, format="xml")
    p = subprocess.run(["java", "-cp", CP, "org.semanticweb.HermiT.cli.CommandLine", *args, f"file://{f}"], capture_output=True, text=True)
    return p.returncode, "\n".join(l for l in (p.stdout + p.stderr).splitlines() if not l.startswith("Picked up JAVA_TOOL_OPTIONS"))


def infer(g):
    """Повертає (consistent, inferred_graph): виведені rdfs:subClassOf між іменованими класами та прямі типи індивідів."""
    rc, cls = run_hermit(g, ["-c"])
    if rc != 0:
        return False, Graph(), cls
    rc2, ind = run_hermit(g, ["-I"])
    inf = Graph()
    for a, b in re.findall(r"SubClassOf\( <([^>]+)> <([^>]+)> \)", cls): inf.add((URIRef(a), RDFS.subClassOf, URIRef(b)))
    for a, b in re.findall(r"EquivalentClasses\( <([^>]+)> <([^>]+)> \)", cls): inf.add((URIRef(a), OWL.equivalentClass, URIRef(b)))
    for a, b in re.findall(r"Type\( <([^>]+)> <([^>]+)> \)", ind): inf.add((URIRef(a), RDF.type, URIRef(b)))
    return True, inf, cls
