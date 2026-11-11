from reco.explain import facts_of, template, check, verify_path, tamper_test, TAMPER
from reco.models import GraphReco, recommend
def _fact(world):
    items = world.items; idx = {it["id"]: i for i, it in enumerate(items)}; G = GraphReco(world.G, items); h = [(idx["sarek_vc_sarek#h007"], 84)]; c = recommend(G, items, "reader", h, 84, {h[0][0]}, k=1)[0]
    return facts_of(items, c, G.explain_path(c, h, 84))
def test_template_passes_and_path_exists(world):
    f = _fact(world); assert check(template(f), f)[0] and verify_path(world.G, world.E, world.items, f)
def test_tampered_explanations_rejected(world):
    f = _fact(world); t = template(f)
    for k, fn in TAMPER.items():
        bad = fn(t, f)
        if bad != t: assert not check(bad, f)[0], k
def test_fake_path_rejected(world):
    f = dict(_fact(world)); f["kind"] = "entity"; f["entity"] = "BRCA1"; f["etype"] = "Gene"; f["via"] = "sarek_vc_sarek#h007"; f["cand"] = "rare_readme#h001"
    assert not verify_path(world.G, world.E, world.items, f)
def test_extra_entity_rejected(world):
    f = _fact(world); assert not check(template(f) + " Також це стосується Mutect2 та BRCA1.", f)[0]
