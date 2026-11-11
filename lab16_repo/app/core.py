"""Domain Knowledge Hub demonstrator core: search/ask with abstention + recommender with explanations + cold start. One process, embedded FalkorDB-lite, no external services."""
from __future__ import annotations
import json, re, pathlib, numpy as np
from rank_bm25 import BM25Okapi
from reco.data import load_items, load_embeddings, allowed, ROOT, AS_OF
from reco.entities import build_entities, extract, build_vocab
from reco.graphdb import ItemGraph
from reco.models import Popularity, GraphReco, KNNReco, Hybrid, recommend
from reco.synth import load as load_events, topic_of, TOPICS, DAYS
from reco.explain import explain, label
from reco.llm import ReplayLLM
from reco.guards import sanitize, INJECTION, output_guard
TOK = lambda s: re.findall(r"[a-zа-яіїєґ0-9\-]+", s.lower()); STOP = set("does use used using which would should can will you your my me we i not there any some all about between into than then so if when where who whom why "
          "the a an of to in on for and or is are was be what which how does do with from by at as it this that що які який як чи та і в на для з до про при".split())
class Hub:
    def __init__(self):
        self.items = load_items(); self.idx = {it["id"]: i for i, it in enumerate(self.items)}; self.E = load_embeddings(self.items); self.ent_of, self.idf, self.types = build_entities(self.items); self.G = ItemGraph(self.items, self.ent_of, self.idf, self.types)
        self.cfg = json.load(open(ROOT / "reco/config.json")); ev = ROOT / "data/interactions.csv"; self.events = load_events(ev) if ev.exists() else []
        self.bm = BM25Okapi([TOK(it["text"]) for it in self.items]); self.llm = ReplayLLM(); self.vocab = build_vocab(); self.rebuild()
    def rebuild(self):
        c = self.cfg; self.pop = Popularity(self.items, self.events); self.graph = GraphReco(self.G, self.items, **c["graph"]); self.knn = KNNReco(self.E, self.items, **c["knn"]); self.hyb = Hybrid(dict(graph=self.graph, knn=self.knn, popularity=self.pop), c["hyb_w"], "weighted")
        self.hist = {}; self.role = {}
        for u, role, it, day, h in sorted(self.events, key=lambda r: (r[3], r[4])): self.hist.setdefault(u, []).append((self.idx[it], day)); self.role[u] = role
    # ---- search / ask -------------------------------------------------------------------------------------------------------------------------
    def visible(self, role, verified_only=True): return [i for i, it in enumerate(self.items) if allowed(it, role) and (it["verified"] or not verified_only)]
    def search(self, q, role="reader", k=5):
        vis = self.visible(role); s = self.bm.get_scores(TOK(q)); order = sorted(vis, key=lambda i: -s[i])[:k]; return [dict(id=self.items[i]["id"], score=round(float(s[i]), 2), label=label(self.items[i]), source=self.items[i]["source_url"]) for i in order if s[i] > 0]
    def ask(self, q, role="reader"):
        """extractive answer with abstention: refuses prompt-injection-like queries, answers only if the best verified passage covers the query terms, else says it does not know"""
        if INJECTION.search(q): return dict(status="REFUSED", answer="Запит схожий на ін'єкцію інструкцій (спробу змінити правила або викрасти секрети); його не виконано.", reason="injection_filter", citations=[])
        terms = [t for t in TOK(q) if t not in STOP and len(t) > 1]; vis = self.visible(role); s = self.bm.get_scores(TOK(q)); order = sorted(vis, key=lambda i: -s[i])[:3]
        if not terms or not order: return dict(status="NO_ANSWER", answer="Не знаю: у Hub немає підтверджених джерел за цим запитом.", reason="no_candidates", citations=[])
        best = order[0]; ptoks = set(TOK(self.items[best]["text"])); cov = sum(t in ptoks for t in terms) / len(terms)
        if cov < 0.6 or s[best] < 8: return dict(status="NO_ANSWER", answer="Не знаю: у підтверджених джерелах Hub немає відповіді (покриття термінів запиту %.0f%%, найкращий BM25 %.1f)." % (100 * cov, s[best]), reason="low_coverage", citations=[], coverage=round(cov, 2))
        clean, flagged = sanitize(self.items[best]["text"]); sents = [x.strip() for x in re.split(r"(?<=[.!?])\s+|\n", clean) if len(x.strip()) > 20]; sc = [sum(t in set(TOK(x)) for t in terms) for x in sents]; pick = [sents[j] for j in np.argsort(sc)[::-1][:2] if sc[j] > 0]
        ans, why = output_guard(" ".join(pick) if pick else clean[:300]); return dict(status="ANSWER", answer=ans, reason="; ".join(why) or "ok", citations=[dict(id=self.items[best]["id"], source=self.items[best]["source_url"], verified=self.items[best]["verified"])], coverage=round(cov, 2), injection_removed=flagged)
    # ---- recommendations ----------------------------------------------------------------------------------------------------------------------
    def _explained(self, recs, hist, now, with_para=True):
        out = []
        for c in recs:
            p = self.graph.explain_path(c, hist, now) or self.knn.explain_path(c, hist, now); e = explain(self.items, c, p, self.llm if with_para else None); out.append(dict(id=self.items[c]["id"], label=label(self.items[c]), explanation=e["final"], explanation_source=e["used"], path_kind=e["facts"]["kind"]))
        return out
    def recommend_user(self, user, k=5, role=None, max_age_days=None):
        if user not in self.hist: raise KeyError(user)
        role = role or self.role[user]; h = self.hist[user]; seen = {i for i, _ in h}; recs = recommend(self.hyb, self.items, role, h, DAYS, seen, k=k, max_age_days=max_age_days, as_of=AS_OF); return dict(user=user, role=role, history=[label(self.items[i]) for i, _ in h[-5:]], recommendations=self._explained(recs, h, DAYS))
    def recommend_new_user(self, role="reader", topics=(), history_ids=(), k=5):
        """cold start for a new user: declared topics -> topic-popularity; with history items -> hybrid on that history"""
        h = [(self.idx[i], DAYS) for i in history_ids if i in self.idx]; seen = {i for i, _ in h}
        if h: recs = recommend(self.hyb, self.items, role, h, DAYS, seen, k=k); return dict(strategy="hybrid on declared history", recommendations=self._explained(recs, h, DAYS))
        from reco.cold import TopicPop
        m = TopicPop(self.items, self.pop, [t for t in topics if t in TOPICS]) if topics else self.pop; recs = recommend(m, self.items, role, [], DAYS, set(), k=k)
        rows = []
        for c in recs:
            lab = label(self.items[c]); t = topic_of(self.items[c]["doc"]); f = dict(cand=self.items[c]["id"], cand_label=lab, kind="topic" if topics and t in topics else "popular", topic=t)
            from reco.explain import template; rows.append(dict(id=self.items[c]["id"], label=lab, explanation=template(f), explanation_source="template", path_kind=f["kind"]))
        return dict(strategy="topic-popularity" if topics else "global popularity", recommendations=rows)
    def add_document(self, doc_id, section, text, sensitivity="public", role_checked="reader"):
        """cold start for a new item: insert into the item graph (entities, same-doc, NEXT edges), embed with the same encoder is NOT done here (no model in the image) -> kNN has no vector, the item is reachable through the graph"""
        it = dict(id=doc_id, doc=doc_id.split("#")[0], title=doc_id.split("#")[0], section=section, type="note", date=AS_OF.isoformat(), sensitivity=sensitivity, source_url="local:user-upload", text=text, verified=False, kind="fixture")
        ents = extract(text, self.vocab); ents = {n: t for n, t in ents.items() if n in self.idf}; self.items.append(it); self.idx[doc_id] = len(self.items) - 1; self.ent_of.append(ents)
        self.E = np.vstack([self.E, np.zeros((1, self.E.shape[1]), np.float32)]); self.G.add_item(it, ents, self.idf, self.types); self.bm = BM25Okapi([TOK(i["text"]) for i in self.items]); self.knn.E = self.E; return dict(id=doc_id, entities=sorted(ents), verified=False, note="new items are unverified until a curator approves; default recommendations (verified_only) do not show them")
