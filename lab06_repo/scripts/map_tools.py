"""Спільні інструменти для концептуальних карт: завантаження, візуалізація (Graphviz → PNG), експорт у draw.io.

Формат карти (JSON): {"title", "concepts":[{id,label,kind(concept|instance),cluster,type,definition}],
                      "propositions":[{id,s,p,o,cross(bool),explanation}]}, де s/o — id понять, p — id відношення з data/relations.json.
"""
import csv
import json
import os
import shutil
import subprocess
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent.parent
REL = {r["id"]: r for r in json.loads((ROOT / "data/relations.json").read_text(encoding="utf-8"))["relations"]}
CLUSTER_COLOR = {"G": "#DCE6F5", "Q": "#E3F1E0", "C": "#FBE9D0", "X": "#EEEEEE"}
CLUSTER_NAME = {"G": "Геноміка й дані", "Q": "Контроль якості варіантів", "C": "Клінічне тестування", "X": "Інше"}


def dot_executable():
    dot = shutil.which("dot")
    if dot is not None:
        return dot

    if os.name == "nt":
        for root in (os.environ.get("ProgramFiles"), os.environ.get("ProgramFiles(x86)")):
            if root:
                candidate = Path(root) / "Graphviz" / "bin" / "dot.exe"
                if candidate.is_file():
                    return str(candidate)

    raise FileNotFoundError(
        "Graphviz 'dot' was not found. Install Graphviz and add its bin directory to PATH, "
        "or run this script from a terminal where `dot -V` works."
    )


def taxonomy_info():
    rows = list(csv.DictReader(open(ROOT / "models/taxonomy_final_lab5.csv", encoding="utf-8-sig")))
    by = {r["id"]: r for r in rows}

    def l1(r):
        while r["level"] != "1":
            r = by[r["parent"]]
        return r["label"]
    return {r["label"]: {"definition": r["definition"], "type": l1(r), "term_id": r["term_id"]} for r in rows if r["term_id"]}


def load_map(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _dot(m, title=None):
    lines = ['digraph M {', 'rankdir=TB; nodesep=0.35; ranksep=0.7; compound=true; newrank=true;',
             'node [fontname="Helvetica", fontsize=12, shape=box, style="rounded,filled", margin="0.12,0.06"];',
             'edge [fontname="Helvetica", fontsize=10, color="#555555"];']
    if title:
        lines.append(f'labelloc=t; fontsize=18; fontname="Helvetica-Bold"; label="{title}";')
    clusters = {}
    for c in m["concepts"]:
        clusters.setdefault(c.get("cluster", "X"), []).append(c)
    for k, cs in clusters.items():
        lines.append(f'subgraph cluster_{k} {{ label="{CLUSTER_NAME.get(k, k)}"; style="rounded,dashed"; color="#999999"; fontname="Helvetica"; fontsize=12;')
        for c in cs:
            if c["kind"] == "instance":
                lines.append(f'{c["id"]} [label="{c["label"]}", shape=ellipse, fillcolor="#FFF3BF", fontsize=11];')
            else:
                lines.append(f'{c["id"]} [label="{c["label"]}", fillcolor="{CLUSTER_COLOR.get(k, "#EEEEEE")}"];')
        lines.append("}")
    for p in m["propositions"]:
        lab = REL[p["p"]]["label_uk"]
        if p.get("cross"):
            lines.append(f'{p["s"]} -> {p["o"]} [label="{lab}", color="#C0392B", fontcolor="#C0392B", penwidth=2.2, style=dashed];')
        else:
            lines.append(f'{p["s"]} -> {p["o"]} [label="{lab}"];')
    lines.append("}")
    return "\n".join(lines)


def render_png(m, out, title=None, dpi=110):
    out = Path(out)
    dot = _dot(m, title)
    out.with_suffix(".dot").write_text(dot, encoding="utf-8")
    subprocess.run([dot_executable(), "-Tpng", f"-Gdpi={dpi}", str(out.with_suffix(".dot")), "-o", str(out)], check=True)
    return out


def to_drawio(m, out, title=None):
    dot = _dot(m, title)
    js = json.loads(subprocess.run([dot_executable(), "-Tjson"], input=dot, capture_output=True, text=True, encoding="utf-8", check=True).stdout)
    H = float(js["bb"].split(",")[3])
    pos = {}
    for o in js.get("objects", []):
        if "pos" in o and not o["name"].startswith("cluster"):
            x, y = map(float, o["pos"].split(","))
            pos[o["name"]] = (x, H - y, float(o["width"]) * 72, float(o["height"]) * 72)
    sc = 1.15
    cells = ['<mxCell id="0"/>', '<mxCell id="1" parent="0"/>']
    for c in m["concepts"]:
        x, y, w, h = pos[c["id"]]
        w, h = max(w * sc, 90), max(h * sc, 36)
        fill = "#FFF3BF" if c["kind"] == "instance" else CLUSTER_COLOR.get(c.get("cluster", "X"), "#EEEEEE")
        style = ("ellipse;" if c["kind"] == "instance" else "rounded=1;") + f"whiteSpace=wrap;html=1;fillColor={fill};strokeColor=#555555;fontSize=12;"
        cells.append(f'<mxCell id="n_{c["id"]}" value="{escape(c["label"])}" style="{style}" vertex="1" parent="1">'
                     f'<mxGeometry x="{x * sc - w / 2:.0f}" y="{y * sc - h / 2:.0f}" width="{w:.0f}" height="{h:.0f}" as="geometry"/></mxCell>')
    for p in m["propositions"]:
        col = "#C0392B" if p.get("cross") else "#555555"
        extra = "dashed=1;strokeWidth=2;" if p.get("cross") else ""
        st = f"endArrow=classic;html=1;strokeColor={col};fontColor={col};fontSize=10;labelBackgroundColor=#FFFFFF;{extra}"
        cells.append(f'<mxCell id="e_{p["id"]}" value="{escape(REL[p["p"]]["label_uk"])}" style="{st}" edge="1" parent="1" source="n_{p["s"]}" target="n_{p["o"]}">'
                     f'<mxGeometry relative="1" as="geometry"/></mxCell>')
    xml = ('<mxfile host="app.diagrams.net"><diagram name="' + escape(title or m.get("title", "map")) +
           '"><mxGraphModel dx="1400" dy="900" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1654" pageHeight="1169" math="0" shadow="0"><root>' +
           "".join(cells) + "</root></mxGraphModel></diagram></mxfile>")
    Path(out).write_text(xml, encoding="utf-8")


def stats(m):
    from collections import Counter
    props = m["propositions"]
    c = Counter(p["p"] for p in props)
    return {"concepts": sum(1 for x in m["concepts"] if x["kind"] == "concept"),
            "instances": sum(1 for x in m["concepts"] if x["kind"] == "instance"),
            "propositions": len(props), "cross_links": sum(1 for p in props if p.get("cross")),
            "relation_counts": dict(c), "related_to_share": c.get("related_to", 0) / max(1, len(props))}
