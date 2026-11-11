"""Aggregates eval/res_*.json and eval/cold.json -> eval/summary.json, eval/table.md, docs/img/*.png"""
import json, glob, pathlib, numpy as np
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
ROOT = pathlib.Path(__file__).resolve().parent.parent; R = {}
for f in sorted(glob.glob(str(ROOT / "eval/res_*.json"))): R.update(json.load(open(f)))
seeds = sorted(R); cfgs = ["popularity", "graph", "knn", "hybrid-weighted", "hybrid-rrf"]; mets = ["p5", "r5", "ndcg10", "coverage", "novelty"]
S = {}
for c in cfgs:
    S[c] = {}
    for m in mets:
        v = np.array([R[s]["configs"][c][m] for s in seeds]); lo = np.mean([R[s]["configs"][c]["ci"][m][0] for s in seeds]); hi = np.mean([R[s]["configs"][c]["ci"][m][1] for s in seeds])
        if m == "coverage": lo, hi = float(v.min()), float(v.max())      # bootstrap over users biases coverage downward -> use the range over seeds
        S[c][m] = dict(mean=float(v.mean()), sd=float(v.std(ddof=1)), ci_lo=float(lo), ci_hi=float(hi), per_seed=v.tolist())
rng = np.random.default_rng(0); paired = {}
for base in ("popularity", "knn", "graph"):
    d = []
    for s in seeds:
        a = np.array(R[s]["configs"]["hybrid-weighted"]["per_user"]["ndcg10"]); b = np.array(R[s]["configs"][base]["per_user"]["ndcg10"]); d.append(a - b)
    allv = np.concatenate(d); bs = [allv[rng.integers(0, len(allv), len(allv))].mean() for _ in range(2000)]; paired[base] = dict(mean_diff=float(allv.mean()), lo=float(np.percentile(bs, 2.5)), hi=float(np.percentile(bs, 97.5)), users=len(allv))
tun = {s: R[s]["params"] for s in seeds}; info = {s: {k: R[s][k] for k in ("n_users", "n_positives", "n_events", "n_train", "n_test")} for s in seeds}
json.dump(dict(summary=S, paired_ndcg_hybrid_minus=paired, tuned=tun, info=info), open(ROOT / "eval/summary.json", "w"), indent=1)
lab = dict(p5="P@5", r5="R@5", ndcg10="nDCG@10", coverage="coverage@5", novelty="novelty@5 (bit)")
with open(ROOT / "eval/table.md", "w") as f:
    f.write("| configuration | " + " | ".join(lab[m] for m in mets) + " |\n|---|" + "---|" * len(mets) + "\n")
    for c in cfgs: f.write(f"| {c} | " + " | ".join(f"{S[c][m]['mean']:.3f} ± {S[c][m]['sd']:.3f} [{S[c][m]['ci_lo']:.3f}; {S[c][m]['ci_hi']:.3f}]" for m in mets) + " |\n")
col = {"popularity": "#8a8a8a", "graph": "#2a6fdb", "knn": "#1b9e77", "hybrid-weighted": "#d95f02", "hybrid-rrf": "#7570b3"}
fig, ax = plt.subplots(1, 4, figsize=(13, 3.4))
for a, m in zip(ax, ["p5", "ndcg10", "coverage", "novelty"]):
    x = np.arange(len(cfgs)); mu = [S[c][m]["mean"] for c in cfgs]; err = [[max(S[c][m]["mean"] - S[c][m]["ci_lo"], 0) for c in cfgs], [max(S[c][m]["ci_hi"] - S[c][m]["mean"], 0) for c in cfgs]]
    a.bar(x, mu, yerr=err, color=[col[c] for c in cfgs], capsize=3); a.set_xticks(x); a.set_xticklabels(["pop", "graph", "kNN", "hyb-w", "hyb-rrf"], rotation=30); a.set_title(lab[m]); a.spines[["top", "right"]].set_visible(False)
plt.tight_layout(); plt.savefig(ROOT / "docs/img/eval_bars.png", dpi=160); plt.close()
fig, a = plt.subplots(figsize=(5.4, 3.4))
for c in cfgs: a.plot(seeds, [S[c]["ndcg10"]["per_seed"][i] for i in range(len(seeds))], "o-", label=c, color=col[c])
a.set_xlabel("generator seed"); a.set_ylabel("nDCG@10"); a.legend(fontsize=7); a.spines[["top", "right"]].set_visible(False); plt.tight_layout(); plt.savefig(ROOT / "docs/img/eval_seeds.png", dpi=160); plt.close()
C = json.load(open(ROOT / "eval/cold.json")); ms = ["popularity", "topic-popularity", "knn", "graph", "hybrid"]; cs = {}
for k in ("0", "1", "3"): cs[k] = {m: {x: float(np.mean([C[s]["new_user"][k][m][x] for s in C])) for x in ("p5", "r5", "ndcg10")} for m in ms}
ci = {}
for mode in ("new_section", "new_document"):
    ci[mode] = {ph: {m: float(np.mean([C[s][mode][ph][m]["hit10"] for s in C])) for m in ("popularity", "knn", "graph", "hybrid")} for ph in ("before_insert", "after_insert")}; ci[mode]["pairs"] = int(np.sum([C[s][mode]["after_insert"]["knn"]["pairs"] for s in C])); ci[mode]["n_cold"] = [C[s][mode]["n_cold"] for s in C]
json.dump(dict(new_user=cs, new_item=ci), open(ROOT / "eval/cold_summary.json", "w"), indent=1)
fig, ax = plt.subplots(1, 2, figsize=(10, 3.4)); ks = ["0", "1", "3"]
for m in ms: ax[0].plot(ks, [cs[k][m]["ndcg10"] for k in ks], "o-", label=m)
ax[0].set_xlabel("events in new user's history"); ax[0].set_ylabel("nDCG@10"); ax[0].legend(fontsize=7); ax[0].set_title("A. new user")
w = 0.35; x = np.arange(4); ms2 = ["popularity", "knn", "graph", "hybrid"]
for j, mode in enumerate(("new_section", "new_document")): ax[1].bar(x + j * w, [ci[mode]["after_insert"][m] for m in ms2], w, label=mode)
ax[1].set_xticks(x + w / 2); ax[1].set_xticklabels(ms2); ax[1].set_ylabel("hit-rate@10 of cold items"); ax[1].legend(fontsize=7); ax[1].set_title("B. new item")
for a in ax: a.spines[["top", "right"]].set_visible(False)
plt.tight_layout(); plt.savefig(ROOT / "docs/img/cold_start.png", dpi=160); plt.close(); print(open(ROOT / "eval/table.md").read()); print(json.dumps(paired, indent=1)); print(json.dumps(tun["0"])[:700])
