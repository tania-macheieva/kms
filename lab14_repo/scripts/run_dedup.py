"""Final decision rule applied to the whole store + evaluation on the gold pairs + merge/unmerge demo.
Rule: (1) different sensitivity -> never merge; (2) identical normalised text -> DUP (deterministic); (3) score >= th+band -> DUP;
(4) |score-th| <= band -> verdict of the LLM judge (llm_log/raw/pairs_judge.json); (5) otherwise keep.
Writes store_clean/corpus.jsonl (merged), quality/merge_log.jsonl, eval/dedup_apply.json, eval/dedup_eval_judge.json."""
import sys, json, csv, pathlib, collections
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from quality.dedup import *
from quality.dedup import rule as rule_
E = json.load(open(ROOT / "eval/dedup_eval.json")); th, band = E["threshold"], E["borderline_band"]
meta = json.load(open(ROOT / "data/judge_pairs_meta.json")); J = {x["pair_id"]: x for x in json.load(open(ROOT / "llm_log/raw/pairs_judge.json"))}
judged = {frozenset((p["a"], p["b"])): J[p["pair_id"]]["label"] for p in meta["judge_pairs"]}
S = Store(); P = blocking(S)
def rule(a, b, use_judge=True): return globals()['rule_'](S, a, b, th, band, judged, use_judge)
pairs = []; why = collections.Counter(); unj = 0
for a, b in P:
    ok, w = rule(a, b)
    if w == "borderline_unjudged": unj += 1
    if ok: pairs.append((S.c[a]["chunk_id"], S.c[b]["chunk_id"])); why[w] += 1
# ---- evaluation of the full pipeline (rule+judge) on gold test and dev ----
gold = list(csv.DictReader(open(ROOT / "quality/pairs_gold.csv", encoding="utf-8"))); idx = S.idx
def evalset(split, use_judge):
    tp = fp = fn = 0
    for r in gold:
        if r["split"] != split: continue
        ok, _ = rule(idx[r["a"]], idx[r["b"]], use_judge); d = int(r["dup"])
        tp += ok and d; fp += ok and not d; fn += (not ok) and d
    p = tp / (tp + fp) if tp + fp else 1; rc = tp / (tp + fn) if tp + fn else 0
    return dict(tp=tp, fp=fp, fn=fn, precision=round(p, 3), recall=round(rc, 3), f1=round(2 * p * rc / (p + rc), 3) if p + rc else 0)
ev = {sp: dict(with_judge=evalset(sp, True), rule_without_judge=evalset(sp, False)) for sp in ("dev", "test")}
# judge agreement with gold on the pairs both cover
gl = {frozenset((r["a"], r["b"])): r for r in gold}; ag = [(k, judged[k], gl[k]["label"]) for k in judged if k in gl]
jv = dict(judge_pairs=len(judged), in_gold=len(ag), agree_binary=sum((j == "DUP") == (g == "DUP") for _, j, g in ag), disagree=[(sorted(k), j, g) for k, j, g in ag if (j == "DUP") != (g == "DUP")],
          judge_dup=sum(v == "DUP" for v in judged.values()), judge_related=sum(v == "RELATED" for v in judged.values()))
json.dump(dict(rule_evaluation=ev, judge_vs_gold=jv), open(ROOT / "eval/dedup_eval_judge.json", "w"), indent=1)
# ---- apply ----
by = {c["chunk_id"]: c for c in chunks()}; man = manifest(); merged, log = merge(chunks(), pairs, man)
for g in log: ids = [g["canonical"]] + g["absorbed"]; g["min_pair_score"] = round(min(score(features(S, S.idx[x], S.idx[y])) for x in ids for y in ids if x < y), 3)
(ROOT / "store_clean").mkdir(exist_ok=True)
with open(ROOT / "store_clean/corpus.jsonl", "w", encoding="utf-8") as f:
    for c in merged: f.write(json.dumps(c, ensure_ascii=False) + "\n")
with open(ROOT / "quality/merge_log.jsonl", "w", encoding="utf-8") as f:
    for g in log: f.write(json.dumps(g, ensure_ascii=False) + "\n")
cid = log[0]["canonical"]; restored = unmerge(merged, cid)
ok1 = {c["chunk_id"] for c in restored} >= {cid, *log[0]["absorbed"]} and all(next(r for r in restored if r["chunk_id"] == a)["text"] == by[a]["text"] for a in log[0]["absorbed"])
allun = merged
for g in log: allun = unmerge(allun, g["canonical"])
summ = dict(threshold=th, band=band, merge_pairs=len(pairs), by_rule=dict(why), clusters=len(log), absorbed=sum(len(g["absorbed"]) for g in log), chunks_before=len(by), chunks_after=len(merged),
            sizes=dict(collections.Counter(len(g["absorbed"]) + 1 for g in log)), min_cluster_score=min(g["min_pair_score"] for g in log), borderline_unjudged=unj,
            unmerge_one_cluster=bool(ok1), unmerge_all_restores_original=bool(sorted(c["chunk_id"] for c in allun) == sorted(by) and all(c == by[c["chunk_id"]] for c in allun)),
            demo=dict(canonical=cid, absorbed=log[0]["absorbed"]))
json.dump(summ, open(ROOT / "eval/dedup_apply.json", "w"), indent=1); print(json.dumps(summ, indent=1)); print(json.dumps(dict(rule_evaluation=ev, judge_vs_gold=jv), indent=1))
