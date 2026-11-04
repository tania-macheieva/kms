"""Конвеєр text-to-SPARQL: промпт (зі схемою) → LLM → парсер → перевірка схеми → виконання з LIMIT → порівняння з еталоном.
LLM-виклики тут не робляться (див. docs/t2s_eval.md): відповіді моделі зберігаються у llm_log/raw/*.json і оцінюються цим модулем."""
import json
import re
from pathlib import Path

import pyoxigraph as ox
from rdflib import Graph, Namespace, RDF, RDFS, OWL, URIRef
from rdflib.plugins.sparql import prepareQuery
from rdflib.plugins.sparql.parserutils import CompValue

ROOT = Path(__file__).resolve().parents[1]
D = Namespace("http://example.org/dkh/onto#")
EXEC_LIMIT = 200
PRE = {"dkh": str(D), "rdf": str(RDF), "rdfs": str(RDFS), "owl": str(OWL), "xsd": "http://www.w3.org/2001/XMLSchema#"}
STD = {str(RDF), str(RDFS), str(OWL), "http://www.w3.org/2001/XMLSchema#"}


# ---------- схема ----------
def _tbox():
    return Graph().parse(ROOT / "data/graphs/tbox.ttl", format="turtle")


def vocabulary():
    """Дозволені IRI: класи й властивості TBox (простір dkh) + індивіди ABox (дані) — те, що «існує у схемі/даних»."""
    t = _tbox(); a = Graph().parse(ROOT / "data/graphs/abox.ttl", format="turtle")
    terms = set()
    for ty in (OWL.Class, OWL.ObjectProperty, OWL.DatatypeProperty, OWL.AnnotationProperty, OWL.NamedIndividual):
        terms |= {s for s in t.subjects(RDF.type, ty) if isinstance(s, URIRef)}
    terms |= {s for s in a.subjects() if isinstance(s, URIRef)}
    return {x for x in terms if str(x).startswith(str(D))}


def schema_text(with_labels=False):
    t = _tbox(); loc = lambda x: "dkh:" + str(x).split("#")[-1]
    cls = sorted(c for c in t.subjects(RDF.type, OWL.Class) if isinstance(c, URIRef) and str(c).startswith(str(D)))
    lines = ["# Класи (Class [SubClassOf])"]
    for c in cls:
        sup = sorted({loc(s) for s in t.objects(c, RDFS.subClassOf) if isinstance(s, URIRef) and str(s).startswith(str(D))})
        lines.append(loc(c) + (f" [⊑ {', '.join(sup)}]" if sup else ""))
    lines.append("# Властивості (property: domain → range)")
    for ty, kind in ((OWL.ObjectProperty, "object"), (OWL.DatatypeProperty, "data")):
        for p in sorted(p for p in t.subjects(RDF.type, ty) if str(p).startswith(str(D))):
            dm = t.value(p, RDFS.domain); rg = t.value(p, RDFS.range)
            f = lambda x: (loc(x) if str(x).startswith(str(D)) else "xsd:" + str(x).split("#")[-1]) if x is not None else "?"
            lines.append(f"{loc(p)} ({kind}): {f(dm)} → {f(rg)}")
    return "\n".join(lines)


# ---------- парсинг, перевірки ----------
def extract_sparql(raw):
    m = re.search(r"```(?:sparql|SPARQL)?\s*\n(.*?)```", raw, re.S)
    return (m.group(1) if m else raw).strip()


def with_prefixes(q):
    declared = set(re.findall(r"(?im)^\s*PREFIX\s+(\w*):", q))
    return "".join(f"PREFIX {k}: <{v}>\n" for k, v in PRE.items() if k not in declared) + q


def check_syntax(q):
    try:
        pq = prepareQuery(with_prefixes(q)); return True, pq, ""
    except Exception as e:
        return False, None, str(e)[:200]


def _iris(node, acc):
    if isinstance(node, URIRef): acc.add(node)
    elif isinstance(node, CompValue) or isinstance(node, dict):
        for v in node.values(): _iris(v, acc)
    elif isinstance(node, (list, tuple, set)):
        for v in node: _iris(v, acc)
    elif hasattr(node, "_vars") or hasattr(node, "p"):
        for v in vars(node).values(): _iris(v, acc)


def used_iris(pq):
    acc = set(); _iris(pq.algebra, acc); return acc


def check_schema(pq, vocab):
    """«Тільки зі схеми»: усі IRI простору dkh: мають існувати у TBox/ABox; IRI rdf/rdfs/owl/xsd дозволені."""
    bad = sorted(str(i).replace(str(D), "dkh:") for i in used_iris(pq) if str(i).startswith(str(D)) and i not in vocab)
    other = sorted(str(i) for i in used_iris(pq) if not str(i).startswith(str(D)) and not any(str(i).startswith(s) for s in STD))
    return (not bad and not other), bad + other


def canon(res):
    def norm(t):
        if t is None: return ""
        v = t.value
        if isinstance(t, ox.Literal) and t.datatype and t.datatype.value.endswith(("decimal", "integer", "double")):
            try: return f"{float(v):.6g}"
            except ValueError: pass
        return v.replace(str(D), "dkh:") if isinstance(t, ox.NamedNode) else v
    k = res.__class__.__name__
    if k == "QueryBoolean": return bool(res)
    if k == "QueryTriples": return sorted([norm(t.subject), norm(t.predicate), norm(t.object)] for t in res)
    vs = [v.value for v in res.variables]
    return sorted([norm(s[v]) for v in vs] for s in res)   # порівняння не залежить від імен змінних і порядку рядків


def execute(store, q, limit=EXEC_LIMIT):
    """Виконує запит із LIMIT (якщо його немає й це SELECT); повертає {'ok', 'canon', 'error'}."""
    text = with_prefixes(q)
    if limit and re.search(r"(?i)\bSELECT\b", text) and not re.search(r"(?i)\bLIMIT\s+\d+\s*;?\s*$", text.strip()):
        text = text.strip().removesuffix(";").rstrip() + f"\nLIMIT {limit}"
    try:
        return {"ok": True, "canon": canon(store.query(text, use_default_graph_as_union=True)), "error": ""}
    except Exception as e:
        return {"ok": False, "canon": None, "error": str(e)[:200]}


def evaluate_one(store, vocab, raw, gold_answer):
    q = extract_sparql(raw)
    r = {"sparql": q, "syntax_ok": False, "schema_ok": False, "result_ok": False, "error_stage": "", "detail": ""}
    ok, pq, err = check_syntax(q)
    if not ok:
        r.update(error_stage="syntax", detail=err); return r
    r["syntax_ok"] = True
    sok, bad = check_schema(pq, vocab)
    r["schema_ok"] = sok
    if not sok:
        r.update(error_stage="schema", detail="IRI поза схемою: " + ", ".join(bad)); return r
    ex = execute(store if store is not None else open_store_cached(), q)
    if not ex["ok"]:
        r.update(error_stage="execution", detail=ex["error"]); return r
    if ex["canon"] == gold_answer: r["result_ok"] = True
    else: r.update(error_stage="result", detail=f"отримано {json.dumps(ex['canon'], ensure_ascii=False)[:160]}; очікувалось {json.dumps(gold_answer, ensure_ascii=False)[:160]}")
    return r


_ST = None


def open_store_cached():
    global _ST
    if _ST is None:
        from store import open_store
        _ST = open_store()
    return _ST
