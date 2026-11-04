"""Парсинг rdflib без помилок (R2 C4): команда + вивід → docs/evidence/rdflib_parse.txt"""
import sys
from pathlib import Path

import rdflib

ROOT = Path(__file__).resolve().parents[1]
out = [f"rdflib {rdflib.__version__}"]
for f in ("models/onto.owl", "models/onto_data.ttl", "models/llm_draft.ttl", "models/onto_inferred.ttl"):
    g = rdflib.Graph().parse(ROOT / f, format="turtle")
    out.append(f"python -c \"import rdflib; g=rdflib.Graph().parse('{f}', format='turtle'); print(len(g))\"  →  {len(g)} триплетів, помилок немає")
(ROOT / "docs/evidence/rdflib_parse.txt").write_text("\n".join(out) + "\n", encoding="utf-8")
print("\n".join(out))
