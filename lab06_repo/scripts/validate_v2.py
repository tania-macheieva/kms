"""Валідація v2: відношення з каталогу, domain/range для понять (екземпляри has_example — виняток), визначення, заповненість CSV."""
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from map_tools import REL, ROOT   # noqa: E402


def validate():
    m = json.loads((ROOT / "models/cmap_v2.json").read_text(encoding="utf-8"))
    rows = list(csv.DictReader(open(ROOT / "models/triples_final.csv", encoding="utf-8-sig")))
    inst = {c["label"] for c in m["concepts"] if c["kind"] == "instance"}
    errs = []
    for c in m["concepts"]:
        if not c.get("definition"):
            errs.append(f"немає визначення: {c['label']}")
    for r in rows:
        if any(not v for v in r.values()):
            errs.append(f"порожнє поле: {r}")
        if r["p"] not in REL:
            errs.append(f"відношення не з каталогу: {r['p']}"); continue
        d = REL[r["p"]]
        if r["o"] in inst:
            if r["p"] != "has_example":
                errs.append(f"екземпляр поза has_example: {r['s']} {r['p']} {r['o']}")
            continue
        if d.get("same_type"):
            if r["s_type"] != r["o_type"]:
                errs.append(f"is_a між типами: {r['s']} → {r['o']}")
        else:
            if d["domain"] != ["*"] and r["s_type"] not in d["domain"]:
                errs.append(f"domain: {r['s']} {r['p']} {r['o']} ({r['s_type']})")
            if d["range"] != ["*"] and r["o_type"] not in d["range"]:
                errs.append(f"range: {r['s']} {r['p']} {r['o']} ({r['o_type']})")
    return m, rows, errs


if __name__ == "__main__":
    m, rows, errs = validate()
    print(len(m["concepts"]), "понять;", len(rows), "рядків;", len(errs), "помилок")
    print("\n".join(errs))
