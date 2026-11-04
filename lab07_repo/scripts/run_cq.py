"""Запускає tests/cq_sparql/*.rq на онтології (mine|llm), використовуючи також виведені HermiT твердження.
Порівнює множину відповідей (?answer) з `# expect:`. Результат → docs/evidence/cq_results_<name>.csv"""
import csv
import json
import re
import sys
from pathlib import Path

from rdflib import Graph, Literal, URIRef
from rdflib.namespace import OWL

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from reasoning import infer   # noqa: E402


def load(name):
    g = Graph()
    if name == "mine":
        g.parse(ROOT / "models/onto.owl", format="turtle")
        d = Graph().parse(ROOT / "models/onto_data.ttl", format="turtle")
        for s in set(d.subjects(OWL.imports, None)): d.remove((s, None, None))
        g += d
    else:
        g.parse(ROOT / "models/llm_draft.ttl", format="turtle")
    return g


def norm(v):
    if isinstance(v, Literal):
        try:
            if v.datatype is not None and str(v.datatype).split("#")[-1] in ("decimal", "integer", "double", "float", "int", "nonNegativeInteger"):
                return f"{float(v):g}"
        except ValueError:
            pass
        return str(v)
    return str(v).split("#")[-1].split("/")[-1]


def run(name):
    g = load(name)
    ok, inf, msg = infer(g)
    if ok: g += inf
    out = []
    for f in sorted((ROOT / "tests/cq_sparql").glob("*.rq")):
        text = f.read_text(encoding="utf-8")
        exp = json.loads(re.search(r"# expect: (.*)", text).group(1))
        q = re.search(r"# question: (.*)", text).group(1)
        try:
            got = sorted({norm(r["answer"]) for r in g.query(text) if r["answer"] is not None})
            err = ""
        except Exception as e:
            got, err = [], str(e)[:80]
        passed = sorted(x.lower() for x in exp) == sorted(x.lower() for x in got)
        out.append({"cq": f.stem, "question": q, "expected": json.dumps(sorted(exp), ensure_ascii=False), "got": json.dumps(got, ensure_ascii=False), "passed": int(passed), "error": err})
    with open(ROOT / f"docs/evidence/cq_results_{name}.csv", "w", newline="", encoding="utf-8-sig") as fh:
        w = csv.DictWriter(fh, list(out[0])); w.writeheader(); w.writerows(out)
    share = sum(r["passed"] for r in out) / len(out)
    return out, share, ok


if __name__ == "__main__":
    for n in (sys.argv[1:] or ["mine"]):
        out, share, ok = run(n)
        print(n, "consistent" if ok else "INCONSISTENT", f"{sum(r['passed'] for r in out)}/{len(out)} = {share:.0%}")
        for r in out:
            if not r["passed"]: print("  FAIL", r["cq"], "exp", r["expected"], "got", r["got"], r["error"])
