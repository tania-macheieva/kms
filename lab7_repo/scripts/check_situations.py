"""Результат 4, C4: SPARQL-запити до індивідів (з виведеннями HermiT), що перевіряють шаблони ситуацій → docs/situations_check.md"""
import csv
import sys
from pathlib import Path

from rdflib.namespace import OWL

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from reasoning import infer   # noqa: E402
from run_cq import load       # noqa: E402

g = load("mine"); ok, inf, _ = infer(g); g += inf
PRE = "PREFIX dkh: <http://example.org/dkh/onto#>\nPREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>\nPREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>\n"
Q = PRE + """SELECT ?xl ?al ?nl WHERE {
  dkh:Situation_%s dkh:guardClass ?c ; dkh:hasAction ?a ; dkh:hasNewState ?n .
  ?x rdf:type ?c ; rdfs:label ?xl . ?a rdfs:label ?al . ?n rdfs:label ?nl }
ORDER BY ?xl"""
EXP = {"S01": ["VAR-002"], "S02": ["VAR-004"], "S03": ["VAR-004"], "S04": ["HBOC-panel"], "S05": ["Andrii", "Halyna", "Iryna", "Marta", "Petro"], "S06": ["Sofiia"]}
sit = {r["id"]: r for r in csv.DictReader(open(ROOT / "models/situations.csv", encoding="utf-8-sig"))}
L = ["# Перевірка шаблонів ситуацій запитами", "", "Запити виконано до `models/onto.owl` + `models/onto_data.ttl` + виведених HermiT типів. Для кожного шаблона: guard-клас → індивіди, які йому відповідають, і дія/новий стан шаблона.", ""]
allok = True
for sid, exp in EXP.items():
    rows = list(g.query(Q % sid))
    got = sorted({str(r[0]) for r in rows}); acts = sorted({str(r[1]) for r in rows}); news = sorted({str(r[2]) for r in rows})
    passed = got == sorted(exp); allok &= passed
    main = sid in ("S01", "S06")
    L += [f"## {sid} — {sit[sid]['name']}{' (основна перевірка)' if main else ''}", "", f"Guard: {sit[sid]['guard']}; клас: `{sit[sid]['guard_class']}`.", "", "```sparql", (Q % sid).replace(PRE, "").strip(), "```", "",
          f"Результат: індивіди {got}; дія {acts}; новий стан {news}. Очікувалось {sorted(exp)} → **{'збіг' if passed else 'НЕ збіг'}**.", ""]
(ROOT / "docs/situations_check.md").write_text("\n".join(L), encoding="utf-8")
print("all ok" if allok else "MISMATCH")
sys.exit(0 if allok else 1)
