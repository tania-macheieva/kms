"""Візуалізація підсумкової таксономії (Graphviz): docs/taxonomy_final.dot / .png / .svg."""
import csv
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
rows = list(csv.DictReader(open(ROOT / "models/taxonomy_final.csv", encoding="utf-8-sig")))
COL = ["#DCE6F5", "#E3F1E0", "#FBE9D0", "#F2DDF0", "#E8E8E8", "#FADADD", "#DDF1F3", "#FFF3BF", "#E5DFF7"]
top = [r["id"] for r in rows if r["parent"] == rows[0]["id"]]
top_color = {t: COL[i % len(COL)] for i, t in enumerate(top)}
by_id = {r["id"]: r for r in rows}


def top_of(r):
    while r["parent"] and r["parent"] != rows[0]["id"]:
        r = by_id[r["parent"]]
    return r["id"]


out = ['digraph T {', 'rankdir=LR; nodesep=0.08; ranksep=0.45; splines=polyline;',
       'node [fontname="Helvetica", fontsize=11, shape=box, style="rounded,filled", margin="0.08,0.03"];']
for r in rows:
    fill = "#FFFFFF" if not r["parent"] else top_color[top_of(r)] if r["id"] not in top_color else top_color[r["id"]]
    shape = "box" if not r["term_id"] else "box"
    label = r["label"].replace('"', "'")
    pw = "2.2" if r["term_id"] == "" else "0.6"
    style = 'rounded,filled,bold' if not r["term_id"] else 'rounded,filled'
    out.append(f'{r["id"]} [label="{label}", fillcolor="{fill}", style="{style}", penwidth={pw if r["term_id"]=="" else 0.6}];')
    if r["parent"]:
        out.append(f'{r["parent"]} -> {r["id"]} [arrowhead=none, color="#888888"];')
out.append("}")
dot = ROOT / "docs/taxonomy_final.dot"
dot.write_text("\n".join(out), encoding="utf-8")
for fmt in ("png", "svg"):
    subprocess.run(["dot", f"-T{fmt}", "-Gdpi=110", str(dot), "-o", str(ROOT / f"docs/taxonomy_final.{fmt}")], check=True)
print("готово")
