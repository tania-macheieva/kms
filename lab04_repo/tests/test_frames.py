import pytest

from models.frames import (Dataset, Entity, IndelVariant, Patient, PREFIX_FRAMES, Proband, Relative, SNPVariant,
                           ValidationError, Variant, input_slots)
from models.instances import SAMPLE_INSTANCES
from engine.engine import Engine


def test_at_least_five_frames_and_two_inheritance_levels():
    assert len(PREFIX_FRAMES) >= 5
    assert [k.__name__ for k in Proband.__mro__[:5]] == ["Proband", "Patient", "Person", "Entity", "object"]
    assert issubclass(SNPVariant, Variant) and issubclass(Variant, Entity)


def test_ten_or_more_valid_instances():
    assert len(SAMPLE_INSTANCES) >= 10
    for prefix, inst in SAMPLE_INSTANCES:
        inst.validate()
        assert isinstance(inst, PREFIX_FRAMES.get(prefix, Entity)) or prefix == "variant"


def test_defaults_and_overridden_defaults():
    assert Variant(id="x").at_exon_end is False
    assert SNPVariant(id="x").variant_type == "SNP" and IndelVariant(id="x").variant_type == "INDEL"
    assert Patient(id="p").variant_known is False and Proband(id="p").variant_known is True      # перевизначено
    assert Relative(id="r").available is True


@pytest.mark.parametrize("make", [
    lambda: SNPVariant(id="x", QD=-1),                       # діапазон
    lambda: Variant(id="x", variant_type="MNP"),             # enum
    lambda: Dataset(id="x", large_variant_set="yes"),        # bool
    lambda: Relative(id="x", age=150),                       # діапазон успадковано від Person
    lambda: Relative(id="x", relationship="neighbour"),      # enum
    lambda: Proband(id="x", variant_gene="TP53"),            # enum
    lambda: Relative(),                                      # обов'язковий id
])
def test_invalid_instances_rejected(make):
    with pytest.raises(ValidationError):
        make()


def test_constraints_are_inherited():
    assert "age" in Proband.all_constraints() and "diagnosis" in Proband.all_constraints() and "id" in Proband.all_constraints()


def test_rule_uses_frame_slot_end_to_end():
    """Правило C06 читає слот Relative.age (факт relative.age), вхід формується з екземпляра фрейму."""
    rel = Relative(id="R-9", age=40, relationship="parent")
    facts = rel.to_facts("relative")
    assert facts["relative.age"] == 40
    res = Engine.from_file().run(facts)
    assert res.facts["relative.testing_age_status"] == "adult_eligible" and "C06" in res.fired


def test_all_rule_input_facts_are_frame_slots():
    import json
    from engine.engine import ROOT
    doc = json.loads((ROOT / "models" / "rules.json").read_text(encoding="utf-8"))
    derived = {e.get("set") or e.get("add") for r in doc["rules"] for e in r["then"]}
    used = {c["fact"] for r in doc["rules"] for c in r["if"] + r["exception"]}
    assert used - derived <= input_slots(), sorted(used - derived - input_slots())
