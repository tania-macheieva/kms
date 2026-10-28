"""Підсумкова таксономія (гібрид) → models/taxonomy_final.csv.

Основа — експертна версія (найкращі структура й принципи поділу, див. docs/taxonomy_eval.md); із LLM-версії запозичено окрему
гілку «Research field» та віднесення allele до варіації; кластерна версія підтвердила групу технологій секвенування й дала
кілька гіпотез, відхилених через артефакти усереднених векторів. Рішення щодо кожної розбіжності — у docs/taxonomy_eval.md (розділ 5).
Допоміжні категорії мають визначення нижче; терміни беруть визначення й alt_labels із models/terms.csv.
"""
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from build_expert_tax import C, N                                   # noqa: E402
from taxlib import load_terms                                       # noqa: E402

TREE = C("Biomedical data analysis", "тип сутності предметної області: що саме це поняття є", [
    C("Biological entity", "рівень організації: елементи геному / білкові сутності", [
        C("Genomic element", "роль у структурі геному", [
            "genome", "chromosome", N("gene", "BRCA1", "BRCA2", p="конкретний ген (екземпляр класу)"), "exon", "intron", "exome",
            "transcript", "transcriptome", "gene panel"]),
        C("Protein-level entity", "ступінь складності молекулярної сутності",
          ["amino acid", "peptide", "protein", "protein domain", "proteome"]),
    ]),
    C("Genetic variation", "аспект характеристики варіації: молекулярний тип / походження / клінічна значущість", [
        N("genetic variant", "single nucleotide polymorphism", "insertion-deletion", "structural variant",
          "copy number variation", "mutation", "allele", p="молекулярний тип зміни"),
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
    C("Method and procedure", "сфера застосування: лабораторна / обчислювальна / клінічна", [
        C("Laboratory method", "що аналізується: нуклеїнові кислоти / білки / зразки", [
            N("DNA sequencing", "next-generation sequencing", "whole genome sequencing", "whole exome sequencing",
              "RNA sequencing", p="охоплення й мішень секвенування"),
            N("mass spectrometry", "tandem mass spectrometry", p="наявність фрагментації іонів"), "laboratory test"]),
        C("Computational procedure", "етап обробки даних (порядок робочого процесу)", [
            "sequence alignment", "variant calling", "variant annotation",
            N("variant filtering", "hard filtering", "variant quality score recalibration", p="спосіб встановлення порогів"),
            "protein identification", "nearest neighbor search"]),
        C("Clinical procedure", "етап клінічного процесу", [
            N("genetic testing", "cascade testing", p="коло тестованих осіб"), "genetic counseling", "risk assessment",
            "clinical trial"]),
    ]),
    C("Research field", "об'єкт вивчення", ["genomics", "proteomics", "epigenetics"]),
    C("Data and artifact", "природа даних: сирі / клінічні / службові", [
        C("Omics data", "тип омікс-даних і стадія обробки", ["sequencing read", "FASTQ file", "BAM file", "VCF file",
                                                           "reference genome", "mass spectrum"]),
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
        C("Condition", "тип клінічного стану", ["diagnosis", "symptom",
                                               N("hereditary cancer", "breast cancer", "ovarian cancer", p="локалізація пухлини"),
                                               "biomarker"]),
        C("Therapy", "вид терапевтичного поняття: загальне / лікарський засіб", ["treatment", "PARP inhibitor"]),
        C("Ethical and legal safeguard", "тип гарантії", ["informed consent", "de-identification", "data privacy"]),
    ]),
    C("Knowledge and information technology", "роль в інженерії знань: організація / зберігання / подання / виведення", [
        C("Knowledge organization system", "рівень формалізації", [
            N("ontology", "Gene Ontology", "Human Phenotype Ontology", p="предмет онтології"),
            N("controlled vocabulary", "Medical Subject Headings", "SNOMED CT", p="призначення словника"),
            "thesaurus", "taxonomy", "knowledge graph"]),
        C("Data resource", "тип ресурсу", ["ClinVar", "UniProt", "dbSNP"]),
        C("Database technology", "модель даних", ["relational database", "graph database", "vector database"]),
        C("Representation and similarity", "що робить з даними: подає / порівнює", [
            "embedding", "semantic similarity", "Resource Description Framework", "Simple Knowledge Organization System",
            "SPARQL"]),
        C("Knowledge engineering", "елемент системи на знаннях", ["rule-based system", "production rule", "inference engine",
                                                                  "frame", "competency question"]),
        C("Data engineering", "етап роботи з даними", ["data integration", "data pipeline"]),
    ]),
])

CAT_DEF = {
    "Biomedical data analysis": "Кореневе поняття: усе, що стосується аналізу біомедичних даних.",
    "Biological entity": "Біологічна сутність — об'єкт живої природи на молекулярному рівні.",
    "Genomic element": "Елемент геному або сукупність таких елементів.",
    "Protein-level entity": "Сутність білкового рівня: від амінокислоти до протеому.",
    "Genetic variation": "Відмінності послідовності ДНК між особами або від референсу та їх характеристики.",
    "Variant by origin": "Класифікація варіантів за походженням: спадкові чи набуті.",
    "Variant by clinical significance": "Класифікація варіантів за доведеним клінічним значенням.",
    "Biological property": "Властивість або процес біологічної системи, що спостерігається чи вимірюється.",
    "Heredity": "Властивості, пов'язані з передачею й проявом ознак.",
    "Molecular activity": "Молекулярні процеси та їх вимірювані показники.",
    "Method and procedure": "Спосіб дії: лабораторний, обчислювальний або клінічний.",
    "Laboratory method": "Експериментальний метод аналізу зразків.",
    "Computational procedure": "Крок обчислювальної обробки даних.",
    "Clinical procedure": "Крок клінічного процесу, пов'язаний із генетичними даними.",
    "Research field": "Галузь науки, об'єкт вивчення якої — певний тип біомолекул.",
    "Data and artifact": "Дані й артефакти: файли, записи, метадані.",
    "Omics data": "Дані геномних і протеомних вимірювань на різних стадіях обробки.",
    "Clinical data": "Записи, що описують пацієнта та його родину.",
    "Data about data": "Дані, що описують інші дані (метадані, схема, походження).",
    "Measure of quality": "Показник, за яким оцінюють якість варіантів або даних.",
    "Variant call annotation": "Анотація виклику варіанта, що кількісно характеризує його підтримку ридами.",
    "Clinical concept": "Поняття клінічної ситуації: особа, стан, терапія, захист прав.",
    "Person": "Особа в контексті генетичного дослідження родини.",
    "Condition": "Клінічний стан: діагноз, симптом, хвороба, маркер.",
    "Therapy": "Лікувальне втручання або лікарський засіб.",
    "Ethical and legal safeguard": "Правова чи етична гарантія захисту особи й даних.",
    "Knowledge and information technology": "Поняття інженерії знань та інформаційних технологій.",
    "Knowledge organization system": "Система організації знань: від словника до графа знань.",
    "Data resource": "Публічний ресурс біомедичних даних.",
    "Database technology": "Тип бази даних за моделлю даних.",
    "Representation and similarity": "Способи подання даних і порівняння об'єктів.",
    "Knowledge engineering": "Елементи побудови систем на знаннях.",
    "Data engineering": "Етапи роботи з даними в інформаційних системах.",
}
LLM_ORIGIN = {"Research field"}                                      # гілка запозичена з LLM-версії
SRC_NOTE = {"Omics data": "expert (об'єднано після тесту єдиної дитини)", "Therapy": "expert (змінено після κ-аналізу)", "Computational procedure": "expert (+ порядок етапів за LLM)"}


def build():
    terms = {t["term"]: t for t in load_terms()}
    rows, counter = [], [0]

    def add(node, parent, level):
        counter[0] += 1
        nid = f"C{counter[0]:03d}"
        label, principle, kids = (node, "", []) if isinstance(node, str) else node
        if label in terms:
            t = terms[label]
            row = {"id": nid, "label": label, "parent": parent, "definition": t["definition"], "alt_labels": t["alt_labels"],
                   "source": t["source"], "level": level, "principle": principle or "", "term_id": t["id"],
                   "label_uk": t["label_uk"]}
        else:
            origin = "llm-hybrid" if label in LLM_ORIGIN else SRC_NOTE.get(label, "expert")
            row = {"id": nid, "label": label, "parent": parent, "definition": CAT_DEF[label], "alt_labels": "",
                   "source": origin, "level": level, "principle": principle or "", "term_id": "", "label_uk": ""}
        rows.append(row)
        for k in kids:
            add(k, nid, level + 1)

    add(TREE, "", 0)
    return rows


def main():
    rows = build()
    out = ROOT / "models/taxonomy_final.csv"
    with open(out, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, ["id", "label", "parent", "definition", "alt_labels", "source", "level", "principle", "term_id", "label_uk"])
        w.writeheader(); w.writerows(rows)
    print(f"вузлів {len(rows)}; термінів {sum(1 for r in rows if r['term_id'])}; максимальний рівень {max(r['level'] for r in rows)}")


if __name__ == "__main__":
    main()
