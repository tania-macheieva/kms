"""Tune the threshold on dev (centre of the F1 plateau), evaluate on test; single-feature baselines; 5-fold CV supplement; blocking stats."""
import csv, json, sys, pathlib, numpy as np
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from quality import dedup as D
from quality.common import ROOT
rows = list(csv.DictReader(open(ROOT / "quality/pairs_gold.csv", encoding="utf-8")))
for r in rows:
    for k in ("fuzz", "ratio", "tfidf", "emb", "len_ratio", "score"): r[k] = float(r[k])
    r["dup"] = int(r["dup"]); r["same_sens"] = r["same_sens"] == "True"
dev = [r for r in rows if r["split"] == "dev"]; test = [r for r in rows if r["split"] == "test"]; probes = [r for r in rows if r["split"] == "probe"]
def prf(rs, fn):
    tp = sum(fn(r) and r["dup"] for r in rs); fp = sum(fn(r) and not r["dup"] for r in rs); fn_ = sum((not fn(r)) and r["dup"] for r in rs)
    p = tp / (tp + fp) if tp + fp else 1.0; rc = tp / (tp + fn_) if tp + fn_ else 0.0; f = 2 * p * rc / (p + rc) if p + rc else 0.0
    return dict(tp=tp, fp=fp, fn=fn_, precision=round(p, 3), recall=round(rc, 3), f1=round(f, 3))
grid = [round(x, 3) for x in np.arange(0.50, 1.0001, 0.005)]
def plateau(rs, key):
    f1 = {t: prf(rs, lambda r: r[key] >= t and r["same_sens"])["f1"] for t in grid}; best = max(f1.values()); ts = [t for t in grid if f1[t] == best]
    return best, ts[0], ts[-1], round((ts[0] + ts[-1]) / 2, 3)
out = dict(n=len(rows), n_dev=len(dev), n_test=len(test), dup_dev=sum(r["dup"] for r in dev), dup_test=sum(r["dup"] for r in test))
res = {}
for key in ("score", "tfidf", "emb", "fuzz", "ratio"):
    best, lo, hi, th = plateau(dev, key)
    res[key] = dict(threshold=th, dev_best_f1=best, plateau=[lo, hi], dev=prf(dev, lambda r: r[key] >= th and r["same_sens"]), test=prf(test, lambda r: r[key] >= th and r["same_sens"]))
out["by_feature"] = res; out["threshold"] = res["score"]["threshold"]; out["borderline_band"] = 0.08
th = out["threshold"]
# 5-fold CV over all labelled non-probe pairs (threshold re-tuned per fold) — a supplement given the small number of positives
rng = np.random.default_rng(14); allr = [r for r in rows if r["split"] != "probe"]; idx = rng.permutation(len(allr)); folds = np.array_split(idx, 5); tp = fp = fn = 0
for k in range(5):
    te = [allr[i] for i in folds[k]]; tr = [allr[i] for j in range(5) if j != k for i in folds[j]]
    t = plateau(tr, "score")[3]; m = prf(te, lambda r: r["score"] >= t and r["same_sens"]); tp += m["tp"]; fp += m["fp"]; fn += m["fn"]
p = tp / (tp + fp) if tp + fp else 1; rc = tp / (tp + fn) if tp + fn else 0; out["cv5"] = dict(tp=tp, fp=fp, fn=fn, precision=round(p, 3), recall=round(rc, 3), f1=round(2 * p * rc / (p + rc), 3))
# bootstrap CI for the test precision/recall of the chosen rule
bs = []
for _ in range(2000):
    s = [test[i] for i in rng.integers(0, len(test), len(test))]; m = prf(s, lambda r: r["score"] >= th and r["same_sens"]); bs.append((m["precision"], m["recall"]))
bs = np.array(bs); out["test_ci95"] = dict(precision=[round(float(np.percentile(bs[:, 0], 2.5)), 2), round(float(np.percentile(bs[:, 0], 97.5)), 2)], recall=[round(float(np.percentile(bs[:, 1], 2.5)), 2), round(float(np.percentile(bs[:, 1], 97.5)), 2)])
# errors on test and dev
out["errors"] = [dict(pair_id=r["pair_id"], a=r["a"], b=r["b"], gold=r["label"], score=r["score"], kind=("FP" if not r["dup"] else "FN"), split=r["split"])
                 for r in dev + test if ((r["score"] >= th and r["same_sens"]) != bool(r["dup"]))]
# borderline zone and judge coverage on the gold pairs
band = out["borderline_band"]; bl = [r for r in dev + test if abs(r["score"] - th) <= band]
out["borderline_in_gold"] = dict(n=len(bl), dup=sum(r["dup"] for r in bl))
out["blocking"] = dict(chunks=len(D.Store().c), all_pairs=len(D.Store().c) * (len(D.Store().c) - 1) // 2, candidates=len(D.blocking(D.Store())), probes=len(probes), probes_dup=sum(r["dup"] for r in probes))
json.dump(out, open(ROOT / "eval/dedup_eval.json", "w"), indent=1, default=lambda o: o.item() if hasattr(o, "item") else str(o)); print(json.dumps({k: v for k, v in out.items() if k != "errors"}, indent=1, default=lambda o: o.item())); print("errors", [(e["pair_id"], e["kind"], e["score"]) for e in out["errors"]])
