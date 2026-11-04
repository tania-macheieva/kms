"""Перевіряє ситуації запитами SPARQL над онтологією + виведеними HermiT твердженнями → docs/evidence/situations_queries.txt"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from reasoning import infer   # noqa: E402
from run_cq import load       # noqa: E402


def run():
    g = load("mine"); ok, inf, _ = infer(g); g += inf
    out, allok = [], True
    for f in sorted((ROOT / "tests/sparql_situations").glob("*.rq")):
        t = f.read_text(encoding="utf-8")
        exp = json.loads(re.search(r"# expect_first_column: (.*)", t).group(1))
        rows = [tuple(str(x) for x in r) for r in g.query(t)]
        first = sorted({r[0] for r in rows})
        passed = first == sorted(exp); allok &= passed
        out += [f"== {f.stem}: {re.search(r'# question: (.*)', t).group(1)}", t.split("\n", 2)[2].strip(), f"Результат: {rows}", f"Очікувано (перший стовпець): {exp} → {'OK' if passed else 'FAIL'}", ""]
    (ROOT / "docs/evidence/situations_queries.txt").write_text("\n".join(out), encoding="utf-8")
    return allok, out


if __name__ == "__main__":
    ok, out = run(); print("\n".join(l for l in out if l.startswith("Результат") or l.startswith("Очікувано"))); sys.exit(0 if ok else 1)
