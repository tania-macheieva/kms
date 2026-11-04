"""Оцінювання карт: рубрика Новака (оцінки двох оцінювачів), узгодженість, precision/recall триплетів LLM відносно експертної карти.

Запуск: python scripts/eval_maps.py   → docs/evidence/map_eval.json, docs/evidence/map_eval.txt
"""
import json
import re
import sys
from pathlib import Path

import numpy as np
from scipy.stats import pearsonr, spearmanr
from sklearn.metrics import cohen_kappa_score

sys.path.insert(0, str(Path(__file__).resolve().parent))
from map_tools import ROOT, load_map, stats                         # noqa: E402

DIMS = ["D1", "D2", "D3", "D4", "D5"]
DIM_NAMES = {"D1": "Пропозиції", "D2": "Ієрархія", "D3": "Крос-зв'язки", "D4": "Приклади", "D5": "Покриття CQ"}
MAPS = {"expert": "Власна (експертна) карта", "llm": "Карта LLM (триплети)", "peer": "Карта колеги (замінник — LLM)"}


def norm_label(x):
    x = re.sub(r"\(.*?\)", "", x).strip().casefold()
    return re.sub(r"\s+", " ", x)


def stmt_set(m):
    by = {c["id"]: c["label"] for c in m["concepts"]}
    return {(norm_label(by[p["s"]]), p["p"], norm_label(by[p["o"]])) for p in m["propositions"]}


def load_scores():
    out = {}
    for r in ("R1", "R2"):
        letters = json.loads((ROOT / f"llm_log/raw/step5_rubric_{r}_letters.json").read_text(encoding="utf-8"))    # map → letter
        raw = json.loads((ROOT / f"llm_log/raw/step5_rubric_{r}_raw_output.json").read_text(encoding="utf-8"))
        inv = {v: k for k, v in letters.items()}
        out[r] = {inv[l]: v for l, v in raw.items()}
    return out


def agreement(sc):
    a = [sc["R1"][m][d] for m in MAPS for d in DIMS]
    b = [sc["R2"][m][d] for m in MAPS for d in DIMS]
    diffs = np.abs(np.array(a) - np.array(b))
    res = {"n_pairs": len(a), "mean_abs_diff": float(diffs.mean()), "exact_agreement": float((diffs == 0).mean()),
           "within_1": float((diffs <= 1).mean()), "pearson": float(pearsonr(a, b)[0]), "spearman": float(spearmanr(a, b)[0]),
           "weighted_kappa_quadratic": float(cohen_kappa_score(a, b, weights="quadratic", labels=[0, 1, 2, 3, 4]))}
    res["per_map_mean_abs_diff"] = {m: float(np.mean([abs(sc["R1"][m][d] - sc["R2"][m][d]) for d in DIMS])) for m in MAPS}
    res["per_dim_mean_abs_diff"] = {d: float(np.mean([abs(sc["R1"][m][d] - sc["R2"][m][d]) for m in MAPS])) for d in DIMS}
    res["totals"] = {m: {"R1": sum(sc["R1"][m][d] for d in DIMS), "R2": sum(sc["R2"][m][d] for d in DIMS)} for m in MAPS}
    res["rank_agreement"] = [sorted(MAPS, key=lambda m: -sum(sc[r][m][d] for d in DIMS)) for r in ("R1", "R2")]
    return res


def precision_recall():
    exp, llm, peer = (load_map(ROOT / f"models/cmap_{k}.json") for k in ("expert", "llm_as_map", "peer")) if (ROOT / "models/cmap_llm_as_map.json").exists() else (None, None, None)
    return exp, llm, peer


def llm_stmts():
    tr = [json.loads(l) for l in (ROOT / "models/triples_llm.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    return tr, {(norm_label(t["s"]), t["p"], norm_label(t["o"])) for t in tr}


def pr(pred, gold):
    tp = pred & gold
    p = len(tp) / len(pred) if pred else 0
    r = len(tp) / len(gold) if gold else 0
    return {"tp": len(tp), "pred": len(pred), "gold": len(gold), "precision": p, "recall": r, "f1": 2 * p * r / (p + r) if p + r else 0}


def relaxed(pred, gold):
    go = {(s, o) for s, _, o in gold}
    pr_ = {(s, o) for s, _, o in pred}
    tp = pr_ & go
    return {"tp_pairs": len(tp), "precision": len(tp) / len(pr_), "recall": len(tp) / len(go)}


def main():
    sc = load_scores()
    ag = agreement(sc)
    exp = load_map(ROOT / "models/cmap_expert.json")
    peer = load_map(ROOT / "models/cmap_peer.json")
    tr, L = llm_stmts()
    E, P = stmt_set(exp), stmt_set(peer)
    manual = {r["id"] for r in json.loads((ROOT / "data/triples_manual_review.json").read_text(encoding="utf-8"))["reviewed"]}
    bad_auto = {t["id"] for t in tr if t["checks"]}
    supported = [t for t in tr if t["id"] not in bad_auto and t["id"] not in manual]
    res = {"scores": sc, "agreement": ag,
           "llm_vs_expert_strict": pr(L, E), "llm_vs_expert_relaxed": relaxed(L, E),
           "peer_vs_expert_strict": pr(P, E), "peer_vs_expert_relaxed": relaxed(P, E),
           "llm_text_supported_precision": {"supported": len(supported), "total": len(tr), "share": len(supported) / len(tr),
                                            "auto_errors": sorted(bad_auto), "manual_flags": sorted(manual)},
           "map_stats": {"expert": stats(exp), "peer": stats(peer)},
           "matches": sorted(map(list, L & E)), "llm_only": sorted(map(list, L - E)), "expert_only": sorted(map(list, E - L))}
    (ROOT / "docs/evidence").mkdir(exist_ok=True)
    (ROOT / "docs/evidence/map_eval.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    t = []
    t.append("== Оцінки (0–4) за D1..D5; R1/R2 — два незалежні оцінювачі (обидва LLM)")
    for m in MAPS:
        t.append(f"{MAPS[m]:34} R1: {[sc['R1'][m][d] for d in DIMS]} = {ag['totals'][m]['R1']}; R2: {[sc['R2'][m][d] for d in DIMS]} = {ag['totals'][m]['R2']}")
    t.append("\n== Узгодженість оцінювачів (15 пар оцінок)")
    for k, v in ag.items():
        if not isinstance(v, (dict, list)):
            t.append(f"  {k}: {v:.3f}" if isinstance(v, float) else f"  {k}: {v}")
    t.append(f"  по картах (середня |різниця|): { {k: round(v, 2) for k, v in ag['per_map_mean_abs_diff'].items()} }")
    t.append(f"  по критеріях: { {k: round(v, 2) for k, v in ag['per_dim_mean_abs_diff'].items()} }")
    t.append(f"  порядок карт за сумою: R1 {ag['rank_agreement'][0]}; R2 {ag['rank_agreement'][1]}")
    t.append("\n== Precision/recall триплетів LLM відносно експертної карти (орієнтовані (s,p,o), нормалізовані мітки)")
    for k in ("llm_vs_expert_strict", "llm_vs_expert_relaxed", "peer_vs_expert_strict", "peer_vs_expert_relaxed"):
        t.append(f"  {k}: " + json.dumps(res[k], ensure_ascii=False))
    t.append(f"  LLM: підтримано текстом і без помилок перевірки/перегляду: {res['llm_text_supported_precision']['supported']}/{len(tr)} = {res['llm_text_supported_precision']['share']:.0%}")
    t.append(f"\n  збіг з експертною картою ({len(res['matches'])}):")
    t += [f"    {s} -{p}-> {o}" for s, p, o in res["matches"]]
    t.append(f"  лише в LLM ({len(res['llm_only'])}):")
    t += [f"    {s} -{p}-> {o}" for s, p, o in res["llm_only"]]
    t.append(f"  лише в експертній ({len(res['expert_only'])}):")
    t += [f"    {s} -{p}-> {o}" for s, p, o in res["expert_only"]]
    txt = "\n".join(t)
    (ROOT / "docs/evidence/map_eval.txt").write_text(txt + "\n", encoding="utf-8")
    print(txt)


if __name__ == "__main__":
    main()
