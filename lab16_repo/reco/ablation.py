"""Ablation of the weighted hybrid with the weights tuned per seed on the validation window: drop each component (and use equal weights) -> eval/ablation.json"""
import json, glob, numpy as np, pathlib
from .eval import World, fit_and_eval, CUTOFF, DAYS, ROOT
from .models import Hybrid
import reco.eval as ev
res = {}
for f in sorted(glob.glob(str(ROOT / "eval/res_*.json"))):
    for s, r in json.load(open(f)).items():
        W = World(int(s)); P = r["params"]; base = P["hyb_w"]; out = {}
        variants = {"tuned": base, "without_graph": {**base, "graph": 0.0}, "without_knn": {**base, "knn": 0.0}, "without_popularity": {**base, "popularity": 0.0}, "equal(1,1,0.3)": dict(graph=1, knn=1, popularity=0.3)}
        for name, w in variants.items():
            p = json.loads(json.dumps(P)); p["hyb_w"] = w; o, users, pos, pop = fit_and_eval(W, CUTOFF, DAYS, p); out[name] = dict(ndcg10=float(o["hybrid-weighted"]["per_user"]["ndcg10"].mean()), p5=float(o["hybrid-weighted"]["per_user"]["p5"].mean()), coverage=o["hybrid-weighted"]["coverage"])
        res[s] = out; W.close(); print(s, {k: round(v["ndcg10"], 3) for k, v in out.items()}, flush=True)
agg = {k: {m: float(np.mean([res[s][k][m] for s in res])) for m in ("ndcg10", "p5", "coverage")} for k in res["0"]}
json.dump(dict(per_seed=res, mean=agg), open(ROOT / "eval/ablation.json", "w"), indent=1); print(json.dumps(agg, indent=1))
