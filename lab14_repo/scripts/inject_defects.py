"""R4: copy store_clean to a temp dir and inject 3 defects (each alone and all together); the gate must catch each. Writes eval/defect_injection.json."""
import json, shutil, subprocess, sys, tempfile, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
def _nl(f):
    if not open(f).read().endswith("\n"): open(f, "a").write("\n")
def d1_duplicate(s):   # an exact copy of an existing chunk under a new valid id (dedup regression)
    p = s / "corpus.jsonl"; rows = [json.loads(l) for l in open(p)]; r = dict(rows[5]); r["chunk_id"] = r["doc_id"] + "#h999"; r["start"], r["end"] = 99990, 99999; rows.append(r)
    open(p, "w").write("\n".join(json.dumps(x, ensure_ascii=False) for x in rows) + "\n")
def d2_age_rule(s):    # re-introduce the logical conflict: CT-01 (minTestingAge 18) APPLIES_TO the 17-year-old
    f = s / "graph/rels_APPLIES_TO__Procedure_Person.csv"; _nl(f); open(f, "a").write("CT-01,Sofiia,cdc,1.0,2026-10-26\n")
def d3_no_provenance(s):  # relationship without source / validFrom
    f = s / "graph/rels_APPLIES_TO__Procedure_DataFile.csv"; _nl(f); open(f, "a").write("HF-01,sample1_vcf,,0.9,\n")
DEFECTS = {"D1_duplicate_chunk": d1_duplicate, "D2_age_rule_violation": d2_age_rule, "D3_relationship_without_provenance": d3_no_provenance}
def run(d, label):
    subprocess.run([sys.executable, str(ROOT / "quality/gate.py"), "--store", str(d), "--label", label, "--no-history"], cwd=ROOT, capture_output=True, text=True)
    rep = json.load(open(ROOT / f"quality/gate_report_{label}.json")); return dict(gate=rep["gate"], caught_by=[r["check"] for r in rep["results"] if r["status"] == "fail" and r["severity"] == "blocking"])
out = {}; tmp = pathlib.Path(tempfile.mkdtemp())
for name, fn in list(DEFECTS.items()) + [("ALL_THREE", None)]:
    d = tmp / name; shutil.copytree(ROOT / "store_clean", d)
    for k, f in DEFECTS.items():
        if fn is None or k == name: f(d)
    out[name] = run(d, "inject_" + name); print(name, out[name])
json.dump(out, open(ROOT / "eval/defect_injection.json", "w"), indent=1); shutil.rmtree(tmp)
