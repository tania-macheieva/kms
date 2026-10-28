"""Діаграма ієрархії класів (Graphviz) → docs/class_hierarchy.png/.svg"""
import csv
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
rows = list(csv.DictReader(open(ROOT / "models/class_table.csv", encoding="utf-8-sig")))
COL = {"BiologicalEntity": "#DCE6F5", "GeneticVariant": "#DCE6F5", "QualityMeasure": "#E3F1E0", "FilterThreshold": "#E3F1E0", "Procedure": "#FFF2CC", "DataArtifact": "#EADCF5",
       "Person": "#FBE9D0", "Disease": "#FBE9D0", "ClinicalSignificance": "#FBE9D0", "Event": "#EEEEEE", "State": "#EEEEEE", "Action": "#EEEEEE", "Sensor": "#EEEEEE", "SituationTemplate": "#EEEEEE"}
by = {r["id"]: r for r in rows}
def top(i):
    while by[i]["parent"] in by: i = by[i]["parent"]
    return i
L = ["digraph H {", "rankdir=LR; nodesep=0.12; ranksep=0.5; node [shape=box, style=\"rounded,filled\", fontname=\"DejaVu Sans\", fontsize=10, height=0.28];", "edge [arrowhead=empty, color=\"#555555\"];"]
for r in rows:
    d = r["class_kind"].startswith("defined")
    L.append(f'"{r["id"]}" [label="{r["label_en"]}", fillcolor="{COL[top(r["id"])]}"' + (', penwidth=2.2, color="#C0392B"' if d else "") + "];")
    if r["parent"] in by: L.append(f'"{r["id"]}" -> "{r["parent"]}";')
L.append("}")
(ROOT / "docs/class_hierarchy.dot").write_text("\n".join(L), encoding="utf-8")
for fmt in ("png", "svg"): subprocess.run(["dot", f"-T{fmt}", "-Gdpi=130" if fmt == "png" else "-Gdpi=96", str(ROOT / "docs/class_hierarchy.dot"), "-o", str(ROOT / f"docs/class_hierarchy.{fmt}")], check=True)
print("ok")
