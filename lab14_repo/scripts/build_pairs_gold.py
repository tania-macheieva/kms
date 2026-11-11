"""Merge the two annotators' labels, compute agreement, list disagreements (adjudicated in llm_log/raw/pairs_adjudication.json), write quality/pairs_gold.csv with dev/test split."""
import json, csv, random, collections, sys, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
cand = json.load(open(ROOT / "data/pairs_candidates.json"))
def load(l): return {x["pair_id"]: x for b in range(1, 5) for x in json.load(open(ROOT / f"llm_log/raw/pairs_{l}_b{b}.json"))}
L1, L2 = load("L1"), load("L2"); assert len(L1) == len(L2) == 160
b = lambda x: x == "DUP"
n = len(cand); po = sum(b(L1[p["pair_id"]]["label"]) == b(L2[p["pair_id"]]["label"]) for p in cand) / n
p1, p2 = sum(b(L1[p["pair_id"]]["label"]) for p in cand) / n, sum(b(L2[p["pair_id"]]["label"]) for p in cand) / n
pe = p1 * p2 + (1 - p1) * (1 - p2); kb = (po - pe) / (1 - pe)
labs = ["DUP", "RELATED", "DISTINCT"]; po3 = sum(L1[p["pair_id"]]["label"] == L2[p["pair_id"]]["label"] for p in cand) / n
pe3 = sum((sum(L1[p["pair_id"]]["label"] == l for p in cand) / n) * (sum(L2[p["pair_id"]]["label"] == l for p in cand) / n) for l in labs); k3 = (po3 - pe3) / (1 - pe3)
dis = [p["pair_id"] for p in cand if b(L1[p["pair_id"]]["label"]) != b(L2[p["pair_id"]]["label"])]
adj_f = ROOT / "llm_log/raw/pairs_adjudication.json"; adj = {x["pair_id"]: x for x in json.load(open(adj_f))} if adj_f.exists() else {}
stats = dict(n=n, binary_agreement=round(po, 3), binary_kappa=round(kb, 3), three_class_kappa=round(k3, 3), disagreements=dis, adjudicated=sorted(adj))
json.dump(stats, open(ROOT / "eval/pairs_agreement.json", "w"), indent=1); print(stats)
if any(d not in adj for d in dis): print("NEED ADJUDICATION:", [d for d in dis if d not in adj]); sys.exit(0)
rows = []
for p in cand:
    i = p["pair_id"]; lab = adj[i]["label"] if i in adj else (L1[i]["label"] if b(L1[i]["label"]) == b(L2[i]["label"]) and L1[i]["label"] == L2[i]["label"] else L1[i]["label"])
    if i not in adj and L1[i]["label"] != L2[i]["label"]: lab = "RELATED" if "RELATED" in (L1[i]["label"], L2[i]["label"]) else L1[i]["label"]  # DUP-vs-DISTINCT never occurs (would be adjudicated); RELATED/other -> RELATED
    rows.append(dict(p, label=lab, dup=int(lab == "DUP"), l1=L1[i]["label"], l2=L2[i]["label"], adjudicated=i in adj))
main = [r for r in rows if not r["probe"]]; probes = [r for r in rows if r["probe"]]
random.seed(14); pos = [r for r in main if r["dup"]]; neg = [r for r in main if not r["dup"]]; random.shuffle(pos); random.shuffle(neg)
for grp in (pos, neg):
    for k, r in enumerate(grp): r["split"] = "dev" if k % 2 == 0 else "test"
for r in probes: r["split"] = "probe"
cols = ["pair_id", "a", "b", "label", "dup", "split", "l1", "l2", "adjudicated", "score", "fuzz", "ratio", "tfidf", "emb", "same_doc", "tail_eq", "same_sens", "len_ratio", "band"]
with open(ROOT / "quality/pairs_gold.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore"); w.writeheader(); w.writerows(sorted(rows, key=lambda r: r["pair_id"]))
print(collections.Counter((r["split"], r["label"]) for r in rows))
