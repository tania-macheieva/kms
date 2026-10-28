"""Експертна концептуальна карта v1 (ручне складання за фокусним питанням) → models/cmap_expert.{json,drawio,png}.
Поняття — зі словника ЛР5 (таксономія), відношення — лише з каталогу data/relations.json."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from map_tools import REL, ROOT, render_png, stats, taxonomy_info, to_drawio   # noqa: E402

TAX = taxonomy_info()
G = ["genetic variant", "single nucleotide polymorphism", "insertion-deletion", "germline variant", "pathogenic variant", "gene",
     "BRCA1", "BRCA2", "gene panel", "VCF file", "BAM file", "variant calling", "sequence alignment"]
Q = ["variant filtering", "hard filtering", "variant quality score recalibration", "quality by depth", "Fisher strand bias",
     "strand odds ratio", "mapping quality", "rank sum test", "read depth", "exon"]
C = ["hereditary cancer", "breast cancer", "ovarian cancer", "proband", "relative", "family history", "genetic testing",
     "cascade testing", "genetic counseling", "risk assessment"]
INST = {  # екземпляр: (клас, кластер, визначення)
    "QD < 2": ("quality by depth", "Q", "Порогове значення з рекомендацій GATK: варіанти з QD нижче 2 відкидають."),
    "FS > 60 (SNP)": ("Fisher strand bias", "Q", "Рекомендований поріг GATK для SNP: FS вище 60."),
    "SOR > 3": ("strand odds ratio", "Q", "Рекомендований поріг GATK: SOR вище 3."),
    "MQ < 40": ("mapping quality", "Q", "Рекомендований поріг GATK: MQ нижче 40."),
    "рідний брат/сестра: 50%": ("relative", "C", "Рідні брати й сестри пробанда з BRCA1/BRCA2 мають шанс 1 з 2 успадкувати ту саму зміну."),
    "двоюрідний родич: до 12,5%": ("relative", "C", "Двоюрідні родичі мають шанс до 1 з 8 мати ту саму зміну."),
}
PROPS = [  # (s, p, o, cross, explanation)
    ("single nucleotide polymorphism", "is_a", "genetic variant"), ("insertion-deletion", "is_a", "genetic variant"),
    ("germline variant", "is_a", "genetic variant"), ("pathogenic variant", "is_a", "genetic variant"),
    ("BRCA1", "is_a", "gene"), ("BRCA2", "is_a", "gene"), ("gene", "part_of", "gene panel"),
    ("sequence alignment", "produces", "BAM file"), ("variant calling", "uses_input", "BAM file"),
    ("variant calling", "produces", "VCF file"), ("variant calling", "detects", "genetic variant"),
    ("genetic variant", "has_annotation", "quality by depth"), ("genetic variant", "has_annotation", "Fisher strand bias"),
    ("genetic variant", "has_annotation", "strand odds ratio"), ("genetic variant", "has_annotation", "mapping quality"),
    ("hard filtering", "is_a", "variant filtering"), ("variant quality score recalibration", "is_a", "variant filtering"),
    ("variant filtering", "applies_to", "VCF file", True, "Поєднує кластер контролю якості з файлами результатів виклику варіантів: фільтрація працює над VCF."),
    ("hard filtering", "uses_input", "quality by depth"), ("hard filtering", "uses_input", "Fisher strand bias"),
    ("hard filtering", "uses_input", "strand odds ratio"), ("hard filtering", "uses_input", "mapping quality"),
    ("hard filtering", "uses_input", "rank sum test"), ("rank sum test", "applies_to", "mapping quality"),
    ("quality by depth", "uses_input", "read depth"), ("strand odds ratio", "recommended_for", "exon"),
    ("hard filtering", "recommended_for", "gene panel", True, "Поєднує контроль якості з типом тесту: для малих панелей (і немодельних організмів) доводиться використовувати hard filtering."),
    ("variant quality score recalibration", "requires", "genetic variant"),
    ("breast cancer", "is_a", "hereditary cancer"), ("ovarian cancer", "is_a", "hereditary cancer"),
    ("pathogenic variant", "increases_risk_of", "hereditary cancer", True, "Зв'язує геномну гілку з клінічною: патогенний варіант (BRCA1/BRCA2) підвищує ризик спадкового раку."),
    ("BRCA1", "increases_risk_of", "breast cancer"), ("BRCA2", "increases_risk_of", "ovarian cancer"),
    ("relative", "is_kin_of", "proband"),
    ("genetic testing", "detects", "pathogenic variant", True, "Клінічне тестування виявляє той самий тип варіантів, що аналізують у геномному конвеєрі."),
    ("cascade testing", "is_a", "genetic testing"), ("cascade testing", "applies_to", "relative"),
    ("cascade testing", "requires", "pathogenic variant", True, "Каскадне тестування можливе лише коли в пробанда вже відомий патогенний варіант."),
    ("genetic counseling", "recommended_for", "relative"), ("genetic counseling", "uses_input", "family history"),
    ("risk assessment", "uses_input", "family history"), ("risk assessment", "applies_to", "proband"),
    ("genetic testing", "applies_to", "proband"),
]


def build():
    ids, concepts = {}, []
    for cl, names in (("G", G), ("Q", Q), ("C", C)):
        for n in names:
            ids[n] = f"M{len(ids) + 1:02d}"
            concepts.append({"id": ids[n], "label": n, "kind": "concept", "cluster": cl, "type": TAX[n]["type"], "definition": TAX[n]["definition"]})
    props = []
    for n, (cls, cl, definition) in INST.items():
        ids[n] = f"I{len([k for k in ids if k in INST]) + 1:02d}"
        concepts.append({"id": ids[n], "label": n, "kind": "instance", "cluster": cl, "type": TAX[cls]["type"], "definition": definition})
        props.append((cls, "has_example", n))
    allp = list(PROPS) + props
    out = [{"id": f"P{i + 1:02d}", "s": ids[t[0]], "p": t[1], "o": ids[t[2]], "cross": len(t) > 3 and bool(t[3]),
            "explanation": t[4] if len(t) > 4 else ""} for i, t in enumerate(allp)]
    assert all(p["p"] in REL for p in out)
    return {"title": "Експертна концептуальна карта v1", "focus_question_file": "docs/cmap_focus.md", "concepts": concepts, "propositions": out}


if __name__ == "__main__":
    m = build()
    (ROOT / "models/cmap_expert.json").write_text(json.dumps(m, ensure_ascii=False, indent=1), encoding="utf-8")
    render_png(m, ROOT / "models/cmap_expert.png", "Експертна концептуальна карта v1")
    to_drawio(m, ROOT / "models/cmap_expert.drawio", "Експертна концептуальна карта v1")
    print(json.dumps(stats(m), ensure_ascii=False))
