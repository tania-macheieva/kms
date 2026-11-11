"""Quality history/trend: run the gate on five successive snapshots of the repair work (S0 baseline -> S4 final) and plot the trend.
Rebuilds quality/history.jsonl from scratch (so the demo is reproducible) and writes quality/trend.png."""
import sys, json, shutil, subprocess, tempfile, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from quality.common import ROOT, chunks
from quality import dedup as D
H = ROOT / "quality/history.jsonl"; H.unlink(missing_ok=True); tmp = pathlib.Path(tempfile.mkdtemp()); stages = {}
def clone(name, base="store"): d = tmp / name; shutil.copytree(ROOT / base, d); return d
def write_corpus(d, rows):
    with open(d / "corpus.jsonl", "w", encoding="utf-8") as f:
        for c in rows: f.write(json.dumps(c, ensure_ascii=False) + "\n")
pairs = [(json.loads(l)["canonical"], a) for l in open(ROOT / "quality/merge_log.jsonl") for a in json.loads(l)["absorbed"]]
merged, _ = D.merge(chunks(ROOT / "store"), pairs)
stages["S0_baseline"] = ROOT / "store"
d = clone("S1_dedup"); write_corpus(d, merged); stages["S1_dedup"] = d
d = clone("S2_titles", "store"); shutil.copy(ROOT / "store_clean/corpus.jsonl", d / "corpus.jsonl"); shutil.copy(ROOT / "store_clean/docs_manifest.json", d / "docs_manifest.json"); stages["S2_titles_sections"] = d
d = clone("S3_conflicts", "store"); [shutil.copy(ROOT / "store_clean" / n, d / n) for n in ("corpus.jsonl", "docs_manifest.json", "alternatives.jsonl", "aliases.csv")]; stages["S3_alternatives_aliases"] = d
stages["S4_final_graph_rule"] = ROOT / "store_clean"
for k, d in stages.items():
    r = subprocess.run([sys.executable, str(ROOT / "quality/gate.py"), "--store", str(d), "--label", k], cwd=ROOT, capture_output=True, text=True); print(r.stdout.strip().splitlines()[0])
shutil.rmtree(tmp)
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
rows = [json.loads(l) for l in open(H)]; x = [r["label"].replace("_", "\n", 1) for r in rows]
fig, ax = plt.subplots(figsize=(8, 3.6)); ax.plot(x, [r["blocking_failed"] for r in rows], "o-", color="#c0392b", label="blocking failures"); ax.plot(x, [r["warnings"] for r in rows], "s--", color="#e69f00", label="warnings (M06, M14)")
for i, r in enumerate(rows): ax.annotate(str(r["blocking_failed"]), (i, r["blocking_failed"]), textcoords="offset points", xytext=(0, 7), ha="center")
ax.set_ylabel("failed checks (of 25)"); ax.set_title("Quality-gate trend over repair stages"); ax.legend(); ax.grid(alpha=.3); plt.xticks(fontsize=7); plt.tight_layout(); plt.savefig(ROOT / "quality/trend.png", dpi=150)
