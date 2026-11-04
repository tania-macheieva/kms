"""Build data/gold.jsonl from two blind annotations + adjudication; compute kappa. Deterministic."""
import sys, json, collections, itertools, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "src"))
from common import *

def cohen(a, b):
    n = len(a); po = sum(x == y for x, y in zip(a, b)) / n
    ca, cb = collections.Counter(a), collections.Counter(b)
    pe = sum(ca[k] * cb[k] for k in set(ca) | set(cb)) / n ** 2
    return (po - pe) / (1 - pe) if pe < 1 else 1.0

P = {p["id"]: p for p in load_passages()}
A = json.load(open(ROOT / "llm_log/raw/annot_A1.json")); B = json.load(open(ROOT / "llm_log/raw/annot_A2.json"))
J = json.load(open(ROOT / "llm_log/raw/adjudication.json"))
dr = {d["id"]: d for d in json.load(open(ROOT / "llm_log/in/disputes_in.json"))}
de = {d["id"]: d for d in json.load(open(ROOT / "llm_log/in/ent_disputes_in.json"))}
jr = {x["id"]: x for x in J["relations"]}; je = {x["id"]: x for x in J["entities"]}
rel_by = {(d["passage_id"], norm(d["subject"]), d["relation"], norm(d["object"])): d["id"] for d in dr.values()}
ent_by = {(d["passage_id"], norm(d["text"])): d["id"] for d in de.values()}

gold, stats = [], collections.Counter()
rel_rows_a, rel_rows_b = [], []      # kappa grid
ent_rows_a, ent_rows_b = [], []
type_a, type_b = [], []
for a, b in zip(A, B):
    pid = a["passage_id"]; p = P[pid]; txt = p["text"]
    ents = {}
    ea = {norm(e["text"]): e for e in a["entities"]}; eb = {norm(e["text"]): e for e in b["entities"]}
    for k in set(ea) | set(eb):
        ent_rows_a.append(int(k in ea)); ent_rows_b.append(int(k in eb))
        if k in ea and k in eb:
            type_a.append(ea[k]["type"]); type_b.append(eb[k]["type"])
        src = "both" if k in ea and k in eb else ("A1" if k in ea else "A2")
        e = ea.get(k) or eb.get(k); typ = e["type"]
        if src != "both" or ea[k]["type"] != eb[k]["type"]:
            d = je[ent_by[(pid, k)]]
            if d["decision"] != "accept": stats["ent_rejected"] += 1; continue
            typ = d["type"]
        ents[k] = (e["text"], typ, src)
    ra = {(norm(r["subject"]), r["relation"], norm(r["object"])): r for r in a["relations"]}
    rb = {(norm(r["subject"]), r["relation"], norm(r["object"])): r for r in b["relations"]}
    rels = {}
    for k in set(ra) | set(rb):
        src = "both" if k in ra and k in rb else ("A1" if k in ra else "A2")
        r = ra.get(k) or rb.get(k)
        if src != "both":
            if jr[rel_by[(pid, *k)]]["decision"] != "accept": stats["rel_rejected"] += 1; continue
        rels[k] = (r, src)
        for x in (k[0], k[2]):   # entities in accepted relations must exist
            ents.setdefault(x, (r["subject"] if x == k[0] else r["object"], REL_TYPES[k[1]][0 if x == k[0] else 1], "from_relation"))
    # kappa grid: all type-compatible (subject, relation, object) over union entities of the passage
    allents = {}
    for k, (t, ty, s) in ents.items(): allents[k] = ty
    for s_, so in allents.items():
        for o_, oo in allents.items():
            for rel, (ts, to) in REL_TYPES.items():
                if so == ts and oo == to and s_ != o_:
                    rel_rows_a.append(int((s_, rel, o_) in ra)); rel_rows_b.append(int((s_, rel, o_) in rb))
    for k, (t, ty, s) in sorted(ents.items()):
        i = find_offset(txt, t)
        gold.append({"kind": "entity", "passage_id": pid, "doc_id": p["doc_id"], "split": p["split"], "text": t, "norm": k,
                     "type": ty, "start": i, "end": i + len(t) if i >= 0 else -1, "doc_start": p["start"] + i if i >= 0 else -1, "source": s})
    for k, (r, s) in sorted(rels.items()):
        i = find_offset(txt, r["evidence"])
        gold.append({"kind": "relation", "passage_id": pid, "doc_id": p["doc_id"], "split": p["split"], "subject": r["subject"],
                     "relation": r["relation"], "object": r["object"], "triple": list(k), "evidence": r["evidence"],
                     "start": i, "end": i + len(r["evidence"]), "doc_start": p["start"] + i, "source": s})
for n_, g in enumerate(gold, 1): g["id"] = f"G{n_:04d}"
with open(ROOT / "data/gold.jsonl", "w", encoding="utf-8") as f:
    for g in gold: f.write(json.dumps(g, ensure_ascii=False) + "\n")
rels = [g for g in gold if g["kind"] == "relation"]; ents = [g for g in gold if g["kind"] == "entity"]
pos = sum(x and y for x, y in zip(rel_rows_a, rel_rows_b))
kap = {"relation_grid_n": len(rel_rows_a), "relation_kappa_grid": round(cohen(rel_rows_a, rel_rows_b), 3),
       "relation_positive_agreement_F1": round(2 * pos / (sum(rel_rows_a) + sum(rel_rows_b)), 3),
       "relation_both": pos, "relation_A1": sum(rel_rows_a), "relation_A2": sum(rel_rows_b),
       "entity_presence_kappa_pool": round(cohen(ent_rows_a, ent_rows_b), 3), "entity_pool_n": len(ent_rows_a),
       "entity_presence_positive_agreement_F1": round(2 * sum(x and y for x, y in zip(ent_rows_a, ent_rows_b)) / (sum(ent_rows_a) + sum(ent_rows_b)), 3),
       "entity_type_kappa_on_agreed": round(cohen(type_a, type_b), 3), "entity_type_n": len(type_a),
       "gold_entities": len(ents), "gold_relations": len(rels), "gold_statements": len(gold),
       "by_split": {s: {"entities": sum(g["split"] == s for g in ents), "relations": sum(g["split"] == s for g in rels),
                         "docs": len({g["doc_id"] for g in gold if g["split"] == s})} for s in ("dev", "test")},
       "relations_by_type": dict(collections.Counter(g["relation"] for g in rels)),
       "entities_by_type": dict(collections.Counter(g["type"] for g in ents)),
       "docs": len({g["doc_id"] for g in gold}), "offset_missing": sum(g["start"] < 0 for g in gold), **dict(stats)}
json.dump(kap, open(ROOT / "eval/gold_stats.json", "w"), indent=1, ensure_ascii=False)
print(json.dumps(kap, indent=1))
