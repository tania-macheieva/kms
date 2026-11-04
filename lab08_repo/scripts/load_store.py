"""Завантажує граф знань у pyoxigraph (іменовані графи tbox/abox/inferred/links), перевіряє COUNT, пише docs/load_log.md і data/kb.jsonld."""
import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path

import pyoxigraph as ox
from rdflib import Graph
from rdflib.namespace import OWL, RDF

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from store import G, GRAPHS, PREFIXES, load_graphs, open_store, prefix_header, query   # noqa: E402


def jsonld():
    """JSON-LD для індивідів ЛР7 (+ їхні об'єкти-літерали): ≥ 20 сутностей."""
    g = Graph().parse(ROOT / "data/graphs/abox.ttl", format="turtle")
    sub = Graph()
    keep = {s for s in g.subjects(RDF.type, OWL.NamedIndividual) if "VAR-1" not in str(s) and "SAMPLE" not in str(s)}   # без синтетичної когорти
    for s in keep:
        for p, o in g.predicate_objects(s): sub.add((s, p, o))
    ctx = {k: v for k, v in PREFIXES.items() if k in ("dkh", "rdfs", "xsd", "owl")}
    sub.serialize(ROOT / "data/kb.jsonld", format="json-ld", context=ctx, indent=1)
    back = Graph().parse(ROOT / "data/kb.jsonld", format="json-ld")
    return len(keep), len(sub), len(back)


def main():
    store = open_store(fresh=True)
    load_graphs(store)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    total = int(next(iter(query(store, "SELECT (COUNT(*) AS ?n) WHERE { GRAPH ?g { ?s ?p ?o } }")))["n"].value)
    per = {r["g"].value.split(":")[-1]: int(r["n"].value) for r in query(store, "SELECT ?g (COUNT(*) AS ?n) WHERE { GRAPH ?g { ?s ?p ?o } } GROUP BY ?g ORDER BY ?g")}
    files = {}
    for name, rel in GRAPHS.items():
        f = ROOT / rel
        if f.exists(): files[name] = (rel, len(Graph().parse(f, format="turtle")), hashlib.sha256(f.read_bytes()).hexdigest()[:12])
    ok = all(per.get(n) == v[1] for n, v in files.items())
    ents, jt, jb = jsonld()
    typed = int(next(iter(query(store, "SELECT (COUNT(DISTINCT ?s) AS ?n) WHERE { ?s a/rdfs:subClassOf* dkh:GeneticVariant }")))["n"].value)
    meta = {"loaded": now, "pyoxigraph": ox.__version__ if hasattr(ox, "__version__") else "0.5.x", "kb_version": "kb-0.1.0", "graphs": per, "total_quads": total, "files": {k: list(v) for k, v in files.items()}}
    (ROOT / "data/load_meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
    L = ["# Журнал завантаження", "", f"- Дата й час завантаження: **{now}** (Europe/Kiev)", f"- Триплстор: **pyoxigraph {meta['pyoxigraph']}** (вбудований SPARQL 1.1 стор на RocksDB, каталог `store/`) — замість Apache Jena Fuseki/GraphDB (Docker і завантаження JAR тут недоступні)",
         f"- Версія графа знань: **{meta['kb_version']}** (контрольні суми файлів нижче)", "- Dataset: іменовані графи `urn:dkh:graph:{tbox,abox,inferred,links}`; запити виконуються над об'єднанням графів (`use_default_graph_as_union`).", "",
         "## Префікси", "", "```", prefix_header().strip(), "```", "", "Ті самі префікси записано у всіх файлах Turtle (`@prefix dkh:` тощо) і в `scripts/store.py` (`PREFIXES`) — єдине джерело для запитів.", "",
         "## Завантажені файли й перевірка COUNT", "", "| Граф | Файл | Триплетів (rdflib) | COUNT у сторі | SHA-256 (12) |", "|---|---|---|---|---|"]
    for n, (rel, c, h) in files.items(): L.append(f"| {n} | {rel} | {c} | {per.get(n)} | {h} |")
    L += ["", f"Запит: `SELECT (COUNT(*) AS ?n) WHERE {{ GRAPH ?g {{ ?s ?p ?o }} }}` → **{total}** квадів; сума за графами збігається з кількістю триплетів у файлах: **{'так' if ok else 'НІ'}**.", "",
          f"Додаткова перевірка: `SELECT (COUNT(DISTINCT ?s) …) WHERE {{ ?s a/rdfs:subClassOf* dkh:GeneticVariant }}` → {typed} генетичних варіантів (4 з ЛР7 + 60 синтетичних).", "",
          "## JSON-LD", "", f"`data/kb.jsonld` — {ents} іменованих індивідів ЛР7 (≥ 20), {jt} триплетів; зворотний парсинг rdflib дає {jb} триплетів ({'збігається' if jb == jt else 'розбіжність'}).", "",
          "## Збагачення даними", "", "До онтології й індивідів ЛР7 додано синтетичну когорту (seed 42): 3 зразки (SAMPLE-A/B/C), по 20 варіантів із анотаціями QD, FS, SOR, MQ (значення випадкові в правдоподібних діапазонах), три патогенні варіанти, клас `dkh:Sample` і властивість `dkh:fromSample`. Усі особи й варіанти вигадані."]
    (ROOT / "docs/load_log.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print(json.dumps(meta["graphs"]), total, ok, ents, jt, jb)
    return ok


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
