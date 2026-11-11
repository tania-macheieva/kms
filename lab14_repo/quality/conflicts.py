"""Conflict detection over the store: graph thresholds vs notes (value), documents vs legacy notes / older docs (temporal),
naming of the same entity (terminological), graph vs SHACL-style rule (logical). Returns a list of conflict records."""
import re, json, pathlib
from .common import STORE, chunks, graph_csv, read_jsonl
NOTE_VAL = {"QD": r"QD\s*<\s*(\d+(?:\.\d+)?)", "FS": r"FS\s*>\s*(\d+(?:\.\d+)?)", "SOR": r"SOR\s*>\s*(\d+(?:\.\d+)?)"}

def detect(store=STORE):
    ch = chunks(store); fx = json.load(open(pathlib.Path(store) / "fixtures.json", encoding="utf-8")); out = []
    # 1) VALUE: threshold nodes of the graph vs numeric thresholds stated in notes
    th = {r["annotation"] + ("_" + r["variantType"] if r["variantType"] != "all" else ""): r for r in graph_csv(store, "nodes_Threshold.csv")}
    for ann, rx in NOTE_VAL.items():
        g = next(r for k, r in th.items() if r["annotation"] == ann and r["variantType"] in ("all", "SNP"))
        for n in fx:
            m = re.search(rx, n["text"])
            if m and float(m.group(1)) != float(g["value"]):
                out.append(dict(id=f"CF-{ann}", type="value", subject=f"{ann} hard-filter threshold", op=g["op"], items=[
                    dict(source=f"graph:Threshold:{g['id']}", value=float(g["value"]), origin="gatk (graph, lab 9)"), dict(source=n["id"], value=float(m.group(1)), origin="synthetic fixture note")]))
    # 2) TEMPORAL: Java requirement of GATK — current README (17) vs legacy note (8) vs older tutorial (1.8)
    j17 = [c for c in ch if c["chunk_id"] == "gatk_readme#h001"]; jold = [c for c in ch if c["chunk_id"] == "gatk_funco_tutorial#h035"]
    legacy = next((n for n in fx if n["id"] == "fx_gatk_java"), None)
    if j17 and legacy:
        out.append(dict(id="CF-JAVA", type="temporal", subject="Java version required to run/build GATK", items=[
            dict(source="gatk_readme#h001", value="17", origin="GATK README, 2026-10-26 (current)"), dict(source="fx_gatk_java", value="8", origin="legacy note v4.2 (synthetic fixture)")]))
    if j17 and jold and re.search(r"Java 1\.8", jold[0]["text"]):
        out.append(dict(id="CF-JAVA-TUT", type="temporal", subject="Java version in the Funcotator tutorial vs GATK README", items=[
            dict(source="gatk_readme#h001", value="17", origin="GATK README, 2026-10-26"), dict(source="gatk_funco_tutorial#h035", value="1.8", origin="Funcotator tutorial, doc date 2026-08-17 (older page)")]))
    # 3) TERMINOLOGICAL: same concept, several labels
    hg = {k: [c["chunk_id"] for c in ch if re.search(k, c["text"])] for k in (r"\bhg19\b", r"\bb37\b", r"GRCh37")}
    if all(hg.values()):
        out.append(dict(id="CF-ASM-GRCh37", type="terminological", subject="human assembly 'build 37' labels hg19 / b37 / GRCh37 (not interchangeable)",
                        items=[dict(source=v[0], value=k.replace("\\b", ""), origin=f"{len(v)} chunks") for k, v in hg.items()]))
    s1 = [c["chunk_id"] for c in ch if c["doc_id"] == "sarek_usage" and re.search(r"--genome GATK\.GRCh38", c["text"])]
    s2 = [c["chunk_id"] for c in ch if c["doc_id"] == "sarek_usage" and re.search(r"--genome GRCh38\.GATK", c["text"])]
    if s1 and s2:
        out.append(dict(id="CF-ASM-GATK", type="terminological", subject="sarek genome key order: GATK.GRCh38 vs GRCh38.GATK", items=[
            dict(source=s1[0], value="GATK.GRCh38", origin="sarek_usage quickstart / config"), dict(source=s2[0], value="GRCh38.GATK", origin="sarek_usage 'overwrite reference files' example")]))
    # 4) LOGICAL: procedure with minTestingAge applied to a younger person
    procs = {r["id"]: r for r in graph_csv(store, "nodes_Procedure.csv")}; people = {r["name"]: r for r in graph_csv(store, "nodes_Person.csv")}
    for r in graph_csv(store, "rels_APPLIES_TO__Procedure_Person.csv"):
        mt, age = procs.get(r["from"], {}).get("minTestingAge"), people.get(r["to"], {}).get("ageYears")
        if mt and age and int(age) < int(mt):
            out.append(dict(id=f"CF-AGE-{r['to']}", type="logical", subject=f"{r['from']} APPLIES_TO {r['to']} violates minTestingAge",
                            items=[dict(source=f"graph:APPLIES_TO:{r['from']}->{r['to']}", value=f"ageYears={age}", origin="graph"), dict(source=f"graph:Procedure:{r['from']}", value=f"minTestingAge={mt}", origin="graph rule")]))
    return out

if __name__ == "__main__":
    for c in detect(): print(c["id"], c["type"], "|", c["subject"])
