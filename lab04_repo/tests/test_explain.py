from engine.engine import Engine


def test_explain_shows_chain_and_sources():
    eng = Engine.from_file()
    res = eng.run({"variant.variant_type": "SNP", "variant.QD": 18.0, "variant.FS": 72.5, "variant.SOR": 2.2,
                   "variant.MQ": 58.0, "variant.at_exon_end": True})
    text = eng.explain(res, "variant.filter_status")
    assert "G14" in text and "G02" in text and "джерело" in text and "variant.FS > 60" in text


def test_explain_unknown_fact():
    eng = Engine.from_file()
    assert "не виведено" in eng.explain(eng.run({}), "relative.recommendation")
