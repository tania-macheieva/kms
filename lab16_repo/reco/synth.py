"""Synthetic interaction log (the Hub has no real users yet). Fully seeded; the generating process is documented in docs/reco_eval.md.
Latent structure: users have role + topic preferences; reading sessions follow a topic, move to the next section of the same document with p=0.4,
to another section of the same document with p=0.2, else to a popularity-weighted item of the topic. Items are visible only if the role may see them and they are verified.
NOTE: entities/graph edges are NOT used by the generator (only documents/topics), so a graph model has no built-in advantage from shared mentions.
Output rows: (user, role, item_id, day[0..83], hour)."""
from __future__ import annotations
import numpy as np, csv, collections, pathlib
from .data import allowed
TOPICS = {"pipelines": ["sarek_"], "rare": ["rare_"], "bcftools": ["bcftools_"], "gatk": ["gatk_readme", "gatk_mutect2", "gatk_docker", "gatk_cnv", "gatk_pathseq"], "annot": ["gatk_funco", "gatk_funcotator"], "hub": ["int_"]}
DAYS = 84
def topic_of(doc):
    for t, ps in TOPICS.items():
        if any(doc.startswith(p) for p in ps): return t
    return None
def generate(items, n_users=64, seed=0, join_late=0.25):
    rng = np.random.default_rng(seed); roles = (["reader"] * 36 + ["analyst"] * 18 + ["clinician"] * 10)[:n_users]
    by_doc = collections.defaultdict(list)
    for i, it in enumerate(items):
        if it["kind"] == "doc" and it["verified"] and topic_of(it["doc"]): by_doc[it["doc"]].append(i)
    for d in by_doc: by_doc[d].sort(key=lambda i: items[i]["id"])                      # chunk ids are ordered h000,h001,... inside a document
    pop_w = {}
    for d, idx in by_doc.items():                                                       # Zipf-like item popularity inside a topic, random ranks
        ranks = rng.permutation(len(idx)) + 1
        for i, r in zip(idx, ranks): pop_w[i] = 1.0 / r ** 0.9
    rows = []; profiles = []
    for u in range(n_users):
        role = roles[u]; tops = [t for t in TOPICS if any(allowed(items[i], role) for d, ix in by_doc.items() if topic_of(d) == t for i in ix)]
        pref = rng.dirichlet(np.full(len(tops), 0.35)); start = int(rng.integers(0, DAYS - 20)) if rng.random() < join_late else int(rng.integers(0, 10))
        n_sess = int(rng.poisson(9)) + 2; days = np.sort(rng.integers(start, DAYS, n_sess)); profiles.append(dict(user=f"u{u:03d}", role=role, topics=dict(zip(tops, pref.round(3).tolist())), first_day=int(days[0])))
        for d in days:
            t = rng.choice(tops, p=pref); docs = [dd for dd in by_doc if topic_of(dd) == t and any(allowed(items[i], role) for i in by_doc[dd])]
            cand = [i for dd in docs for i in by_doc[dd] if allowed(items[i], role)]; w = np.array([pop_w[i] for i in cand]); cur = cand[int(rng.choice(len(cand), p=w / w.sum()))]
            L = 2 + int(rng.geometric(0.28)); h = int(rng.integers(8, 20))
            for _ in range(min(L, 12)):
                rows.append((f"u{u:03d}", role, items[cur]["id"], int(d), h)); r = rng.random(); ix = by_doc[items[cur]["doc"]]; pos = ix.index(cur)
                if r < 0.4 and pos + 1 < len(ix) and allowed(items[ix[pos + 1]], role): cur = ix[pos + 1]
                elif r < 0.6: cur = [i for i in ix if allowed(items[i], role)][int(rng.integers(0, len([i for i in ix if allowed(items[i], role)])))]
                else: cur = cand[int(rng.choice(len(cand), p=w / w.sum()))]
    return rows, profiles
def save(rows, path):
    with open(path, "w", newline="", encoding="utf-8") as f: w = csv.writer(f); w.writerow(["user", "role", "item", "day", "hour"]); w.writerows(rows)
def load(path):
    return [(r["user"], r["role"], r["item"], int(r["day"]), int(r["hour"])) for r in csv.DictReader(open(path, encoding="utf-8"))]
