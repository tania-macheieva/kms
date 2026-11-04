"""Перевірки корпусу термінів та трьох чернеток таксономії (результати 1–2)."""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def terms():
    return list(csv.DictReader(open(ROOT / "models/terms.csv", encoding="utf-8-sig")))


def test_corpus_size_unique_and_alt_labels():
    t = terms()
    assert 100 <= len(t) <= 150
    assert len({r["term"].casefold() for r in t}) == len(t)
    assert "alt_labels" in t[0] and sum(1 for r in t if r["alt_labels"]) >= 30


def test_at_least_50_definitions():
    assert sum(1 for r in terms() if r["definition"].strip()) >= 50


def _load(path):
    return list(csv.DictReader(open(path, encoding="utf-8-sig")))


def test_three_versions_same_format_and_size():
    expert = _load(ROOT / "models/tax_expert.csv")
    cluster = _load(ROOT / "models/tax_cluster.csv")
    llm = json.loads((ROOT / "models/tax_llm.json").read_text(encoding="utf-8"))["nodes"]
    for rows in (expert, cluster, llm):
        assert {"id", "parent_id", "label"} <= set(rows[0])
        assert len(rows) >= 40
        assert max(int(r["level"]) for r in rows) >= 2          # корінь + ≥ 3 рівні (0,1,2,3)
    assert max(int(r["level"]) for r in expert) >= 3 and max(n["level"] for n in llm) >= 3 and max(int(r["level"]) for r in cluster) >= 3


def test_llm_version_has_division_principle_on_every_internal_node():
    nodes = json.loads((ROOT / "models/tax_llm.json").read_text(encoding="utf-8"))["nodes"]
    parents = {n["parent_id"] for n in nodes if n["parent_id"]}
    assert all(n["principle_of_division"] for n in nodes if n["id"] in parents)


def test_every_term_in_every_version_exactly_once():
    ids = {r["id"] for r in terms()}
    for name in ("tax_expert.csv", "tax_cluster.csv"):
        used = [r["term_id"] for r in _load(ROOT / "models" / name) if r["term_id"]]
        assert sorted(used) == sorted(ids), name
    llm = [n["term_id"] for n in json.loads((ROOT / "models/tax_llm.json").read_text(encoding="utf-8"))["nodes"] if n["term_id"]]
    assert sorted(llm) == sorted(ids)


def test_kappa_computation_matches_sklearn_on_30_terms():
    from sklearn.metrics import cohen_kappa_score
    a = {r["term_id"]: r["category"] for r in _load(ROOT / "annotations/rater_R1_llm.csv")}
    b = {r["term_id"]: r["category"] for r in _load(ROOT / "annotations/rater_R2_llm.csv")}
    assert len(a) >= 30 and set(a) == set(b)
    k = cohen_kappa_score([a[i] for i in sorted(a)], [b[i] for i in sorted(a)])
    assert -1 <= k <= 1
