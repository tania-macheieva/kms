"""Рисунки: ієрархія класів (docs/class_hierarchy_*.png) і родинне дерево з виведеними ступенями (docs/family_inferred.png). Потрібен Graphviz."""
import csv
import subprocess
import sys
from pathlib import Path

from rdflib import Graph
from rdflib.namespace import RDF

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
rows = list(csv.DictReader(open(ROOT / "models/class_table.csv", encoding="utf-8-sig")))
COL = {"primitive (⊑)": "#DCE6F5", "defined (≡)": "#FBE9D0"}
tops = [r for r in rows if r["parent"] == "owl:Thing"]
groups = [tops[:5], tops[5:10], tops[10:]]
def kids(i): return [r for r in rows if r["parent"] == i]
def draw(top_rows, out):
    L = ['digraph G { rankdir=LR; node [shape=box, style="rounded,filled", fontname="DejaVu Sans", fontsize=11]; edge [arrowhead=empty, color="#555555"];']
    def add(r):
        L.append(f'"{r["id"]}" [label="{r["id"]}", fillcolor="{COL[r["class_kind"]]}"];')
        for k in kids(r["id"]):
            L.append(f'"{k["id"]}" -> "{r["id"]}";'); add(k)
    for t in top_rows: add(t)
    L.append("}")
    p = subprocess.run(["dot", "-Tpng", "-Gdpi=110", "-o", str(out)], input="\n".join(L), text=True, capture_output=True)
    assert p.returncode == 0, p.stderr
for i, g in enumerate(groups, 1): draw(g, ROOT / f"docs/class_hierarchy_{i}.png")
# родина
d = Graph().parse(ROOT / "models/onto_data.ttl", format="turtle"); inf = Graph().parse(ROOT / "models/onto_inferred.ttl", format="turtle")
D = "http://example.org/dkh/onto#"
degs = {}
for s, o in inf.subject_objects(RDF.type):
    n = str(o).split("#")[-1]
    if n in ("FirstDegreeRelative", "SecondDegreeRelative", "ThirdDegreeRelative", "MinorRelative"): degs.setdefault(str(s).split("#")[-1], []).append("minor" if n == "MinorRelative" else n.replace("DegreeRelative", ""))
colors = {"First": "#C6E0B4", "Second": "#FFE699", "Third": "#F8CBAD"}
L = ['digraph F { rankdir=TB; node [shape=box, style="rounded,filled", fontname="DejaVu Sans", fontsize=11, fillcolor="#EEEEEE"]; edge [color="#555555"];']
for p in ["Olena", "Marta", "Iryna", "Petro", "Sofiia", "Halyna", "Andrii", "Maria"]:
    ds = degs.get(p, []); col = next((colors[x] for x in ds if x in colors), "#BDD7EE" if p == "Olena" else "#EEEEEE")
    lab = p + ("\\n(proband)" if p == "Olena" else "") + ("\\n" + ", ".join(x.lower() + "-degree" if x in colors else x for x in ds) if ds else "")
    L.append(f'"{p}" [label="{lab}", fillcolor="{col}"];')
for a, b in (("Maria", "Iryna"), ("Maria", "Halyna"), ("Iryna", "Olena"), ("Petro", "Olena"), ("Iryna", "Marta"), ("Petro", "Marta"), ("Olena", "Sofiia"), ("Halyna", "Andrii")): L.append(f'"{a}" -> "{b}";')
L.append('"Marta" -> "Olena" [dir=both, style=dashed, constraint=false, label="sibling"]; "Iryna" -> "Halyna" [dir=both, style=dashed, constraint=false, label="sibling"];}')
subprocess.run(["dot", "-Tpng", "-Gdpi=110", "-o", str(ROOT / "docs/family_inferred.png")], input="\n".join(L), text=True, check=True)
print("ok")
