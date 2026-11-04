"""Імпорт карти-«замінника колеги» (сирий вихід незалежного LLM-запуску) у формат карт → models/cmap_peer.{json,png}."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from map_tools import REL, ROOT, load_map, render_png, stats, taxonomy_info   # noqa: E402

raw = json.loads((ROOT / "llm_log/raw/step4_peer_map_raw_output.json").read_text(encoding="utf-8"))
exp = {c["label"]: c["cluster"] for c in load_map(ROOT / "models/cmap_expert.json")["concepts"] if c["kind"] == "concept"}
tax = taxonomy_info()
concepts = []
for c in raw["concepts"]:
    concepts.append({"id": c["id"], "label": c["label"], "kind": c["kind"], "cluster": exp.get(c["label"], "X"),
                     "type": tax.get(c["label"], {}).get("type"), "definition": c.get("definition", ""),
                     "in_vocabulary": c["label"] in tax})
props = [{"id": p["id"], "s": p["s"], "p": p["p"], "o": p["o"], "cross": bool(p.get("cross")), "explanation": p.get("explanation", "")} for p in raw["propositions"]]
assert all(p["p"] in REL for p in props)
m = {"title": "Карта-замінник колеги (LLM, незалежний запуск)", "concepts": concepts, "propositions": props}
(ROOT / "models/cmap_peer.json").write_text(json.dumps(m, ensure_ascii=False, indent=1), encoding="utf-8")
render_png(m, ROOT / "models/cmap_peer.png", "Карта-замінник колеги (LLM)")
s = stats(m); s["in_vocabulary"] = sum(1 for c in concepts if c["in_vocabulary"])
print(json.dumps(s, ensure_ascii=False))
