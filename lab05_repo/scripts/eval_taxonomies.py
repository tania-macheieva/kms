"""Метрики якості трьох версій таксономії, κ Коена для розмітників та скоригований індекс Ренда (ARI).

Запуск: python scripts/eval_taxonomies.py [--json]
Метрики на версію: покриття (частка з 121 термінів, що є вузлами), частка категорій «Інше», глибина/ширина,
автоматичні MECE-перевірки: M1 термін у кількох місцях; M2 внутрішній вузол з єдиною дитиною (поділ не вичерпний);
M3 внутрішній вузол без принципу поділу; M4 нечіткий принцип («тощо», «etc»); M5 однакові мітки серед сусідів.
Ручні MECE-порушення (змішування is-a/part-of, перетини обсягів) перелічено в docs/taxonomy_eval.md окремо.
"""
import csv
import json
import re
import sys
from collections import Counter
from pathlib import Path

from sklearn.metrics import adjusted_rand_score, cohen_kappa_score

sys.path.insert(0, str(Path(__file__).resolve().parent))
from taxlib import ROOT, ancestor_at_level, children_map, load_all, load_final, load_terms   # noqa: E402

OTHER = re.compile(r"\b(other|others|misc\w*|різне|інше|інші)\b", re.I)


def metrics(nodes, n_terms):
    kids = children_map(nodes)
    internal = [n for n in nodes if n["id"] in kids]
    leaves = [n for n in nodes if n["id"] not in kids]
    terms = [n["term_id"] for n in nodes if n["term_id"]]
    cats = [n for n in nodes if not n["term_id"]]
    has_principle = any(n.get("principle") for n in nodes)
    m = {
        "nodes": len(nodes), "terms_as_nodes": len(set(terms)), "coverage": len(set(terms)) / n_terms,
        "category_nodes": len(cats),
        "other_share": sum(1 for n in cats if OTHER.search(n["label"])) / max(1, len(cats)),
        "max_depth": max(n["level"] for n in nodes),
        "internal": len(internal), "leaves": len(leaves),
        "mean_branching": sum(len(kids[n["id"]]) for n in internal) / len(internal),
        "max_branching": max(len(kids[n["id"]]) for n in internal),
        "M1_duplicate_terms": sum(1 for t, c in Counter(terms).items() if c > 1),
        "M2_single_child": sum(1 for n in internal if len(kids[n["id"]]) == 1),
        "M3_no_principle": sum(1 for n in internal if not n.get("principle")) if has_principle else None,
        "M4_vague_principle": sum(1 for n in internal if re.search(r"тощо|etc", n.get("principle") or "", re.I)),
        "M5_same_sibling_labels": sum(1 for p, ch in kids.items() if len({c["label"].casefold() for c in ch}) < len(ch)),
    }
    return m


def single_child_nodes(nodes):
    kids = children_map(nodes)
    return [(n["label"], kids[n["id"]][0]["label"]) for n in nodes if n["id"] in kids and len(kids[n["id"]]) == 1]


def kappa_table():
    cats = {r["term_id"]: r["category"] for r in csv.DictReader(open(ROOT / "annotations/rater_R1_llm.csv", encoding="utf-8"))}
    r2 = {r["term_id"]: r["category"] for r in csv.DictReader(open(ROOT / "annotations/rater_R2_llm.csv", encoding="utf-8"))}
    expert = load_all()["expert"]
    by_id = {n["id"]: n for n in expert}
    anc = ancestor_at_level(expert, 1)
    tax = {t: by_id[a]["label"] for t, a in anc.items()}
    ids = sorted(cats)
    out = {"n_terms": len(ids)}
    pairs = {"R1 vs R2 (обидва LLM)": (cats, r2), "R1 vs експертна таксономія": (cats, tax), "R2 vs експертна таксономія": (r2, tax)}
    human = ROOT / "annotations/rater_human.csv"
    if human.exists():
        h = {r["term_id"]: r["category"] for r in csv.DictReader(open(human, encoding="utf-8-sig")) if r.get("category")}
        if len(h) >= 30:
            pairs["людина vs R1"] = (h, cats); pairs["людина vs експертна таксономія"] = (h, tax)
    for name, (a, b) in pairs.items():
        ids2 = [i for i in ids if i in a and i in b]
        out[name] = {"kappa": cohen_kappa_score([a[i] for i in ids2], [b[i] for i in ids2]),
                     "agreement": sum(a[i] == b[i] for i in ids2) / len(ids2), "n": len(ids2)}
    disagreements = [(i, cats[i], tax[i]) for i in ids if cats[i] != tax[i]]
    return out, disagreements


def ari_table(all_nodes):
    terms = [t["id"] for t in load_terms()]
    res = {}
    for level in (1, 2):
        parts = {k: ancestor_at_level(v, level) for k, v in all_nodes.items()}
        res[f"рівень {level}"] = {
            "expert~llm": adjusted_rand_score([parts["expert"][t] for t in terms], [parts["llm"][t] for t in terms]),
            "expert~cluster": adjusted_rand_score([parts["expert"][t] for t in terms], [parts["cluster"][t] for t in terms]),
            "llm~cluster": adjusted_rand_score([parts["llm"][t] for t in terms], [parts["cluster"][t] for t in terms]),
            "k": {k: len(set(p.values())) for k, p in parts.items()}}
    return res


def contingency(all_nodes, a, b, level=1):
    terms = load_terms()
    pa, pb = ancestor_at_level(all_nodes[a], level), ancestor_at_level(all_nodes[b], level)
    la = {n["id"]: n["label"] for n in all_nodes[a]}; lb = {n["id"]: n["label"] for n in all_nodes[b]}
    table = Counter((la[pa[t["id"]]], lb[pb[t["id"]]]) for t in terms)
    dominant = {}
    for (x, y), c in table.items():
        if c > dominant.get(x, ("", 0))[1]:
            dominant[x] = (y, c)
    odd = [(t["term"], la[pa[t["id"]]], lb[pb[t["id"]]]) for t in terms if lb[pb[t["id"]]] != dominant[la[pa[t["id"]]]][0]]
    return dominant, odd


def main():
    allv = load_all(); n_terms = len(load_terms())
    allv_f = dict(allv, final=load_final())                       # підсумкова версія — для метрик та ARI
    res = {"metrics": {k: metrics(v, n_terms) for k, v in allv_f.items()}}
    res["kappa"], dis = kappa_table()
    res["ari"] = ari_table(allv)
    res["ari_final"] = {f"рівень {lv}": {k: adjusted_rand_score([ancestor_at_level(allv_f["final"], lv)[t["id"]] for t in load_terms()],
                                                                 [ancestor_at_level(allv[k], lv)[t["id"]] for t in load_terms()])
                                         for k in allv} for lv in (1, 2)}
    if "--json" in sys.argv:
        print(json.dumps(res, ensure_ascii=False, indent=1, default=float)); return
    print("== Метрики за версіями")
    keys = list(res["metrics"]["expert"])
    print(f"{'метрика':24}" + "".join(f"{k:>10}" for k in res["metrics"]))
    for k in keys:
        row = [res["metrics"][v][k] for v in res["metrics"]]
        print(f"{k:24}" + "".join(f"{(f'{x:.3f}' if isinstance(x, float) else str(x)):>10}" for x in row))
    print("\n== Вузли з єдиною дитиною")
    for v, nodes in allv.items():
        print(" ", v, single_child_nodes(nodes))
    print("\n== κ Коена (30 термінів; категорії = 8 вузлів рівня 1 експертної таксономії)")
    for k, v in res["kappa"].items():
        if isinstance(v, dict):
            print(f"  {k:36} κ = {v['kappa']:.3f}; збіг {v['agreement']:.0%}; n = {v['n']}")
    print("  розбіжності розмітника R1 з експертною таксономією:")
    for t, r, x in dis:
        print(f"    {t}: R1 = {r} | таксономія = {x}")
    print("\n== Скоригований індекс Ренда (ARI)")
    for lv, v in res["ari"].items():
        print(f"  {lv}: expert~llm = {v['expert~llm']:.3f}; expert~cluster = {v['expert~cluster']:.3f}; llm~cluster = {v['llm~cluster']:.3f}; кількість груп {v['k']}")
    print("\n== ARI підсумкової версії відносно трьох чернеток")
    for lv, v in res["ari_final"].items():
        print(f"  {lv}: " + "; ".join(f"final~{k} = {x:.3f}" for k, x in v.items()))
    print("  вузли з єдиною дитиною (final):", single_child_nodes(allv_f["final"]))
    for b in ("llm", "cluster"):
        dom, odd = contingency(allv, "expert", b)
        print(f"\n== Домінантна відповідність рівня 1: експертна → {b}")
        for x, (y, c) in sorted(dom.items()):
            print(f"  {x:40} → {y} ({c})")
        print(f"  терміни поза домінантною відповідністю: {len(odd)}")
        for t, x, y in odd:
            print(f"    {t}: expert={x} | {b}={y}")


if __name__ == "__main__":
    main()
