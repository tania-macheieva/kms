"""П'ять «пасток» — нетипових ситуацій, вигаданих LLM-експертом (Claude) для пошуку дефектів у правилах і рушії.
Очікування сформульовано за текстами джерел до запуску; результати — у docs/rules_analysis.md."""
import pytest

from engine.engine import Engine


def run(rules_path, facts, draft=False):
    return Engine.from_file(rules_path, include_draft=draft).run(facts)


BASE = {"variant.QD": 30.0, "variant.FS": 2.0, "variant.SOR": 1.0, "variant.MQ": 60.0}


def test_trap1_indel_with_moderate_fs_and_readpos(rules_path):
    """Пастка 1: INDEL із FS=150 і ReadPosRankSum=-15: за порогами для INDEL (200 і -20) відкидати не треба."""
    res = run(rules_path, {**BASE, "variant.variant_type": "INDEL", "variant.FS": 150.0, "variant.ReadPosRankSum": -15.0})
    assert "variant.flags" not in res.facts, f"хибно відкинуто: {res.facts.get('variant.flags')} правилами {res.fired}"


def test_trap2_nonmodel_organism_with_large_curated_set(rules_path):
    """Пастка 2: нестандартний організм, хоча набір великий і є відомі варіанти → hard filtering, а не VQSR."""
    res = run(rules_path, {"dataset.dataset_type": "non_model_organism", "dataset.large_variant_set": True,
                           "dataset.has_curated_known_variants": True})
    assert res.facts.get("dataset.filtering_method") == "hard_filtering", res.fired


@pytest.mark.xfail(strict=True, reason="відомий недолік монотонного ланцюжкування; усунено політикою: draft вимкнено за замовчуванням")
def test_trap3_draft_absence_rule_fires_too_early(rules_path):
    """Пастка 3: чернеткове G08 («немає прапорців → PASS») спрацьовує до того, як прапорці виведено."""
    res = run(rules_path, {**BASE, "variant.variant_type": "SNP", "variant.QD": 1.0}, draft=True)
    assert res.facts.get("variant.filter_status") == "FILTERED", f"отримано {res.facts.get('variant.filter_status')}, спрацювали {res.fired}"


def test_trap3_default_engine_has_no_premature_pass(rules_path):
    """Заходи до пастки 3: без чернеток (режим за замовчуванням) QD=1 дає FILTERED і ніколи PASS."""
    res = run(rules_path, {**BASE, "variant.variant_type": "SNP", "variant.QD": 1.0})
    assert res.facts.get("variant.filter_status") == "FILTERED"


def test_trap4_minor_with_risk_but_relative_unavailable(rules_path):
    """Пастка 4: 17 років + дитячий ризик + родич недоступний: вік дозволяє тест, але черга — «наступний найближчий»."""
    res = run(rules_path, {"proband.variant_gene": "BRCA1", "proband.variant_known": True,
                           "proband.variant_childhood_cancer_risk": True, "relative.relationship": "child",
                           "relative.age": 17, "relative.available": False, "relative.wants_testing": True})
    assert res.facts["relative.testing_age_status"] == "testing_appropriate"
    assert res.facts["relative.testing_order"] == "next_closest_available"
    assert "relative.recommendation" not in res.facts          # першої черги немає → пропозиції немає


def test_trap5_user_supplies_contradicting_derived_fact(rules_path):
    """Пастка 5: користувач вручну вказав filter_status=PASS, але QD=1 дає LowQD → суперечність має бути позначена
    як НЕрозв'язана (потрібен погляд людини), а не тихо проігнорована."""
    res = run(rules_path, {**BASE, "variant.variant_type": "SNP", "variant.QD": 1.0, "variant.filter_status": "PASS"})
    assert any(c["fact"] == "variant.filter_status" for c in res.unresolved_conflicts), res.conflicts


def test_trap_exception_with_custom_thresholds_blocks_review(rules_path):
    """Додатково: власні пороги + екзонний кінець + FS=100 → ні прапорців, ні REVIEW."""
    res = run(rules_path, {**BASE, "variant.variant_type": "SNP", "variant.FS": 100.0, "variant.at_exon_end": True,
                           "dataset.custom_thresholds": True})
    assert "variant.flags" not in res.facts and "variant.filter_status" not in res.facts
