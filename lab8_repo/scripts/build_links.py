"""data/links.ttl (прийняті зв'язки), data/links_decisions.csv (усі кандидати, у т. ч. відхилені), data/wikidata_mirror.ttl (мітки Q-id зі списку пошуку).
Метод: Q-id кандидатів знайдено пошуковим запитом (WebSearch, домен wikidata.org) 2026-10-27; єдине, що вдалося перевірити, — заголовок (мітка) сторінки в результатах пошуку.
Сторінки сутностей відкрити не вдалося (WebFetch: url_not_found), тому описи, «instance of» та зовнішні ідентифікатори НЕ перевірено."""
import csv
import re
from pathlib import Path

from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import OWL, RDF, RDFS, SKOS, XSD

ROOT = Path(__file__).resolve().parents[1]
D = Namespace("http://example.org/dkh/onto#"); WD = Namespace("http://www.wikidata.org/entity/")
# (наш термін, наш IRI, наш label, Q-id, мітка в Wikidata за списком пошуку, властивість, впевненість, рішення, обґрунтування)
C = [
 ("gene", "Gene", "gene", "Q7187", "gene", "closeMatch", "medium-high", "accepted", "мітки збігаються; тип/опис сторінки не перевірено, тому closeMatch, а не exactMatch"),
 ("breast cancer", "BreastCancer", "breast cancer", "Q128581", "breast cancer", "closeMatch", "medium-high", "accepted", "мітки збігаються; ми також маємо MeSH Breast Neoplasms (ЛР5) — узгоджується"),
 ("ovarian cancer", "OvarianCancer", "ovarian cancer", "Q172341", "ovarian cancer", "closeMatch", "medium-high", "accepted", "мітки збігаються; MeSH Ovarian Neoplasms (ЛР5)"),
 ("single nucleotide polymorphism", "SNP", "single nucleotide polymorphism", "Q501128", "single-nucleotide polymorphism", "closeMatch", "medium-high", "accepted", "мітки збігаються з точністю до дефіса"),
 ("genetic counseling", "GeneticCounseling", "genetic counseling", "Q1124169", "genetic counseling", "closeMatch", "medium-high", "accepted", "мітки збігаються; MeSH Genetic Counseling (ЛР5)"),
 ("exon", "Exon", "exon", "Q373027", "exon", "closeMatch", "medium", "accepted", "мітки збігаються; у пошуку є омоніми (прізвища, ExxonMobil) — вибрано запис саме з міткою «exon», тип не перевірено"),
 ("BRCA1", "BRCA1", "BRCA1", "Q227339", "BRCA1", "closeMatch", "medium", "accepted", "мітка збігається; у Wikidata ген і білок — окремі елементи, не з'ясовано, який саме Q227339; тому closeMatch, не sameAs"),
 ("BRCA2", "BRCA2", "BRCA2", "Q17853272", "BRCA2", "closeMatch", "low-medium", "accepted", "мітка збігається, але є другий кандидат Q421651 «BRCA2 DNA repair associated»; який із двох — ген, не перевірено"),
 ("VCF file", "VCFFile", "VCF file", "Q7915770", "Variant Call Format", "relatedMatch", "low", "accepted", "наш клас — файл у форматі, Wikidata — формат: не еквівалент, лише пов'язане поняття"),
 ("single nucleotide polymorphism", "SNP", "single nucleotide polymorphism", "Q7391885", "SNP array", "closeMatch", "—", "rejected", "«SNP array» — технологія (мікрочип) для виявлення SNP, не тип варіанта: мітка іншого поняття"),
 ("pathogenic variant", "PathogenicVariant", "pathogenic variant", "Q4836333", "BRCA mutation", "closeMatch", "—", "rejected", "«BRCA mutation» вужче (лише BRCA), а наш клас — будь-який патогенний варіант; зв'язок хибний за обсягом"),
 ("hereditary cancer", "(ЛР6, не клас ЛР7)", "hereditary cancer", "Q19000660", "hereditary breast ovarian cancer", "closeMatch", "—", "rejected", "це конкретний синдром (HBOC), вужчий за «спадковий рак»"),
 ("BRCA2", "BRCA2", "BRCA2", "Q421651", "BRCA2 DNA repair associated", "closeMatch", "—", "rejected", "другий елемент для того ж гена: неоднозначність; без відкритої сторінки (ген чи білок) обрати не можна — залишено перший збіг за точною міткою"),
]
norm = lambda s: re.sub(r"[^a-z0-9]", "", s.lower())
g = Graph(); [g.bind(k, v) for k, v in (("dkh", D), ("skos", SKOS), ("wd", WD), ("rdfs", RDFS), ("xsd", XSD), ("owl", OWL))]
g.add((D.matchConfidence, RDF.type, OWL.AnnotationProperty)); g.add((D.matchConfidence, RDFS.label, Literal("match confidence", lang="en")))
g.add((D.matchVerification, RDF.type, OWL.AnnotationProperty)); g.add((D.matchVerification, RDFS.label, Literal("match verification", lang="en")))
rows = []
for term, iri, lab, q, wl, prop, conf, dec, why in C:
    rows.append({"our_term": term, "our_iri": f"dkh:{iri}", "wikidata": f"wd:{q}", "wikidata_label": wl, "property": f"skos:{prop}", "confidence": conf, "decision": dec,
                 "label_match_V1": int(norm(lab) == norm(wl)), "rationale": why})
    if dec == "accepted":
        s, o = D[iri], WD[q]
        g.add((s, SKOS[prop], o)); g.add((o, RDFS.label, Literal(wl, lang="en")))
        # reified-коментар: анотація на самому зв'язку (OWL axiom annotation у стилі RDF-reification)
        b = URIRef(f"urn:dkh:link:{iri}-{q}")
        g.add((b, RDF.type, RDF.Statement)); g.add((b, RDF.subject, s)); g.add((b, RDF.predicate, SKOS[prop])); g.add((b, RDF.object, o))
        g.add((b, D.matchConfidence, Literal(conf))); g.add((b, RDFS.comment, Literal(why, lang="uk"))); g.add((b, D.matchVerification, Literal("V1: мітка збігається зі списком пошуку Wikidata 2026-10-27; сторінку не відкрито")))
g.serialize(ROOT / "data/links.ttl", format="turtle")
with open(ROOT / "data/links_decisions.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, list(rows[0])); w.writeheader(); w.writerows(rows)
m = Graph(); m.bind("wd", WD); m.bind("rdfs", RDFS)
m.add((URIRef("urn:dkh:mirror"), RDFS.comment, Literal("Локальне дзеркало міток Wikidata: лише пари Q-id → мітка, зняті з результатів пошуку 2026-10-27. Не є вмістом Wikidata.")))
for r in C: m.add((WD[r[3]], RDFS.label, Literal(r[4], lang="en")))
m.serialize(ROOT / "data/wikidata_mirror.ttl", format="turtle")
print(sum(r["decision"] == "accepted" for r in rows), "прийнято;", sum(r["decision"] == "rejected" for r in rows), "відхилено")
