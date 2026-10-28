"""Перевірка визначень класів: (1) формат «рід + відмінність» (рід = батьківський клас); (2) відсутність самопосилань («Насос — це насос»);
(3) відсутність кругових залежностей між визначеннями (клас A у визначенні B, B у визначенні A, у т. ч. через ланцюг)."""
import csv
import re
import sys
from pathlib import Path

import networkx as nx

ROOT = Path(__file__).resolve().parents[1]
rows = list(csv.DictReader(open(ROOT / "models/class_table.csv", encoding="utf-8-sig")))
by = {r["id"]: r for r in rows}


def mentions(text, label):
    l = label.lower()
    if len(l) < 5:
        return re.search(rf"(?<!\w){re.escape(l)}(?!\w)", text.lower()) is not None
    stem = l[:-2] if len(l) > 7 else l[:-1]
    return re.search(rf"(?<!\w){re.escape(stem)}", text.lower()) is not None


def check():
    issues, G = [], nx.DiGraph()
    for r in rows:
        diff, genus = r["differentia"], r["genus"]
        if not diff.strip(): issues.append((r["id"], "немає відмінності"))
        parent = by.get(r["parent"])
        if parent and genus.lower() != parent["label_uk"].lower():
            issues.append((r["id"], f"рід «{genus}» ≠ батьківський клас «{parent['label_uk']}»"))
        if mentions(diff, r["label_uk"]) or genus.lower() == r["label_uk"].lower():
            issues.append((r["id"], "самопосилання: у відмінності/роді згадано сам термін"))
        for o in rows:
            if o["id"] != r["id"] and o["id"] != r["parent"] and mentions(diff, o["label_uk"]):
                G.add_edge(r["id"], o["id"])
    cycles = list(nx.simple_cycles(G))
    out = [f"Класів: {len(rows)}; проблем формату/самопосилань: {len(issues)}; циклів залежностей між визначеннями: {len(cycles)}"]
    out += [f"  {i}: {m}" for i, m in issues] + [f"  цикл: {' → '.join(c)}" for c in cycles]
    out += ["", "Залежності (клас → класи, згадані у відмінності):"] + [f"  {a} → {', '.join(sorted(G.successors(a)))}" for a in sorted(G.nodes) if list(G.successors(a))]
    (ROOT / "docs/evidence/definition_check.txt").write_text("\n".join(out) + "\n", encoding="utf-8")
    print("\n".join(out[:12]))
    return issues, cycles


if __name__ == "__main__":
    i, c = check()
    sys.exit(1 if i or c else 0)
