"""Assemble store_clean/ (the improved snapshot) from store/ (baseline): dedup-merged corpus (run_dedup.py) + repaired titles/sections
+ graph without the rule-violating edge + alternatives register + aliases. Idempotent."""
import sys, json, shutil, csv, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from quality.common import ROOT
S, C = ROOT / "store", ROOT / "store_clean"
if not (C / "corpus.jsonl").exists(): sys.exit("run scripts/run_dedup.py first")
T = json.load(open(ROOT / "quality/doc_titles.json")); rows = [json.loads(l) for l in open(C / "corpus.jsonl", encoding="utf-8")]; nt = ns = 0
def fix(c):
    global nt, ns
    if c["doc_id"] in T and c["title"] != T[c["doc_id"]]: c["old_title"] = c.get("old_title", c["title"]); c["title"] = T[c["doc_id"]]; nt += 1
    if not c["section"].strip(): c["section"] = "Preamble"; ns += 1
for c in rows:
    fix(c)
    for m in c.get("merged_from", []): fix(m)
with open(C / "corpus.jsonl", "w", encoding="utf-8") as f:
    for c in rows: f.write(json.dumps(c, ensure_ascii=False) + "\n")
man = json.load(open(S / "docs_manifest.json"))
for d in man:
    if d["doc_id"] in T: d["old_title"] = d["title"]; d["title"] = T[d["doc_id"]]
json.dump(man, open(C / "docs_manifest.json", "w"), ensure_ascii=False, indent=1)
for n in ("fixtures.json", "rag_eval.jsonl", "emb_bge.npy"): shutil.copy(S / n, C / n)
if (C / "docs_clean").exists(): shutil.rmtree(C / "docs_clean")
shutil.copytree(S / "docs_clean", C / "docs_clean"); shutil.copy(ROOT / "quality/aliases.csv", C / "aliases.csv")
(C / "graph").mkdir(exist_ok=True)
for p in (S / "graph").glob("*.csv"):
    if p.name == "rels_APPLIES_TO__Procedure_Person.csv":
        r = list(csv.DictReader(open(p))); keep = [x for x in r if x["to"] != "Sofiia"]; drop = [x for x in r if x["to"] == "Sofiia"]
        w = csv.DictWriter(open(C / "graph" / p.name, "w", newline=""), fieldnames=list(r[0])); w.writeheader(); w.writerows(keep)
        w = csv.DictWriter(open(C / "graph" / "rels_DEFERRED_FOR__Procedure_Person.csv", "w", newline=""), fieldnames=list(r[0]) + ["eligibleAtAge", "reason"]); w.writeheader()
        for x in drop: w.writerow(dict(x, eligibleAtAge=18, reason="CF-AGE-Sofiia: minTestingAge=18 > ageYears=17 (rule S14)"))
    else: shutil.copy(p, C / "graph" / p.name)
print(f"store_clean: {len(rows)} chunks, titles repaired {nt}, sections repaired {ns}")
