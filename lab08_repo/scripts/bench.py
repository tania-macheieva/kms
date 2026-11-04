"""Порівняння часу «повільний vs оптимізований» запит на синтетичному наборі (seed 42): N варіантів × 4 анотації.
Результат: queries/results/bench.json. Той самий запит за змістом (кількість варіантів із QD<2), однакова відповідь — перевіряється."""
import json
import random
import statistics
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import pyoxigraph as ox  # noqa: E402
from store import ROOT, prefix_header  # noqa: E402

N = int(sys.argv[1]) if len(sys.argv) > 1 else 50000


def build(n, seed=42):
    rnd = random.Random(seed)
    D = lambda s: ox.NamedNode("http://example.org/dkh/onto#" + s)
    g = ox.NamedNode("urn:bench")
    XD = ox.NamedNode("http://www.w3.org/2001/XMLSchema#decimal"); T = ox.NamedNode("http://www.w3.org/1999/02/22-rdf-syntax-ns#type")
    qs = []
    for i in range(n):
        v = D(f"B{i}"); qs += [ox.Quad(v, T, D("SNP" if i % 5 else "Indel"), g), ox.Quad(v, D("hasVariantId"), ox.Literal(f"B-{i}"), g)]
        for nm, lo, hi in (("QD", 0, 35), ("FS", 0, 80), ("SOR", 0, 6), ("MQ", 20, 60)):
            a = D(f"B{i}_{nm}")
            qs += [ox.Quad(v, D("hasAnnotation"), a, g), ox.Quad(a, D("hasAnnotationName"), ox.Literal(nm), g),
                   ox.Quad(a, D("hasNumericValue"), ox.Literal(f"{rnd.uniform(lo, hi):.1f}", datatype=XD), g), ox.Quad(a, D("isAnnotationOf"), v, g)]
    st = ox.Store(); st.extend(qs)
    return st


def main():
    st = build(N)
    res = {"variants": N, "triples": len(st), "seed": 42, "runs": 5}
    for name in ("slow", "fast"):
        text = prefix_header() + (ROOT / f"queries/bench/{name}.rq").read_text(encoding="utf-8")
        ts = []
        for _ in range(5):
            t = time.perf_counter(); r = list(st.query(text, use_default_graph_as_union=True)); ts.append(time.perf_counter() - t)
        res[name] = {"answer": int(r[0]["n"].value), "ms_median": round(statistics.median(ts) * 1000, 1), "ms_all": [round(x * 1000, 1) for x in ts]}
    assert res["slow"]["answer"] == res["fast"]["answer"], "відповіді відрізняються!"
    res["speedup"] = round(res["slow"]["ms_median"] / res["fast"]["ms_median"], 1)
    (ROOT / "queries/results/bench.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
    print(res)


if __name__ == "__main__":
    main()
