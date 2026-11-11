import math, numpy as np, pytest
from reco.eval import split, CUTOFF, DAYS, metrics_for, coverage, VAL_CUT
from reco.models import Popularity, GraphReco, KNNReco, Hybrid, recommend, _norm
from reco.data import eligible, allowed, AS_OF, age_days
def test_split_no_future_leakage(world):
    users, hist, roles, seen, pos = split(world.rows, world.items, CUTOFF, DAYS)
    assert users and all(d < CUTOFF for u in users for _, d in hist[u])
    for u in users: assert not (pos[u] & seen[u]) and pos[u]          # positives are new items read at/after the cut
    test_items = {world.items[i]["id"] for i in set().union(*(pos[u] for u in users))}; assert test_items
def test_popularity_uses_train_only(world):
    train = [r for r in world.rows if r[3] < CUTOFF]; test_only = {r[2] for r in world.rows if r[3] >= CUTOFF} - {r[2] for r in train}
    pop = Popularity(world.items, train); idx = {it["id"]: i for i, it in enumerate(world.items)}
    assert test_only and all(pop.cnt.get(idx[i], 0) == 0 for i in test_only)
def test_validation_window_precedes_test():
    assert VAL_CUT < CUTOFF < DAYS
def test_filters(world):
    it = world.items
    assert all(it[i]["sensitivity"] == "public" for i in eligible(it, "reader"))
    assert all(it[i]["verified"] for i in eligible(it, "clinician"))
    assert any(it[i]["sensitivity"] == "restricted" for i in eligible(it, "clinician")) and not any(it[i]["sensitivity"] == "restricted" for i in eligible(it, "analyst"))
    assert all(age_days(it[i], AS_OF) <= 20 for i in eligible(it, "analyst", max_age_days=20))
    assert len(eligible(it, "analyst", verified_only=False)) > len(eligible(it, "analyst"))
def test_recommend_excludes_seen_and_respects_role(world):
    pop = Popularity(world.items, world.rows); r = recommend(pop, world.items, "reader", [], 84, {0, 1, 2}, k=20)
    assert not {0, 1, 2} & set(r) and all(world.items[i]["sensitivity"] == "public" for i in r)
def test_hybrid_modes(world):
    items = world.items; pop = Popularity(items, world.rows); K = KNNReco(world.E, items); h = [(10, 80), (11, 82)]
    for mode in ("weighted", "rrf"):
        H = Hybrid(dict(knn=K, popularity=pop), dict(knn=1, popularity=0.3), mode); r = recommend(H, items, "reader", h, 84, {10, 11}, k=10); assert len(r) == 10 and len(set(r)) == 10
    a = recommend(Hybrid(dict(knn=K, popularity=pop), dict(knn=1, popularity=0), "weighted"), items, "reader", h, 84, {10, 11}, k=10); b = recommend(K, items, "reader", h, 84, {10, 11}, k=10); assert a == b
def test_graph_scores_from_cypher(world):
    items = world.items; G = GraphReco(world.G, items); idx = {it["id"]: i for i, it in enumerate(items)}; h = [(idx["sarek_vc_sarek#h007"], 84)]; comp = G.components(h, 84)
    assert comp and any(c["next"] > 0 for c in comp.values()) and any(c["ent"] > 0 for c in comp.values())
    c = idx["sarek_vc_sarek#h008"] if "sarek_vc_sarek#h008" in idx else None
    p = G.explain_path(recommend(G, items, "reader", h, 84, {h[0][0]}, k=1)[0], h, 84); assert p["kind"] in ("entity", "next", "doc")
def test_metrics_hand_example():
    class P: 
        def pop_share(self, i): return 0.5
    recs = {"u": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]}; pos = {"u": {2, 6}}; m = metrics_for(recs, pos, ["u"], P(), 100)
    assert m["p5"][0] == pytest.approx(1 / 5) and m["r5"][0] == pytest.approx(1 / 2)
    idcg = 1 + 1 / math.log2(3); dcg = 1 / math.log2(3) + 1 / math.log2(7); assert m["ndcg10"][0] == pytest.approx(dcg / idcg) and m["novelty"][0] == pytest.approx(1.0)
    assert coverage(recs, ["u"], 20) == pytest.approx(5 / 20)
def test_norm_constant():
    assert np.all(_norm(np.array([3.0, 3.0])) == 0)
