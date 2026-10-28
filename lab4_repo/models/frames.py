"""Фрейми предметної області: геномні варіанти, набори даних та каскадне тестування родичів.

Ієрархія наслідування (is-a):

    Entity                      (id, source, version)
    ├── Variant                 (варіант і його анотації GATK)
    │   ├── SNPVariant          (variant_type за замовчуванням SNP)
    │   └── IndelVariant        (variant_type за замовчуванням INDEL)
    ├── Dataset                 (набір даних і спосіб фільтрації)
    ├── FilterRequest           (запит користувача на фільтрацію)
    ├── GeneticTest             (генетичний тест)
    ├── TestOffer               (пропозиція тестування)
    └── Person                  (вік)
        ├── Patient             (діагноз, сімейний анамнез)
        │   └── Proband         (носій відомої зміни: ген, ризик у дитинстві)
        └── Relative            (родич пробанда)

Слоти фреймів — це ті самі факти, якими оперують правила з models/rules.json:
факт `variant.QD` = слот `QD` фрейму `Variant`, факт `relative.age` = слот `age` фрейму `Relative` тощо
(відповідність префікс → фрейм — у PREFIX_FRAMES).
"""
from __future__ import annotations

from dataclasses import dataclass, fields
from typing import Any, ClassVar, Dict, Optional


class ValidationError(ValueError):
    """Порушення обмеження слота."""


def _is_number(x: Any) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool)


@dataclass(kw_only=True)
class Entity:
    """Кореневий фрейм: ідентифікація, джерело й версія запису."""
    id: str = ""
    source: Optional[str] = None
    version: int = 1

    # Обмеження слотів: ("enum", {значення}) | ("range", мін, макс) | ("bool",) | ("required",)
    CONSTRAINTS: ClassVar[Dict[str, tuple]] = {
        "id": ("required",),
        "version": ("range", 1, 10_000),
    }

    @classmethod
    def all_constraints(cls) -> Dict[str, tuple]:
        merged: Dict[str, tuple] = {}
        for klass in reversed(cls.__mro__):          # від кореня до нащадка: нащадок перевизначає
            merged.update(getattr(klass, "CONSTRAINTS", {}))
        return merged

    @classmethod
    def slot_names(cls):
        return [f.name for f in fields(cls)]

    def __post_init__(self) -> None:
        self.validate()

    def validate(self) -> None:
        for slot, spec in self.all_constraints().items():
            value = getattr(self, slot, None)
            kind = spec[0]
            if kind == "required":
                if value in (None, ""):
                    raise ValidationError(f"{type(self).__name__}.{slot}: обов'язковий слот не заповнено")
                continue
            if value is None:
                continue                                  # необов'язковий слот
            if kind == "enum" and value not in spec[1]:
                raise ValidationError(f"{type(self).__name__}.{slot}={value!r}: допустимо {sorted(spec[1])}")
            if kind == "range":
                if not _is_number(value) or not (spec[1] <= value <= spec[2]):
                    raise ValidationError(f"{type(self).__name__}.{slot}={value!r}: очікується число в [{spec[1]}; {spec[2]}]")
            if kind == "bool" and not isinstance(value, bool):
                raise ValidationError(f"{type(self).__name__}.{slot}={value!r}: очікується true/false")

    def to_facts(self, prefix: str) -> Dict[str, Any]:
        """Слоти → плоскі факти `prefix.slot` для рушія (порожні слоти пропускаються)."""
        return {f"{prefix}.{name}": getattr(self, name) for name in self.slot_names()
                if getattr(self, name) is not None}


# --------------------------- варіанти ---------------------------
@dataclass(kw_only=True)
class Variant(Entity):
    """Генетичний варіант і анотації GATK, які використовує жорстка фільтрація."""
    variant_type: Optional[str] = None
    QD: Optional[float] = None
    FS: Optional[float] = None
    SOR: Optional[float] = None
    MQ: Optional[float] = None
    MQRankSum: Optional[float] = None
    ReadPosRankSum: Optional[float] = None
    at_exon_end: bool = False                             # значення за замовчуванням

    CONSTRAINTS: ClassVar[Dict[str, tuple]] = {
        "variant_type": ("enum", {"SNP", "INDEL"}),
        "QD": ("range", 0, 1000), "FS": ("range", 0, 10_000), "SOR": ("range", 0, 1000),
        "MQ": ("range", 0, 100), "MQRankSum": ("range", -100, 100), "ReadPosRankSum": ("range", -100, 100),
        "at_exon_end": ("bool",),
    }


@dataclass(kw_only=True)
class SNPVariant(Variant):
    variant_type: Optional[str] = "SNP"                   # перевизначене значення за замовчуванням


@dataclass(kw_only=True)
class IndelVariant(Variant):
    variant_type: Optional[str] = "INDEL"


# --------------------------- набір даних і запит ---------------------------
@dataclass(kw_only=True)
class Dataset(Entity):
    dataset_type: Optional[str] = None
    large_variant_set: bool = False
    has_curated_known_variants: bool = False
    custom_thresholds: bool = False                       # користувач уточнив пороги за власними розподілами

    CONSTRAINTS: ClassVar[Dict[str, tuple]] = {
        "dataset_type": ("enum", {"whole_genome", "exome", "small_gene_panel", "non_model_organism"}),
        "large_variant_set": ("bool",), "has_curated_known_variants": ("bool",), "custom_thresholds": ("bool",),
    }


@dataclass(kw_only=True)
class FilterRequest(Entity):
    filter_basis: Optional[str] = None

    CONSTRAINTS: ClassVar[Dict[str, tuple]] = {
        "filter_basis": ("enum", {"QD", "FS", "SOR", "MQ", "MQRankSum", "ReadPosRankSum", "QUAL", "DP"}),
    }


# --------------------------- тест і пропозиція ---------------------------
@dataclass(kw_only=True)
class GeneticTest(Entity):
    test_type: Optional[str] = None
    includes_family_variant: Optional[bool] = None
    ordered_for_relative: bool = False

    CONSTRAINTS: ClassVar[Dict[str, tuple]] = {
        "test_type": ("enum", {"family_variant_specific", "generic_cancer_panel"}),
        "includes_family_variant": ("bool",), "ordered_for_relative": ("bool",),
    }


@dataclass(kw_only=True)
class TestOffer(Entity):
    __test__ = False                                      # щоб pytest не сприймав клас як тестовий
    time_limited: bool = False

    CONSTRAINTS: ClassVar[Dict[str, tuple]] = {"time_limited": ("bool",)}


# --------------------------- люди ---------------------------
@dataclass(kw_only=True)
class Person(Entity):
    age: Optional[int] = None

    CONSTRAINTS: ClassVar[Dict[str, tuple]] = {"age": ("range", 0, 120)}


DIAGNOSES = {"breast_cancer_female", "breast_cancer_male", "ovarian_cancer", "peritoneal_cancer",
             "fallopian_tube_cancer", "other"}


@dataclass(kw_only=True)
class Patient(Person):
    diagnosis: Optional[str] = None
    family_member_with_cancer: bool = False
    variant_known: bool = False                           # за замовчуванням зміна невідома

    CONSTRAINTS: ClassVar[Dict[str, tuple]] = {
        "diagnosis": ("enum", DIAGNOSES),
        "family_member_with_cancer": ("bool",), "variant_known": ("bool",),
    }


@dataclass(kw_only=True)
class Proband(Patient):
    """Пацієнт із відомою спадковою зміною (четвертий рівень: Entity → Person → Patient → Proband)."""
    variant_gene: Optional[str] = None
    variant_known: bool = True                            # перевизначене значення за замовчуванням
    variant_childhood_cancer_risk: bool = False

    CONSTRAINTS: ClassVar[Dict[str, tuple]] = {
        "variant_gene": ("enum", {"BRCA1", "BRCA2", "other"}),
        "variant_childhood_cancer_risk": ("bool",),
    }


RELATIONSHIPS = {"parent", "child", "full_sibling", "half_sibling", "sibling", "aunt_uncle",
                 "grandparent", "cousin", "other_distant", "friend"}


@dataclass(kw_only=True)
class Relative(Person):
    relationship: Optional[str] = None
    available: bool = True                                # за замовчуванням родич доступний для тестування
    wants_testing: bool = False

    CONSTRAINTS: ClassVar[Dict[str, tuple]] = {
        "relationship": ("enum", RELATIONSHIPS),
        "available": ("bool",), "wants_testing": ("bool",),
    }


PREFIX_FRAMES = {
    "variant": Variant, "dataset": Dataset, "request": FilterRequest, "relative": Relative,
    "patient": Patient, "proband": Proband, "test": GeneticTest, "offer": TestOffer,
}


def input_slots() -> set:
    """Усі факти, які можуть надходити як вхідні дані (слоти фреймів з префіксами)."""
    return {f"{p}.{s}" for p, cls in PREFIX_FRAMES.items() for s in cls.slot_names()}
