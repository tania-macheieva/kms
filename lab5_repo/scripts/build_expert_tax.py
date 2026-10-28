"""Експертна таксономія (ручне групування за явними принципами поділу) → models/tax_expert.csv.

Формат вузла: label, [діти]. Рядок = термін із корпусу; кортеж (назва, принцип, [діти]) = допоміжна категорія з принципом поділу.
Допоміжні категорії не є термінами корпусу. Інстанси (BRCA1, BRCA2 під gene; GO, HPO, MeSH, SNOMED CT під типом словника)
трактуються як вужчі поняття (SKOS broader), що є стандартною практикою.
"""
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "data"))
from curation import T                                          # noqa: E402

TERMS = {t[0] for t in T}


def C(label, principle, children):
    return (label, principle, children)


def N(term, *kids, p="вужче поняття (is-a)"):                  # вузол-термін з дітьми-термінами та принципом поділу
    return (term, p, list(kids))


TREE = C("Biomedical data analysis", "тип сутності предметної області: що саме це поняття є", [
    C("Biological entity", "рівень організації: елементи геному / білкові сутності", [
        C("Genomic element", "роль у структурі геному", [
            "genome", "chromosome", N("gene", "BRCA1", "BRCA2", p="конкретний ген (екземпляр класу)"), "exon", "intron", "allele", "exome",
            "transcript", "transcriptome"]),
        C("Protein-level entity", "ступінь складності молекулярної сутності", [
            "amino acid", "peptide", N("protein", "protein domain", p="структурна складова білка"), "proteome"]),
    ]),
    C("Genetic variation", "аспект характеристики варіації: молекулярний тип / походження / клінічна значущість", [
        N("genetic variant", "single nucleotide polymorphism", "insertion-deletion", "structural variant",
          "copy number variation", "mutation", p="молекулярний тип зміни"),
        C("Variant by origin", "походження варіанта", ["germline variant", "somatic variant"]),
        C("Variant by clinical significance", "доведена клінічна значущість варіанта",
          ["pathogenic variant", "benign variant", "variant of uncertain significance"]),
    ]),
    C("Biological property", "що описує властивість: спадковість / молекулярна активність", [
        C("Heredity", "прояв і передача ознаки", ["genotype", "phenotype", "penetrance", "autosomal dominant inheritance"]),
        C("Molecular activity", "тип молекулярної активності", ["gene expression", "DNA methylation",
                                                               "post-translational modification", "protein-protein interaction",
                                                               "protein abundance"]),
    ]),
    C("Method and procedure", "сфера застосування: лабораторна / обчислювальна / клінічна / наукова дисципліна", [
        C("Laboratory method", "що аналізується: нуклеїнові кислоти / білки / зразки", [
            N("DNA sequencing", "next-generation sequencing", "whole genome sequencing", "whole exome sequencing",
              "RNA sequencing", p="охоплення й мішень секвенування"),
            N("mass spectrometry", "tandem mass spectrometry", p="наявність фрагментації іонів"), "laboratory test"]),
        C("Computational procedure", "етап обробки даних", [
            "sequence alignment", "variant calling", "variant annotation",
            N("variant filtering", "hard filtering", "variant quality score recalibration", p="спосіб встановлення порогів"), "protein identification"]),
        C("Clinical procedure", "етап клінічного процесу", [
            N("genetic testing", "cascade testing", p="коло тестованих осіб"), "genetic counseling", "risk assessment", "treatment", "clinical trial"]),
        C("Research field", "об'єкт вивчення", ["genomics", "proteomics", "epigenetics"]),
    ]),
    C("Data and artifact", "природа даних: сирі / клінічні / службові", [
        C("Sequencing data", "стадія обробки послідовностей", ["sequencing read", "FASTQ file", "BAM file", "VCF file",
                                                              "reference genome", "gene panel"]),
        C("Proteomic data", "тип вимірювань", ["mass spectrum"]),
        C("Clinical data", "тип клінічного запису", ["electronic health record", "clinical note", "family history"]),
        C("Data about data", "що описується", ["metadata", "data schema", "data provenance"]),
    ]),
    C("Measure of quality", "об'єкт оцінювання: варіант / набір даних", [
        C("Variant call annotation", "виміряна ознака підтримки варіанта", ["quality by depth", "Fisher strand bias",
                                                                          "strand odds ratio", "mapping quality", "read depth",
                                                                          "rank sum test"]),
        "data quality",
    ]),
    C("Clinical concept", "роль у клінічній ситуації: людина / стан / терапія / захист", [
        C("Person", "роль особи в генетичному дослідженні родини", [N("patient", "proband", p="роль у родинному дослідженні"), "relative"]),
        C("Condition", "тип клінічного стану", ["diagnosis", "symptom", N("hereditary cancer", "breast cancer", "ovarian cancer", p="локалізація пухлини"),
                                               "biomarker"]),
        C("Therapeutic agent", "тип втручання", [N("PARP inhibitor", p="клас препарату")]),
        C("Ethical and legal safeguard", "тип гарантії", ["informed consent", "de-identification", "data privacy"]),
    ]),
    C("Knowledge and information technology", "роль в інженерії знань: організація / зберігання / подання / виведення", [
        C("Knowledge organization system", "рівень формалізації", [
            N("ontology", "Gene Ontology", "Human Phenotype Ontology", p="предмет онтології"),
            N("controlled vocabulary", "Medical Subject Headings", "SNOMED CT", p="призначення словника"), "thesaurus", "taxonomy", "knowledge graph"]),
        C("Data resource", "тип ресурсу", ["ClinVar", "UniProt", "dbSNP"]),
        C("Database technology", "модель даних", ["relational database", "graph database", "vector database"]),
        C("Representation and similarity", "що робить з даними: подає / порівнює", [
            "embedding", "semantic similarity", "nearest neighbor search", "Resource Description Framework",
            "Simple Knowledge Organization System", "SPARQL"]),
        C("Knowledge engineering", "елемент системи на знаннях", [N("rule-based system", "production rule", "inference engine", p="складова системи на правилах"),
                                                                  "frame", "competency question"]),
        C("Data engineering", "етап роботи з даними", ["data integration", "data pipeline"]),
    ]),
])


def flatten(tree):
    rows, counter = [], [0]
    term_id = {t[0]: i for i, t in enumerate(sorted(T, key=lambda t: t[0].casefold()), 1)}

    def add(node, parent, level):
        counter[0] += 1
        nid = f"E{counter[0]:03d}"
        if isinstance(node, str):
            label, principle, kids = node, "", []
        else:
            label, principle, kids = node
        tid = f"T{term_id[label]:03d}" if label in TERMS else ""
        rows.append({"id": nid, "parent_id": parent, "label": label, "level": level, "principle": principle or "",
                     "term_id": tid, "is_term": "1" if tid else "0"})
        for k in kids:
            add(k, nid, level + 1)

    add(tree, "", 0)
    return rows


def main():
    rows = flatten(TREE)
    used = [r["label"] for r in rows if r["is_term"] == "1"]
    missing, dup = TERMS - set(used), {u for u in used if used.count(u) > 1}
    assert not missing and not dup, (sorted(missing), dup)
    out = ROOT / "models/tax_expert.csv"
    with open(out, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, list(rows[0])); w.writeheader(); w.writerows(rows)
    print(f"вузлів: {len(rows)}; термінів: {len(used)}; допоміжних категорій: {len(rows) - len(used)}; макс. рівень: {max(r['level'] for r in rows)}")


if __name__ == "__main__":
    main()
