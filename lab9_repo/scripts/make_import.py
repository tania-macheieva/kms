"""Генерує import/00_schema.neo4j.cypher, 01_nodes.cypher, 02_rels.cypher із data/*.csv (однакові для Neo4j 5 і FalkorDB)."""
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KEY = {"Variant": "id", "Annotation": "id", "AnnotationType": "name", "Gene": "symbol", "GenePanel": "name", "Sample": "code", "Person": "name", "Diagnosis": "id", "Threshold": "id", "Procedure": "id", "DataFile": "id", "Instrument": "id", "Situation": "id", "Concept": "name"}
TYPES = {("Annotation", "value"): "float", ("Person", "ageYears"): "int", ("Person", "deceased"): "bool", ("Person", "proband"): "bool", ("Threshold", "value"): "float",
         ("Variant", "exonEnd"): "bool", ("Procedure", "minTestingAge"): "int", ("Concept", "probability"): "float"}
conv = lambda lab, p: (lambda t: {"float": f"CASE row.{p} WHEN '' THEN null ELSE round(toFloat(row.{p}) * 1000) / 1000 END", "int": f"CASE row.{p} WHEN '' THEN null ELSE toInteger(row.{p}) END",
                                  "bool": f"CASE row.{p} WHEN 'true' THEN true WHEN 'false' THEN false ELSE null END", None: f"CASE row.{p} WHEN '' THEN null ELSE row.{p} END"}[t])(TYPES.get((lab, p)))
out = ["// Примітка: toFloat() у FalkorDB повертає значення з точністю float32 (напр. 1.1 → 1.10000002384186), тому округлення round(x*1000)/1000 повертає точний double (дані мають ≤ 1 знака після коми). У Neo4j це безпечно, але зайве.\n// Вузли: LOAD CSV + MERGE за ключем (ідемпотентно). Файли — у каталозі import сервера.\n"]
for lab, k in KEY.items():
    cols = list(next(csv.reader(open(ROOT / f"data/nodes_{lab}.csv", encoding="utf-8"))))
    sets = ", ".join(f"n.{c} = {conv(lab, c)}" for c in cols if c != k)
    out.append(f"LOAD CSV WITH HEADERS FROM 'file:///nodes_{lab}.csv' AS row\nMERGE (n:{lab} {{{k}: row.{k}}})" + (f"\nSET {sets};\n" if sets else ";\n"))
(ROOT / "import/01_nodes.cypher").write_text("\n".join(out), encoding="utf-8")
out = ["// Зв'язки: MATCH кінців + MERGE зв'язку; властивості походження source/confidence/validFrom ставляться при створенні.\n"]
for f in sorted((ROOT / "data").glob("rels_*.csv")):
    t, fl, tl = f.stem[5:].split("__")[0], *f.stem.split("__")[1].split("_")
    out.append(f"LOAD CSV WITH HEADERS FROM 'file:///{f.name}' AS row\nMATCH (a:{fl} {{{KEY[fl]}: row.from}}), (b:{tl} {{{KEY[tl]}: row.to}})\nMERGE (a)-[r:{t}]->(b)\nON CREATE SET r.source = row.source, r.confidence = round(toFloat(row.confidence) * 1000) / 1000, r.validFrom = date(row.validFrom);\n")
(ROOT / "import/02_rels.cypher").write_text("\n".join(out), encoding="utf-8")
UNI = [("Variant", "id"), ("Gene", "symbol"), ("Person", "name"), ("Annotation", "id"), ("Sample", "code"), ("Threshold", "id")]
IDX = [("Annotation", "name"), ("Annotation", "value"), ("Variant", "type"), ("Person", "ageYears")]
s = ["// Схема для Neo4j 5 (довідково; у цьому середовищі виконано еквівалент через API FalkorDB — scripts/import_graph.py).\n"]
s += [f"CREATE CONSTRAINT {l.lower()}_{p} IF NOT EXISTS FOR (n:{l}) REQUIRE n.{p} IS UNIQUE;" for l, p in UNI]
s += [f"CREATE INDEX {l.lower()}_{p}_idx IF NOT EXISTS FOR (n:{l}) ON (n.{p});" for l, p in IDX]
s += ["", "SHOW CONSTRAINTS;", "SHOW INDEXES;"]
(ROOT / "import/00_schema.neo4j.cypher").write_text("\n".join(s) + "\n", encoding="utf-8")
print("ok", len(KEY), "вузлових і", len(list((ROOT / "data").glob("rels_*.csv"))), "реляційних CSV")
