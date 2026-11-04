"""Візуалізація графа триплетів LLM → models/cmap_llm.png (Graphviz). Вузли пофарбовано за типом ЛР5; помилкові ребра — червоні пунктирні."""
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from map_tools import REL, ROOT, dot_executable                      # noqa: E402

COL = {"Biological entity": "#DCE6F5", "Genetic variation": "#E3F1E0", "Method and procedure": "#FBE9D0", "Data and artifact": "#E8E8E8",
       "Measure of quality": "#DDF1F3", "Clinical concept": "#FADADD", "Knowledge and information technology": "#E5DFF7",
       "Biological property": "#F2DDF0", "Research field": "#FFF3BF"}


def main(src=ROOT / "models/triples_llm.jsonl", out=ROOT / "models/cmap_llm.png"):
    triples = [json.loads(l) for l in Path(src).read_text(encoding="utf-8").splitlines() if l.strip()]
    review = {r["id"] for r in json.loads((ROOT / "data/triples_manual_review.json").read_text(encoding="utf-8"))["reviewed"]} if (ROOT / "data/triples_manual_review.json").exists() else set()
    ids, lines = {}, ['digraph L {', 'rankdir=LR; nodesep=0.25; ranksep=1.0;', 'label="Граф триплетів LLM (червоні пунктирні — помилки перевірки; помаранчеві — ручний перегляд)"; labelloc=t; fontsize=16; fontname="Helvetica-Bold";',
                      'node [fontname="Helvetica", fontsize=11, shape=box, style="rounded,filled", margin="0.1,0.05"]; edge [fontname="Helvetica", fontsize=9, color="#666666"];']
    def nid(label, ty):
        if label not in ids:
            ids[label] = f"n{len(ids)}"
            shape = "box" if ty else "ellipse"
            fill = COL.get(ty, "#FFF3BF")
            lines.append(f'{ids[label]} [label="{label}", shape={shape}, fillcolor="{fill}"];')
        return ids[label]
    for t in triples:
        a, b = nid(t["s"], t["s_type"]), nid(t["o"], t["o_type"])
        bad = bool(t["checks"])
        manual = t["id"] in review
        attr = f'label="{REL[t["p"]]["label_uk"]}"'
        if bad:
            attr += ', color="#C0392B", fontcolor="#C0392B", style=dashed, penwidth=2'
        elif manual:
            attr += ', color="#E67E22", fontcolor="#E67E22", penwidth=2'
        lines.append(f"{a} -> {b} [{attr}];")
    lines.append("}")
    dot = Path(out).with_suffix(".dot"); dot.write_text("\n".join(lines), encoding="utf-8")
    subprocess.run([dot_executable(), "-Tpng", "-Gdpi=100", str(dot), "-o", str(out)], check=True)
    print("ok", len(ids), "вузлів,", len(triples), "ребер")


if __name__ == "__main__":
    main()
