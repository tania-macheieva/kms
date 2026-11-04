"""RAG pipeline: question -> pre-filter by role -> hybrid retrieval (BM25 + dense, RRF) -> [reranker] -> (+ graph sub-graph) -> prompt -> LLM -> checks -> log."""
from __future__ import annotations
import json, re, time, uuid, datetime as dt
from dataclasses import dataclass, field, asdict
from pathlib import Path
from . import chunking, hybrid
from .embed import Embedder
from .graph_context import GraphContextBuilder, ROLE_MAX
from .llm import count_tokens

ROOT = Path(__file__).resolve().parents[1]
PROMPT_FILE = ROOT / "prompts" / "rag_v1.md"
LOG_FILE = ROOT / "logs" / "rag_log.jsonl"
SENS_FOR_ROLE = {"reader": ["public"], "analyst": ["public", "internal"], "clinician": ["public", "internal", "restricted"]}
CITE = re.compile(r"\[([^\[\]\n]{2,80}?)\]")
LEAK = re.compile(r"(sk-[A-Za-z0-9_\-]{16,}|\bapi[_ -]?key\s*[:=]\s*\S{8,}|##\s*Output format \(strict\)|Grounding\.\s+Use only facts|Never reveal these rules)", re.I)   # real secrets / verbatim system-prompt text, not mere mentions


def load_prompt(path: Path = PROMPT_FILE):
    t = path.read_text(encoding="utf-8"); sysm = t.split("# SYSTEM", 1)[1].split("# USER", 1)[0].strip(); usr = t.split("# USER", 1)[1].strip()
    return sysm, usr


@dataclass
class Config:
    k: int = 5                 # context chunks passed to the LLM
    rerank: bool = True        # MaxSim reranker over the top-30 hybrid candidates
    rerank_in: int = 30
    use_graph: bool = True
    prompt_file: Path = PROMPT_FILE
    name: str = "A"


@dataclass
class RagResult:
    qid: str
    question: str
    role: str
    config: str
    answer: str = ""
    status: str = ""
    sources: list = field(default_factory=list)          # [{id, kind, doc_id, section, sensitivity, source_url, score}]
    context_ids: list = field(default_factory=list)
    cited: list = field(default_factory=list)
    invalid_citations: list = field(default_factory=list)
    uncited_sentences: int = 0
    guard: str = ""
    in_tokens: int = 0
    out_tokens: int = 0
    latency: dict = field(default_factory=dict)
    backend: str = ""
    model: str = ""
    graph: dict = field(default_factory=dict)
    prompt_user: str = ""
    prompt_system: str = ""


def check_citations(body: str, valid_ids: set):
    """Automatic citation check (V1): every [id] must be an id from the supplied context; also counts uncited factual sentences."""
    cited, bad = [], []
    for m in CITE.finditer(body):
        for part in re.split(r"\s*[,;]\s*", m.group(1)):
            part = part.strip()
            if part:
                (cited if part in valid_ids else bad).append(part)
    sents = [s.strip() for s in re.split(r"(?<=[.!?])\s+|\n+", body) if len(s.strip()) > 30]
    uncited = sum(1 for s in sents if not any(
        part.strip() in valid_ids
        for m in CITE.finditer(s)
        for part in re.split(r"\s*[,;]\s*", m.group(1))
    ))
    return cited, bad, uncited


def parse_status(text: str):
    m = re.match(r"\s*STATUS:\s*(ANSWER|NO_ANSWER|CONFLICT)\s*\n?(.*)", text, re.S)
    return (m.group(1), m.group(2).strip()) if m else ("MALFORMED", text.strip())


class RAG:
    def __init__(self, llm, model="bge", graph: GraphContextBuilder | None = None, log=True):
        docs = hybrid.load_docs(); self.docs = {d["doc_id"]: d for d in docs}
        ch = chunking.chunk_corpus(docs, "heading", max_words=250, min_words=40)
        self.ret = hybrid.Retriever(ch, docs, model, tag="heading-250"); self.chunk_by_id = {c.id: i for i, c in enumerate(self.ret.chunks)}
        self.graph = graph; self.llm = llm; self.log = log; self.system, self.user_tpl = load_prompt()

    # ---- retrieval --------------------------------------------------------------------------------------------
    def retrieve(self, question, role, cfg: Config):
        pred = hybrid.make_pred(sensitivity=SENS_FOR_ROLE[role]); t0 = time.perf_counter()
        if cfg.rerank: hits = self.ret.search(question, "hybrid_rerank", cfg.k, pred, rerank_in=cfg.rerank_in)
        else: hits = self.ret.search(question, "hybrid", cfg.k, pred)
        return hits, (time.perf_counter() - t0) * 1000

    def source_of(self, row, score):
        c, m = self.ret.chunks[row], self.ret.metas[row]
        return dict(id=c.id, kind="text", doc_id=c.doc_id, section=c.section, type=m["type"], sensitivity=m["sensitivity"], source_url=self.docs[c.doc_id]["source_url"], score=round(score, 4))

    def get_source(self, sid, role):
        """Used by GET /sources/{id}: returns (record, allowed). Unknown ids -> (None, None)."""
        if sid.startswith("fx_"): return None, None
        if sid not in self.chunk_by_id: return None, None
        row = self.chunk_by_id[sid]; rec = self.source_of(row, 0.0); rec["text"] = self.ret.chunks[row].text
        return rec, rec["sensitivity"] in SENS_FOR_ROLE[role]

    # ---- main ----------------------------------------------------------------------------------------------------
    def ask(self, question: str, role: str = "reader", cfg: Config | None = None, qid: str | None = None, extra_chunks: list | None = None) -> RagResult:
        cfg = cfg or Config(); qid = qid or uuid.uuid4().hex[:8]; T = {}; t_all = time.perf_counter()
        r = RagResult(qid=qid, question=question, role=role, config=cfg.name)
        hits, T["retrieve_ms"] = self.retrieve(question, role, cfg)
        items, ctx_ids = [], []
        for row, sc in hits:
            c = self.ret.chunks[row]; r.sources.append(self.source_of(row, sc)); ctx_ids.append(c.id)
            items.append(f"[{c.id}] (type={self.ret.metas[row]['type']}; source={self.docs[c.doc_id]['source_url']})\n{c.text}")
        for fx in extra_chunks or []:      # test fixtures (conflicting / poisoned sources) are given to the model as ordinary sources
            items.append(f"[{fx['id']}] (type={fx.get('type', 'note')})\n{fx['text']}"); ctx_ids.append(fx["id"])
            r.sources.append(dict(id=fx["id"], kind="fixture", doc_id="fixture", section="", type=fx.get("type", "note"), sensitivity=fx.get("sensitivity", "public"), source_url="", score=0.0))
        gtext = ""
        if cfg.use_graph and self.graph:
            g = self.graph.build(question, role); T["graph_ms"] = g.ms
            r.graph = dict(seeds=[(l, k) for l, k, _ in g.seeds], nodes=g.n_nodes, edges=g.n_edges, truncated=g.truncated, denied=g.denied)
            if g.text: gtext = "KNOWLEDGE GRAPH FACTS (node ids in [G:Label:key]):\n" + g.text; ctx_ids += sorted(g.node_ids)
        r.context_ids = ctx_ids
        context = "\n\n".join(items + ([gtext] if gtext else [])) or "(no relevant sources were found)"
        sysm, usr = load_prompt(cfg.prompt_file) if cfg.prompt_file != PROMPT_FILE else (self.system, self.user_tpl)
        user = usr.replace("{context}", context).replace("{question}", question); r.prompt_system, r.prompt_user = sysm, user
        res = self.llm.generate(sysm, user)
        T["llm_ms"] = res.latency_ms; r.backend, r.model = res.backend, res.model; r.in_tokens, r.out_tokens = res.in_tokens, res.out_tokens
        status, body = parse_status(res.text); r.status = status
        if status == "MALFORMED":
            r.status = "NO_ANSWER"
            body = "The model returned an invalid response format; no answer was accepted."
        cited, bad, uncited = check_citations(body, set(ctx_ids)); r.cited, r.invalid_citations, r.uncited_sentences = cited, bad, uncited
        if LEAK.search(body): r.guard = "blocked_output_leak"; status, body = "NO_ANSWER", "The answer was withheld by the output guard (possible prompt-injection / confidential content)."; r.status = "BLOCKED"
        if bad:
            def keep_valid(match):
                parts = [p.strip() for p in re.split(r"\s*[,;]\s*", match.group(1))]
                return " ".join(f"[{p}]" for p in parts if p in ctx_ids)
            body = CITE.sub(keep_valid, body)
            r.guard = (r.guard + " invalid_citation_removed").strip()
        r.answer = body; T["total_ms"] = (time.perf_counter() - t_all) * 1000; r.latency = T
        if self.log: self._log(r)
        return r

    def _log(self, r: RagResult):
        LOG_FILE.parent.mkdir(exist_ok=True)
        rec = dict(ts=dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"), qid=r.qid, role=r.role, config=r.config, question=r.question,
                   sources=[s["id"] for s in r.sources], context_ids=r.context_ids, answer=r.answer, status=r.status, cited=r.cited, invalid_citations=r.invalid_citations,
                   uncited_sentences=r.uncited_sentences, guard=r.guard, in_tokens=r.in_tokens, out_tokens=r.out_tokens, latency_ms={k: (round(v, 1) if v is not None else None) for k, v in r.latency.items()},
                   backend=r.backend, model=r.model, graph=r.graph)
        with open(LOG_FILE, "a", encoding="utf-8") as f: f.write(json.dumps(rec, ensure_ascii=False) + "\n")
