"""Експорт підсумкової таксономії в SKOS (rdflib) → models/taxonomy.ttl.

ConceptScheme, Concept, prefLabel@en/@uk, altLabel@en, definition@uk, broader/narrower, hasTopConcept/topConceptOf,
exactMatch/closeMatch на зовнішні ресурси (data/external_links.csv, лише зі статусом verified).
Базовий URI example.org — заглушка: перед публікацією замініть на власний простір імен.
"""
import csv
import sys
from pathlib import Path

from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import DCTERMS, RDF, SKOS, XSD

ROOT = Path(__file__).resolve().parent.parent
BASE = "http://example.org/knowledge-hub/biomed/"
EX = Namespace(BASE)

CAT_UK = {"Biomedical data analysis": "Аналіз біомедичних даних", "Biological entity": "Біологічна сутність",
          "Genomic element": "Елемент геному", "Protein-level entity": "Сутність білкового рівня",
          "Genetic variation": "Генетична варіація", "Variant by origin": "Варіант за походженням",
          "Variant by clinical significance": "Варіант за клінічною значущістю", "Biological property": "Біологічна властивість",
          "Heredity": "Спадковість", "Molecular activity": "Молекулярна активність", "Method and procedure": "Метод і процедура",
          "Laboratory method": "Лабораторний метод", "Computational procedure": "Обчислювальна процедура",
          "Clinical procedure": "Клінічна процедура", "Research field": "Галузь досліджень", "Data and artifact": "Дані й артефакти",
          "Omics data": "Омікс-дані", "Clinical data": "Клінічні дані",
          "Data about data": "Дані про дані", "Measure of quality": "Міра якості", "Variant call annotation": "Анотація виклику варіанта",
          "Clinical concept": "Клінічне поняття", "Person": "Особа", "Condition": "Клінічний стан", "Therapy": "Терапія",
          "Ethical and legal safeguard": "Етична й правова гарантія", "Knowledge and information technology": "Знання та інформаційні технології",
          "Knowledge organization system": "Система організації знань", "Data resource": "Ресурс даних",
          "Database technology": "Технологія баз даних", "Representation and similarity": "Подання й схожість",
          "Knowledge engineering": "Інженерія знань", "Data engineering": "Інженерія даних"}


def load_final():
    return list(csv.DictReader(open(ROOT / "models/taxonomy_final.csv", encoding="utf-8-sig")))


def load_links(only_verified=True):
    rows = list(csv.DictReader(open(ROOT / "data/external_links.csv", encoding="utf-8")))
    return [r for r in rows if r["verification_result"].startswith("verified")] if only_verified else rows


def build_graph():
    rows, links = load_final(), load_links()
    g = Graph()
    g.bind("skos", SKOS); g.bind("ex", EX); g.bind("dct", DCTERMS)
    scheme = EX["scheme"]
    g.add((scheme, RDF.type, SKOS.ConceptScheme))
    g.add((scheme, DCTERMS.title, Literal("Біомедична таксономія ЛР5 (Medicine / biomedical data analysis)", lang="uk")))
    g.add((scheme, DCTERMS.title, Literal("Biomedical data analysis taxonomy (Lab 5)", lang="en")))
    g.add((scheme, DCTERMS.description, Literal("Підсумкова таксономія з гібриду експертної, LLM- та кластерної версій; визначення — чернетки LLM.", lang="uk")))
    uri = {r["id"]: EX[r["id"]] for r in rows}
    by_label = {r["label"]: r for r in rows}
    for r in rows:
        c = uri[r["id"]]
        g.add((c, RDF.type, SKOS.Concept))
        g.add((c, SKOS.inScheme, scheme))
        g.add((c, SKOS.notation, Literal(r["id"])))
        g.add((c, SKOS.prefLabel, Literal(r["label"], lang="en")))
        uk = r["label_uk"] or CAT_UK.get(r["label"])
        if uk:
            g.add((c, SKOS.prefLabel, Literal(uk, lang="uk")))
        for a in [x for x in r["alt_labels"].split(";") if x]:
            g.add((c, SKOS.altLabel, Literal(a, lang="en")))
        if r["definition"]:
            g.add((c, SKOS.definition, Literal(r["definition"], lang="uk")))
        if r["parent"]:
            g.add((c, SKOS.broader, uri[r["parent"]]))
            g.add((uri[r["parent"]], SKOS.narrower, c))
        else:
            g.add((c, SKOS.topConceptOf, scheme)); g.add((scheme, SKOS.hasTopConcept, c))
    for l in links:
        c = uri[by_label[l["concept_label"]]["id"]]
        prop = SKOS.exactMatch if l["match_type"] == "exactMatch" else SKOS.closeMatch
        g.add((c, prop, URIRef(l["external_uri"])))
    return g


def main():
    g = build_graph()
    out = ROOT / "models/taxonomy.ttl"
    g.serialize(destination=str(out), format="turtle")
    print(f"записано {out.relative_to(ROOT)}: {len(g)} триплетів")


if __name__ == "__main__":
    main()
