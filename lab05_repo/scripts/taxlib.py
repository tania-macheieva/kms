"""Спільні функції: завантаження трьох версій у єдиний формат (id, parent_id, label, level, term_id)."""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def load_terms():
    return list(csv.DictReader(open(ROOT / "models/terms.csv", encoding="utf-8-sig")))


def load_csv_tax(path):
    rows = list(csv.DictReader(open(path, encoding="utf-8-sig")))
    return [{"id": r["id"], "parent_id": r["parent_id"] or None, "label": r["label"], "level": int(r["level"]),
             "term_id": r.get("term_id") or None, "principle": r.get("principle") or None} for r in rows]


def load_llm(path=ROOT / "models/tax_llm.json"):
    d = json.loads(Path(path).read_text(encoding="utf-8"))
    return [{"id": n["id"], "parent_id": n["parent_id"], "label": n["label"], "level": n["level"], "term_id": n["term_id"],
             "principle": n.get("principle_of_division")} for n in d["nodes"]]


def load_all():
    return {"expert": load_csv_tax(ROOT / "models/tax_expert.csv"),
            "llm": load_llm(),
            "cluster": load_csv_tax(ROOT / "models/tax_cluster.csv")}


def children_map(nodes):
    m = {}
    for n in nodes:
        m.setdefault(n["parent_id"], []).append(n)
    return m


def ancestor_at_level(nodes, level):
    """term_id → id предка на заданому рівні (або самого вузла, якщо він мілкіший)."""
    by_id = {n["id"]: n for n in nodes}
    out = {}
    for n in nodes:
        if not n["term_id"]:
            continue
        cur = n
        while cur["level"] > level:
            cur = by_id[cur["parent_id"]]
        out[n["term_id"]] = cur["id"]
    return out


def load_final():
    rows = list(csv.DictReader(open(ROOT / "models/taxonomy_final.csv", encoding="utf-8-sig")))
    return [{"id": r["id"], "parent_id": r["parent"] or None, "label": r["label"], "level": int(r["level"]),
             "term_id": r["term_id"] or None, "principle": r["principle"] or None} for r in rows]
