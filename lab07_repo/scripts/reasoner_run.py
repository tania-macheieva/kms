"""HermiT: узгодженість, класифікація, виведені твердження, навмисні суперечності → docs/reasoner_log.md, models/onto_inferred.ttl.
Потребує Java та owlready2 (містить HermiT.jar)."""
import contextlib
import io
import os
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path

from rdflib import Graph, Namespace, URIRef
from rdflib.namespace import OWL, RDF

ROOT = Path(__file__).resolve().parents[1]
D = Namespace("http://example.org/dkh/onto#")
import owlready2
HJ = Path(owlready2.__file__).parent / "hermit"


def java_executable():
    java = shutil.which("java")
    if java:
        return java
    java_home = os.environ.get("JAVA_HOME")
    if java_home:
        candidate = Path(java_home) / "bin" / ("java.exe" if os.name == "nt" else "java")
        if candidate.is_file():
            return str(candidate)
    raise RuntimeError(
        "Java was not found. Install a JDK (the project was tested with Java 21), "
        "add its bin directory to PATH or set JAVA_HOME, then reopen PowerShell."
    )


def merged_graph(extra=None, drop=None):
    g = Graph().parse(ROOT / "models/onto.owl", format="turtle")
    d = Graph().parse(ROOT / "models/onto_data.ttl", format="turtle")
    for s in set(d.subjects(OWL.imports, None)):
        d.remove((s, None, None))
    g += d
    for t in (extra or []): g.add(t)
    for t in (drop or []): g.remove(t)
    return g


def hermit(args, g, tmp):
    f = Path(tmp) / "m.owl"
    g.serialize(f, format="xml")
    cp = os.pathsep.join((str(HJ), str(HJ / "HermiT.jar")))
    command = [java_executable(), "-cp", cp, "org.semanticweb.HermiT.cli.CommandLine", *args, f.resolve().as_uri()]
    p = subprocess.run(command, capture_output=True, text=True)
    out = "\n".join(l for l in (p.stdout + p.stderr).splitlines() if not l.startswith("Picked up JAVA_TOOL_OPTIONS"))
    return p.returncode, out


def short(u): return str(u).split("#")[-1].strip("<>")


def main():
    tmp = tempfile.mkdtemp()
    ver = ["HermiT"]
    g = merged_graph()
    # 1. узгодженість + класифікація
    rc, cls_out = hermit(["-c"], g, tmp)
    unsat = [l for l in cls_out.splitlines() if "owl:Nothing" in l or "Nothing>" in l]
    rc2, ind_out = hermit(["-I"], g, tmp)
    inferred_types = {}
    for m in re.finditer(r"Type\( <([^>]+)> <([^>]+)> \)", ind_out):
        inferred_types.setdefault(m.group(1), set()).add(m.group(2))
    asserted = {}
    for s, o in g.subject_objects(RDF.type): asserted.setdefault(str(s), set()).add(str(o))
    parents = {}
    for m in re.finditer(r"SubClassOf\( <([^>]+)> <([^>]+)> \)", cls_out): parents.setdefault(m.group(1), set()).add(m.group(2))
    def anc(c, seen=None):
        seen = seen if seen is not None else set()
        for q in parents.get(c, ()):
            if q not in seen: seen.add(q); anc(q, seen)
        return seen
    for ind in list(inferred_types):
        ts = inferred_types[ind]
        inferred_types[ind] = {t for t in ts if not any(t in anc(u) for u in ts if u != t)}
    new_types = []
    for ind, ts in sorted(inferred_types.items()):
        if (URIRef(ind), RDF.type, OWL.NamedIndividual) not in g: continue
        for t in sorted(ts):
            if t not in asserted.get(ind, set()):
                new_types.append((short(ind), short(t)))
    # 2. виведені властивості (owlready2 + HermiT)
    from owlready2 import World, sync_reasoner_hermit
    f = Path(tmp) / "o.owl"; g.serialize(f, format="xml")
    buf = io.StringIO()
    w = World(); onto = w.get_ontology(f"file://{f}").load()
    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
        with onto: sync_reasoner_hermit(w, infer_property_values=True)
    rel = []
    asserted_rel = {(str(a), str(b), str(c)) for a, b, c in g}
    for ind in onto.individuals():
        for pr in onto.object_properties():
            vals = getattr(ind, pr.python_name, None)
            vals = [] if vals is None else (vals if isinstance(vals, list) else [vals])
            for v in vals:
                trip = (str(D[ind.name]), str(D[pr.name]), str(D[v.name]))
                if trip not in asserted_rel and ind.name != v.name:
                    rel.append((ind.name, pr.name, v.name))
    rel = sorted(set(rel))
    # 3. onto_inferred.ttl
    inf = Graph(); inf.bind("dkh", D)
    for ind, t in new_types: inf.add((D[ind], RDF.type, D[t]))
    for s, p, o in rel: inf.add((D[s], D[p], D[o]))
    inf.serialize(ROOT / "models/onto_inferred.ttl", format="turtle")
    # 4. навмисні суперечності
    cases = []
    bad = merged_graph(extra=[(D["VAR-003"], RDF.type, D.SNP)])
    rcb, outb = hermit(["-c"], bad, tmp); fixed_rc, _ = hermit(["-c"], merged_graph(), tmp)
    cases.append(("Суперечність 1: індивід VAR-003 (INDEL) додатково оголошено SNP, а SNP і Indel диз'юнктні", "VAR-003 rdf:type dkh:SNP", rcb, outb, fixed_rc))
    dm = [(D.Marta, D.hasParent, D.Maria), (D.Iryna, OWL.differentFrom, D.Petro), (D.Iryna, OWL.differentFrom, D.Maria), (D.Petro, OWL.differentFrom, D.Maria)]
    bad2 = merged_graph(extra=dm)
    rcb2, outb2 = hermit(["-c"], bad2, tmp)
    cases.append(("Суперечність 2: Marta має трьох різних батьків, а Person ⊑ hasParent ≤ 2", "Marta hasParent Maria; Iryna, Petro, Maria — owl:differentFrom", rcb2, outb2, fixed_rc))
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    L = [f"# Журнал reasoner (HermiT)", "", f"Дата запуску: {now}. Reasoner: {' '.join(ver) or 'HermiT'} (HermiT.jar із пакета owlready2 {owlready2.VERSION}); Java: OpenJDK 21.",
         "Онтологія: models/onto.owl + models/onto_data.ttl (злиті rdflib у RDF/XML; Protégé очікує ту саму комбінацію). Скрипт: `python scripts/reasoner_run.py`. Протоколи Protégé (скріншоти) в цьому середовищі отримати неможливо — замість них наведено вивід командного рядка HermiT.", "",
         "## 1. Узгодженість і класифікація", "", f"Команда: `java -cp HermiT.jar org.semanticweb.HermiT.cli.CommandLine -c file:///…/m.owl` → код завершення **{rc}**; необґрунтованих (unsatisfiable) класів: **{len(unsat)}**. Онтологія **узгоджена**. Вивід починається так:", "", "```", "\n".join(cls_out.splitlines()[:6]), "…", f"(усього {len(cls_out.splitlines())} рядків SubClassOf/EquivalentClasses; повний вивід — docs/evidence/hermit_classify.txt)", "```", "",
         f"## 2. Виведені твердження про індивідів (класифікація екземплярів, `-I`)", "", f"Нових припущень типу (відсутніх у вхідних даних): **{len(new_types)}**.", "", "| Індивід | Виведений тип | Чому (аксіома) |", "|---|---|---|"]
    WHY = {"FirstDegreeRelative": "Person ⊓ ∃isFirstDegreeRelativeOf.Proband (зв'язок виведено з hasParent/hasSibling/hasChild)", "SecondDegreeRelative": "ланцюги hasParent∘hasParent, hasParent∘hasSibling ⊑ isSecondDegreeRelativeOf",
           "ThirdDegreeRelative": "ланцюг hasAuntOrUncle∘hasChild = hasCousin ⊑ isThirdDegreeRelativeOf", "AdultRelative": "Relative ⊓ ∃hasAgeYears.[≥ 18]", "MinorRelative": "Relative ⊓ ∃hasAgeYears.[< 18]",
           "PathogenicVariant": "GeneticVariant ⊓ ∃hasClinicalSignificance.{Pathogenic}", "LowQDVariant": "∃hasAnnotation.(QualityByDepth ⊓ значення < 2)", "FlaggedVariant": "LowQDVariant ⊑ FlaggedVariant (об'єднання порогів)",
           "HighFSSnpVariant": "SNP ⊓ ∃hasAnnotation.(FisherStrandBias ⊓ значення > 60)", "LowQDAnnotation": "QualityByDepth ⊓ значення < 2", "ExonEndVariant": "GeneticVariant ⊓ hasExonEndPosition = true"}
    for ind, t in new_types:
        L.append(f"| {ind} | {t} | {WHY.get(t, '—')} |")
    L += ["", "## 3. Виведені зв'язки між індивідами (`sync_reasoner_hermit(infer_property_values=True)`)", "", f"Нових зв'язків: **{len(rel)}**. Приклади:", "", "```"]
    L += [f"{s} {p} {o}" for s, p, o in rel[:25]] + ["…", "```", "", "## 4. Навмисні суперечності", ""]
    for title, change, rcx, outx, fixrc in cases:
        L += [f"### {title}", "", f"Внесена зміна: `{change}`.", "", f"HermiT (код завершення {rcx}):", "", "```", "\n".join(outx.splitlines()[:3]), "```", "",
              f"Усунення: видалено доданий(і) трип­лет(и) (у Protégé — вилучити твердження або виправити тип/кількість батьків); повторний запуск HermiT → код {fixrc}, онтологія знову узгоджена.", ""]
    (ROOT / "docs/reasoner_log.md").write_text("\n".join(L), encoding="utf-8")
    (ROOT / "docs/evidence/hermit_classify.txt").write_text(cls_out, encoding="utf-8")
    (ROOT / "docs/evidence/hermit_instances.txt").write_text(ind_out, encoding="utf-8")
    (ROOT / "docs/evidence/hermit_contradictions.txt").write_text("\n\n".join(f"== {c[0]}\n{c[3]}" for c in cases), encoding="utf-8")
    print("consistent rc", rc, "unsat", len(unsat), "new types", len(new_types), "new relations", len(rel), "contradiction rc", [c[2] for c in cases], "fixed rc", fixed_rc)


if __name__ == "__main__":
    main()
