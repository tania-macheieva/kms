"""Демонстрація різниці OWL (відкритий світ) vs SHACL (закритий світ) на одних і тих самих даних.
1) HermiT щодо дефектного набору (3 вади SHACL) → очікується «узгоджено»;
2) варіант «неправильний тип»: VAR-107 locatedIn Olena → OWL може вивести, що Olena — Gene (range), SHACL — повідомляє про порушення sh:class."""
import json
import sys
from pathlib import Path

from rdflib import Graph, Namespace, RDF

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from reasoning import infer  # noqa: E402
import shacl_check  # noqa: E402

D = Namespace("http://example.org/dkh/onto#")
out = {}
valid = Graph().parse(ROOT / "data/kb.ttl", format="turtle")
bad = Graph().parse(ROOT / "data/kb_defective.ttl", format="turtle")
ok, inf, msg = infer(bad); out["hermit_defective"] = {"consistent": ok}
t = Graph().parse(ROOT / "data/kb.ttl", format="turtle")
t.remove((D["VAR-107"], D.locatedIn, None)); t.add((D["VAR-107"], D.locatedIn, D.Olena))
ok2, inf2, msg2 = infer(t)
out["hermit_wrong_type"] = {"consistent": ok2, "message": (msg2 or "")[:300], "olena_inferred_gene": (D.Olena, RDF.type, D.Gene) in inf2}
sok, srg = shacl_check.validate(t)
out["shacl_wrong_type"] = {"conforms": sok, "violations": [r for r in shacl_check.summarize(srg) if r["severity"] == "Violation"]}
(ROOT / "shapes/owl_vs_shacl.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
print(json.dumps(out, ensure_ascii=False, indent=1))
