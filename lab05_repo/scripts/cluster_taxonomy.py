"""Кластерна таксономія: embeddings (spaCy en_core_web_md 3.8.0, 300-вимірні статичні вектори) + агломеративна кластеризація
(Ward) → models/tax_cluster.csv.

Текст для embedding: канонічний термін + англомовні alt_labels (визначення українською, а модель англомовна, тому не використовуються).
Дерево: корінь → K1 крупних кластерів → K2 підкластерів → терміни (дві частини однієї дендрограми, тому вкладені).
Назви кластерів: пропонує LLM (data/cluster_names.json), затверджує студент; без файлу — тимчасові назви C1-n.
Запуск: python scripts/cluster_taxonomy.py [--show]   (seed фіксований; Ward детермінований, seed потрібен лише для numpy)
"""
import csv
import json
import sys
from pathlib import Path

import numpy as np
import spacy
from scipy.cluster.hierarchy import fcluster, linkage

ROOT = Path(__file__).resolve().parent.parent
SEED, K1, K2 = 42, 9, 30
np.random.seed(SEED)


def embed(terms):
    nlp = spacy.load("en_core_web_md")
    vecs, oov = [], []
    for t in terms:
        text = " ".join([t["term"]] + [a for a in t["alt_labels"].split(";") if a])
        toks = [x for x in nlp(text) if x.has_vector and not x.is_punct]
        if not toks:
            oov.append(t["term"]); vecs.append(np.zeros(300)); continue
        vecs.append(np.mean([x.vector for x in toks], axis=0))
    v = np.array(vecs)
    norms = np.linalg.norm(v, axis=1, keepdims=True)
    return v / np.where(norms == 0, 1, norms), oov, nlp.meta["version"]


def main():
    terms = list(csv.DictReader(open(ROOT / "models/terms.csv", encoding="utf-8-sig")))
    X, oov, ver = embed(terms)
    Z = linkage(X, method="ward")
    c1, c2 = fcluster(Z, K1, "maxclust"), fcluster(Z, K2, "maxclust")
    names_path = ROOT / "data/cluster_names.json"
    names = json.loads(names_path.read_text(encoding="utf-8")) if names_path.exists() else {}
    groups = {}
    for t, a, b in zip(terms, c1, c2):
        groups.setdefault((int(a), int(b)), []).append(t)
    if "--show" in sys.argv:
        for (a, b), ts in sorted(groups.items()):
            print(f"{a}.{b}: " + "; ".join(t["term"] for t in ts))
        print("OOV:", oov)
        return
    rows = [{"id": "K000", "parent_id": "", "label": "Biomedical data analysis (clusters)", "level": 0, "term_id": ""}]
    top_ids, sub_ids = {}, {}
    for (a, b), ts in sorted(groups.items()):
        if a not in top_ids:
            top_ids[a] = f"K{a:02d}"
            rows.append({"id": top_ids[a], "parent_id": "K000", "label": names.get(f"{a}", f"C{a}"), "level": 1, "term_id": ""})
        sid = f"K{a:02d}{b:02d}"
        sub_ids[(a, b)] = sid
        rows.append({"id": sid, "parent_id": top_ids[a], "label": names.get(f"{a}.{b}", f"C{a}.{b}"), "level": 2, "term_id": ""})
        for t in ts:
            rows.append({"id": f"K{t['id']}", "parent_id": sid, "label": t["term"], "level": 3, "term_id": t["id"]})
    with open(ROOT / "models/tax_cluster.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, list(rows[0])); w.writeheader(); w.writerows(rows)
    print(f"spaCy en_core_web_md {ver}; numpy {np.__version__}; seed {SEED}; K1={K1}, K2={K2}")
    print(f"вузлів {len(rows)}; термінів без вектора (OOV): {len(oov)} {oov}")


if __name__ == "__main__":
    main()
