"""Quality profile of a store: 14 metrics (thresholds.json) + verdicts. CLI: python quality/profile.py --store store --label baseline [--sample llm_log/raw/accuracy_expert.json ...]"""
import sys, json, re, csv, argparse, pathlib, datetime, collections
import numpy as np
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from quality.common import ROOT, chunks, graph_csv, read_jsonl
from quality import dedup as D, conflicts as C
import jsonschema
from sklearn.feature_extraction.text import TfidfVectorizer
REQ = ["chunk_id", "doc_id", "title", "section", "type", "date", "sensitivity", "source_url", "lang", "text"]
TODAY = datetime.date(2026, 11, 6)
def dedup_params(): E = json.load(open(ROOT / "eval/dedup_eval.json")); return E["threshold"], E["borderline_band"]
def judged_map():
    meta = json.load(open(ROOT / "data/judge_pairs_meta.json")); J = {x["pair_id"]: x["label"] for x in json.load(open(ROOT / "llm_log/raw/pairs_judge.json"))}
    return {frozenset((p["a"], p["b"])): J[p["pair_id"]] for p in meta["judge_pairs"]}
def norm(s): return re.sub(r"\s+", " ", s).strip()
def resolved(sd, cf):
    sd = pathlib.Path(sd)
    alts = {c["conflict_id"] for c in read_jsonl(sd / "alternatives.jsonl")} if (sd / "alternatives.jsonl").exists() else set()
    al = open(sd / "aliases.csv", encoding="utf-8").read() if (sd / "aliases.csv").exists() else ""
    if cf["type"] in ("value", "temporal"): return cf["id"] in alts
    if cf["type"] == "terminological": return all(any(x["value"] in line for line in al.splitlines()) or cf["id"] == "CF-ASM-GRCh37" and "skos:closeMatch" in al for x in cf["items"])
    return False
def metrics(sd, sample_files=()):
    sd = pathlib.Path(sd); ch = chunks(sd); n = len(ch); M = {}
    M["M01_completeness"] = sum(all(str(c.get(k, "")).strip() for k in REQ) for c in ch) / n
    sch = json.load(open(ROOT / "schema/chunk.schema.json")); v = jsonschema.Draft202012Validator(sch)
    M["M02_schema_validity"] = sum(not list(v.iter_errors(c)) for c in ch) / n
    cfs = C.detect(sd); open_ = [c for c in cfs if not resolved(sd, c)]
    M["M03_open_conflicts"] = len(open_)
    M["M04_active_logical_violations"] = sum(c["type"] == "logical" for c in cfs)
    dec = {r["conflict_id"] for r in csv.DictReader(open(ROOT / "quality/decisions.csv", encoding="utf-8"))}
    all_cf = {c["id"] for c in C.detect(ROOT / "store")}   # conflicts that exist in the data universe
    det = {c["id"]: c for c in cfs}   # a conflict that is no longer detected on this store (e.g. the violating edge was removed) counts as resolved
    M["M07_conflict_documentation"] = sum(cid in dec and (cid not in det or resolved(sd, det[cid])) for cid in all_cf) / len(all_cf)
    # provenance fidelity: the source span of every chunk is contained in its text
    docs = {}; ok = 0
    for c in chunks(sd):
        for x in [c] + c.get("merged_from", []):
            d = docs.setdefault(x["doc_id"], (ROOT / "store/docs_clean" / f"{x['doc_id']}.md").read_text(encoding="utf-8")); ok += norm(d[x["start"]:x["end"]]) in norm(x["text"])
    tot = sum(1 + len(c.get("merged_from", [])) for c in ch); M["M05_provenance_fidelity"] = ok / tot
    th, band = dedup_params(); S = D.Store(store=sd); pairs = D.find_pairs(S, th, band, judged_map())
    M["M08_near_duplicate_share"] = len({b for _, b, _ in pairs}) / n
    M["M09_freshness"] = sum(bool(re.match(r"\d{4}-\d{2}-\d{2}$", c["date"])) and (TODAY - datetime.date.fromisoformat(c["date"])).days <= 365 for c in ch) / n
    M["M10_id_uniqueness"] = len({c["chunk_id"] for c in ch}) / n
    nodes = {}
    for f in (sd / "graph").glob("nodes_*.csv"):
        lab = f.stem.split("_", 1)[1]; rows = list(csv.DictReader(open(f))); key = list(rows[0])[0]; nodes[lab] = {r[key] for r in rows}
    allk = set().union(*nodes.values()); tr = okr = 0
    for f in (sd / "graph").glob("rels_*.csv"):
        for r in csv.DictReader(open(f)): tr += 1; okr += r["from"] in allk and r["to"] in allk
    M["M11_graph_referential_integrity"] = okr / tr
    M["M12_sensitivity_valid"] = sum(c["sensitivity"] in ("public", "internal", "restricted") for c in ch) / n
    def cyr(t): L = [ch_ for ch_ in t if ch_.isalpha()]; return sum("Ѐ" <= ch_ <= "ӿ" for ch_ in L) / max(len(L), 1)
    M["M13_language_consistency"] = sum((cyr(c["text"]) > .3) == (c["lang"] == "uk") for c in ch) / n
    # M14 self retrieval@1
    allc = ch; vec = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True); X = vec.fit_transform([D.normalise(c["text"]) for c in allc]); hit = 0; tot = 0
    for i, c in enumerate(allc):
        t = D.normalise(c["text"]); mid = len(t) // 2; q = vec.transform([t[max(0, mid - 100): mid + 100]]); top = int(np.argmax((X @ q.T).toarray().ravel())); tot += 1; hit += top == i
    M["M14_self_retrieval_at1"] = hit / tot
    # M06 from expert files (later files override earlier ones, by chunk_id)
    rec = {}
    for f in sample_files:
        for x in json.load(open(f)): rec[x["n"]] = x   # sample record number; later files override earlier ones
    if rec: M["M06_expert_sample_accuracy"] = sum(x["meta_ok"] and x["text_ok"] for x in rec.values()) / len(rec)
    return M, dict(n_chunks=n, conflicts=[c["id"] for c in cfs], open_conflicts=[c["id"] for c in open_], expert_n=len(rec))
OPS = {">=": lambda a, b: a >= b - 1e-12, "<=": lambda a, b: a <= b + 1e-12}
def verdicts(M):
    T = json.load(open(ROOT / "quality/thresholds.json")); return {k: dict(value=round(v, 4), op=T[k]["op"], threshold=T[k]["threshold"], dimension=T[k]["dimension"], severity=T[k]["severity"], ok=bool(OPS[T[k]["op"]](v, T[k]["threshold"]))) for k, v in M.items()}
if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--store", required=True); ap.add_argument("--label", required=True); ap.add_argument("--sample", nargs="*", default=[]); a = ap.parse_args()
    M, info = metrics(ROOT / a.store, [ROOT / s for s in a.sample]); V = verdicts(M)
    import hashlib; sha = hashlib.sha256(open(ROOT / a.store / "corpus.jsonl", "rb").read()).hexdigest()[:16]
    json.dump(dict(label=a.label, version=f"{a.label}-{sha}", date=str(TODAY), store=a.store, corpus_sha256_16=sha, info=info, metrics=V), open(ROOT / f"quality/metrics_{a.label}.json", "w"), indent=1)
    for k, v in V.items(): print(f"{k:34s} {v['value']:>8} {v['op']} {v['threshold']:<5} {'ok' if v['ok'] else 'FAIL (' + v['severity'] + ')'}")
