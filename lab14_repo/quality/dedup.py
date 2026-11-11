"""Entity resolution (de-duplication) of chunks.
Pipeline: normalise -> blocking (inverted index on word 5-shingles) -> compare (string: rapidfuzz; sparse: TF-IDF cosine;
dense: bge embedding cosine; attributes: same doc / section tail / length ratio / sensitivity) -> decision (threshold tuned on dev,
borderline zone -> LLM judge) -> merge with provenance (merged_from) -> unmerge."""
from __future__ import annotations
import re, copy, pathlib, itertools, collections, hashlib
import numpy as np
from rapidfuzz import fuzz
from sklearn.feature_extraction.text import TfidfVectorizer
from .common import ROOT, STORE, chunks, manifest

WEIGHTS = dict(tfidf=.35, emb=.25, fuzz=.25, ratio=.15)
MD = re.compile(r"[`*_>#|\[\]()~]|^\s*[-+]\s+|^\s*\d+\.\s+", re.M)

def normalise(text: str) -> str:
    """Drop the synthetic first line ('doc — section') and heading lines, strip markdown, lowercase, collapse whitespace."""
    lines = text.split("\n")[1:]
    lines = [l for l in lines if not l.lstrip().startswith("#")]
    t = MD.sub(" ", "\n".join(lines)).lower()
    return re.sub(r"\s+", " ", t).strip()

def shingles(norm: str, n=5):
    w = norm.split()
    return {hash(" ".join(w[i:i + n])) & 0xFFFFFFFF for i in range(max(len(w) - n + 1, 0))} if len(w) >= n else {hash(norm) & 0xFFFFFFFF}

def tail(section: str) -> str: return section.split(">")[-1].strip().lower()

class Store:
    def __init__(self, drop_ids=(), store=STORE):
        store = pathlib.Path(store); self.all = chunks(store); Eb = np.load(STORE / "emb_bge.npy"); idmap = {c["chunk_id"]: i for i, c in enumerate(chunks(STORE))}
        # embeddings are cached for the baseline snapshot; chunks unknown to it (newly added) get a zero vector (string features still apply)
        E = np.vstack([Eb[idmap[c["chunk_id"]]] if c["chunk_id"] in idmap else np.zeros(Eb.shape[1], dtype=Eb.dtype) for c in self.all])
        drop = set(drop_ids); keep = [i for i, c in enumerate(self.all) if c["chunk_id"] not in drop]
        self.c = [self.all[i] for i in keep]; self.E = E[keep] / np.maximum(np.linalg.norm(E[keep], axis=1, keepdims=True), 1e-9)
        self.norm = [normalise(c["text"]) for c in self.c]
        self.idx = {c["chunk_id"]: i for i, c in enumerate(self.c)}
        self.T = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True).fit_transform(self.norm)

def blocking(S: Store, min_shared=2, max_block=60):
    """Token blocking: chunks sharing >= min_shared word 5-shingles become a candidate pair (avoids comparing all O(n^2) pairs)."""
    inv = collections.defaultdict(list)
    for i, n in enumerate(S.norm):
        for h in shingles(n): inv[h].append(i)
    cnt = collections.Counter()
    for ids in inv.values():
        if 1 < len(ids) <= max_block:
            for a, b in itertools.combinations(ids, 2): cnt[(a, b)] += 1
    return sorted(p for p, n in cnt.items() if n >= min_shared)

def features(S: Store, a: int, b: int) -> dict:
    na, nb = S.norm[a], S.norm[b]; ca, cb = S.c[a], S.c[b]
    la, lb = len(na), len(nb)
    return dict(fuzz=fuzz.token_set_ratio(na, nb) / 100, ratio=fuzz.ratio(na, nb) / 100,
                tfidf=float((S.T[a].multiply(S.T[b])).sum()), emb=float(S.E[a] @ S.E[b]),
                same_doc=ca["doc_id"] == cb["doc_id"], tail_eq=tail(ca["section"]) == tail(cb["section"]),
                same_sens=ca["sensitivity"] == cb["sensitivity"], len_ratio=min(la, lb) / max(la, lb, 1))

def score(f: dict) -> float:
    s = sum(WEIGHTS[k] * f[k] for k in WEIGHTS)
    return s * 0.85 if f["len_ratio"] < 0.5 else s      # very different lengths -> one chunk is a part of the other, not a duplicate

def single(f: dict, key="tfidf") -> float: return f[key]

def decide(f: dict, th: float) -> bool:
    """Automatic decision: score >= th AND the same sensitivity label (never silently merge across access levels)."""
    return f["same_sens"] and score(f) >= th

# ---------------- merge with provenance / unmerge ----------------
PRIO = {"public": 0, "internal": 1, "restricted": 2}
def canonical_choice(group: list[dict]) -> dict:
    """public > internal > restricted (never hide a public chunk behind a restricted one), then longest, then smallest id."""
    return sorted(group, key=lambda c: (PRIO.get(c["sensitivity"], 9), -len(c["text"]), c["chunk_id"]))[0]

def clusters(pairs, ids):
    p = {i: i for i in ids}
    def f(x):
        while p[x] != x: p[x] = p[p[x]]; x = p[x]
        return x
    for a, b in pairs: p[f(a)] = f(b)
    g = collections.defaultdict(list)
    for i in ids: g[f(i)].append(i)
    return [sorted(v) for v in g.values() if len(v) > 1]

def merge(all_chunks, pairs, man=None):
    """Returns (merged chunk list, log). The canonical chunk keeps `merged_from` = full records of the absorbed chunks
    (so nothing is lost and unmerge() is exact); the log records who/when/why."""
    by = {c["chunk_id"]: c for c in all_chunks}; out = {k: copy.deepcopy(v) for k, v in by.items()}; log = []
    for g in clusters(pairs, list(by)):
        canon = canonical_choice([by[i] for i in g]); abs_ = [i for i in g if i != canon["chunk_id"]]
        out[canon["chunk_id"]]["merged_from"] = [copy.deepcopy(by[i]) for i in abs_]
        for i in abs_: del out[i]
        log.append(dict(canonical=canon["chunk_id"], absorbed=abs_, docs=sorted({by[i]["doc_id"] for i in g}), rule="threshold/judge",
                        text_sha256={i: hashlib.sha256(by[i]["text"].encode()).hexdigest()[:16] for i in g}))
    order = [c["chunk_id"] for c in all_chunks if c["chunk_id"] in out]
    return [out[i] for i in order], log

def unmerge(merged, canonical_id):
    """Restore the absorbed chunks of one cluster (exact original records)."""
    res = []
    for c in merged:
        if c["chunk_id"] == canonical_id and c.get("merged_from"):
            c = copy.deepcopy(c); back = c.pop("merged_from"); res.append(c); res += back
        else: res.append(c)
    return res


# ---------------- decision rule (shared by run_dedup.py and quality/profile.py) ----------------
def rule(S, a, b, th, band, judged=None, use_judge=True):
    """(is_dup, reason). judged: {frozenset({id_a,id_b}): 'DUP'|'RELATED'} verdicts of the LLM judge for the borderline zone."""
    f = features(S, a, b); s = score(f)
    if not f["same_sens"]: return False, "sensitivity"
    if S.norm[a] == S.norm[b]: return True, "exact_text"
    if s >= th + band: return True, "threshold"
    if abs(s - th) <= band:
        lab = (judged or {}).get(frozenset((S.c[a]["chunk_id"], S.c[b]["chunk_id"])))
        return (lab == "DUP", "judge") if (use_judge and lab) else (False, "borderline_unjudged")
    return False, "below"

def find_pairs(S, th, band, judged=None):
    out = []
    for a, b in blocking(S):
        ok, why = rule(S, a, b, th, band, judged)
        if ok: out.append((S.c[a]["chunk_id"], S.c[b]["chunk_id"], why))
    return out
