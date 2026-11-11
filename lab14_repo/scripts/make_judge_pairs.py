"""All borderline pairs of the whole store (|score - th| <= band, same sensitivity, texts not identical after normalisation) -> blind judge batch."""
import sys, json, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from quality import dedup as D
from quality.common import ROOT
E = json.load(open(ROOT / "eval/dedup_eval.json")); th, band = E["threshold"], E["borderline_band"]
S = D.Store(); P = D.blocking(S); jp = []; auto = []; sens_blocked = []; nj = 0
for a, b in P:
    f = D.features(S, a, b); s = D.score(f)
    if abs(s - th) > band and s < th: continue
    if s >= th + band and S.norm[a] != S.norm[b]: pass
    if not f["same_sens"]: sens_blocked.append((S.c[a]["chunk_id"], S.c[b]["chunk_id"], round(s, 3))); continue
    if S.norm[a] == S.norm[b]: auto.append((S.c[a]["chunk_id"], S.c[b]["chunk_id"])); continue
    if abs(s - th) <= band:
        nj += 1; jp.append(dict(pair_id=f"JP{nj:03d}", a=S.c[a]["chunk_id"], b=S.c[b]["chunk_id"], score=round(s, 4),
                                A=dict(id=S.c[a]["chunk_id"], doc=S.c[a]["doc_id"], section=S.c[a]["section"], text=S.c[a]["text"]), B=dict(id=S.c[b]["chunk_id"], doc=S.c[b]["doc_id"], section=S.c[b]["section"], text=S.c[b]["text"])))
    # pairs above th+band that are not identical: auto-merged by threshold
json.dump([{k: v for k, v in p.items() if k != "score"} for p in jp], open(ROOT / "llm_log/in/pairs_judge.json", "w"), ensure_ascii=False, indent=0)
json.dump(dict(judge_pairs=[{k: p[k] for k in ("pair_id", "a", "b", "score")} for p in jp], exact_text_rule=auto, sensitivity_blocked=sens_blocked), open(ROOT / "data/judge_pairs_meta.json", "w"), indent=1)
print(len(jp), "to judge;", len(auto), "exact-text auto DUP;", len(sens_blocked), "blocked by sensitivity")
