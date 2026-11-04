"""Fixed test subsets (seed 7): R2 = 10 queries, R3 = 20 queries (R2 subset + 10 more incl. 6 Ukrainian)."""
import json, random
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
G = [json.loads(l) for l in open(ROOT / "eval/gold.jsonl", encoding="utf-8")]
rnd = random.Random(7); by = lambda t: [g["qid"] for g in G if g["type"] == t]
r2 = rnd.sample(by("keyword"), 3) + rnd.sample(by("paraphrase"), 4) + rnd.sample(by("multi_step"), 3)
rest_en = [q for q in by("keyword") + by("paraphrase") if q not in r2]
r3 = r2 + rnd.sample(rest_en, 4) + rnd.sample(by("uk_cross"), 3) + rnd.sample(by("uk_internal"), 3)
json.dump(dict(r2=r2, r3=r3), open(ROOT / "eval/subsets.json", "w"), indent=1); print(len(r2), len(r3), r3)
