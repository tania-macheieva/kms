"""Chunking strategies over cleaned markdown documents.

Every chunk carries character offsets (start, end) into the cleaned document text, so relevance can be
judged by span overlap with gold evidence independently of the strategy (see src/metrics.py).
`text` is what is embedded / indexed; `context` is what would be handed to a reader (LLM) and is what the
"average context size" metric counts (differs from `text` only for the hierarchical strategy).
"""
from __future__ import annotations
import re
from dataclasses import dataclass, field

HEAD = re.compile(r"^(#{1,6})\s+(.*\S)\s*$", re.M)
WORD = re.compile(r"\S+")


@dataclass
class Chunk:
    id: str
    doc_id: str
    start: int
    end: int
    text: str
    section: str = ""
    context: str = ""
    context_span: tuple = field(default=None)  # (start, end) of the context in the document

    def __post_init__(self):
        if not self.context: self.context = self.text
        if self.context_span is None: self.context_span = (self.start, self.end)


def nwords(s: str) -> int:
    return len(WORD.findall(s))


def sections(text: str):
    """Yield (path, start, end) for each heading-delimited section; the heading line belongs to its section."""
    heads = [(m.start(), len(m.group(1)), m.group(2)) for m in HEAD.finditer(text)]
    if not heads: return [("", 0, len(text))]
    out, stack = [], []
    if heads[0][0] > 0: out.append(("", 0, heads[0][0]))
    for i, (pos, lvl, title) in enumerate(heads):
        while stack and stack[-1][0] >= lvl: stack.pop()
        stack.append((lvl, title))
        end = heads[i + 1][0] if i + 1 < len(heads) else len(text)
        out.append((" > ".join(t for _, t in stack), pos, end))
    return out


def _paras(text, start, end):
    """Paragraph spans (split on blank lines) inside [start, end)."""
    spans, pos = [], start
    for m in re.finditer(r"\n\s*\n", text[start:end]):
        s, e = pos, start + m.start()
        if text[s:e].strip(): spans.append((s, e))
        pos = start + m.end()
    if text[pos:end].strip(): spans.append((pos, end))
    return spans


def _units(text, start, end, limit):
    """Paragraph spans; a paragraph longer than `limit` words (tables, code) is split further on line breaks."""
    out = []
    for ps, pe in _paras(text, start, end):
        if nwords(text[ps:pe]) <= limit: out.append((ps, pe)); continue
        pos = ps
        for m in re.finditer(r"\n", text[ps:pe]):
            if nwords(text[pos:ps + m.start()]) >= limit // 2: out.append((pos, ps + m.start())); pos = ps + m.end()
        if text[pos:pe].strip(): out.append((pos, pe))
    return out


def fixed(doc, size=200, overlap=40):
    """Fixed-size word windows with overlap; blind to structure."""
    if size <= 0 or overlap < 0 or overlap >= size:
        raise ValueError("size must be positive and overlap must be in [0, size)")
    t = doc["text"]; ws = list(WORD.finditer(t)); step = size - overlap; out = []
    if not ws: return out
    for i in range(0, max(len(ws) - overlap, 1), step):
        a, b = ws[i].start(), ws[min(i + size, len(ws)) - 1].end()
        out.append(Chunk(f"{doc['doc_id']}#f{len(out):03d}", doc["doc_id"], a, b, t[a:b]))
        if i + size >= len(ws): break
    return out


def heading(doc, max_words=250, min_words=40):
    """Structure-aware: one chunk per heading section; tiny sections merge forward, long ones split on paragraphs.
    The title/section path is prepended to the embedded text."""
    t = doc["text"]; out, pend = [], None

    def emit(path, a, b):
        body = t[a:b].strip()
        if not body: return
        head = f"{doc['title']} — {path}\n" if path else f"{doc['title']}\n"
        out.append(Chunk(f"{doc['doc_id']}#h{len(out):03d}", doc["doc_id"], a, b, head + body, path))

    for path, a, b in sections(t):
        if pend: a, path = pend[1], pend[0] if nwords(t[pend[1]:a]) else path; pend = None
        w = nwords(t[a:b])
        if w < min_words: pend = (path, a); continue
        if w <= max_words: emit(path, a, b); continue
        cur_a, cur_w = None, 0
        for ps, pe in _units(t, a, b, max_words):
            pw = nwords(t[ps:pe])
            if cur_a is not None and cur_w + pw > max_words: emit(path, cur_a, last_e); cur_a, cur_w = None, 0
            if cur_a is None: cur_a = ps
            cur_w += pw; last_e = pe
        if cur_a is not None: emit(path, cur_a, last_e)
    if pend and nwords(t[pend[1]:]) > 0:
        if out and nwords(t[pend[1]:]) < min_words: out[-1].end = len(t); out[-1].text += "\n" + t[pend[1]:].strip()
        else: emit(pend[0], pend[1], len(t))
    return out


def hierarchical(doc, child_words=70, parent_words=500):
    """Small child chunks (paragraph groups) are indexed; the enclosing section (parent, capped) is returned as context."""
    t = doc["text"]; out = []
    for path, a, b in sections(t):
        # parent = the section, truncated to parent_words (cut at a paragraph boundary)
        pa, pb, w = a, a, 0
        for ps, pe in _units(t, a, b, child_words * 2):
            pw = nwords(t[ps:pe])
            if w and w + pw > parent_words: break
            pb, w = pe, w + pw
        paras = _units(t, a, b, child_words * 2)
        cur, cw = [], 0
        def emit():
            nonlocal cur, cw
            if not cur: return
            s, e = cur[0][0], cur[-1][1]
            head = f"{doc['title']} — {path}\n" if path else f"{doc['title']}\n"
            out.append(Chunk(f"{doc['doc_id']}#p{len(out):03d}", doc["doc_id"], s, e, head + t[s:e].strip(), path,
                             context=t[pa:pb].strip(), context_span=(pa, pb)))
            cur, cw = [], 0
        for ps, pe in paras:
            pw = nwords(t[ps:pe])
            if cur and cw + pw > child_words: emit()
            cur.append((ps, pe)); cw += pw
        emit()
    return out


def semantic(doc, emb, min_words=60, max_words=220, pct=20):
    """Semantic: sentence groups split where adjacent-window cosine similarity falls under the pct-th percentile."""
    import numpy as np
    t = doc["text"]; sents = []
    for ps, pe in _paras(t, 0, len(t)):
        for m in re.finditer(r"[^.!?\n]+(?:[.!?]+|\n|$)", t[ps:pe]):
            if m.group().strip(): sents.append((ps + m.start(), ps + m.end()))
    if len(sents) < 3: return fixed(doc)
    texts = [t[a:b].strip() for a, b in sents]
    win = [" ".join(texts[max(0, i - 1):i + 2]) for i in range(len(texts))]
    v = emb.encode(win)
    sim = (v[:-1] * v[1:]).sum(1); thr = np.percentile(sim, pct)
    out, a_i, w = [], 0, 0
    for i, (a, b) in enumerate(sents):
        w += nwords(t[a:b])
        cut = i == len(sents) - 1 or (w >= min_words and sim[i] <= thr) or w >= max_words
        if cut:
            s, e = sents[a_i][0], b
            out.append(Chunk(f"{doc['doc_id']}#s{len(out):03d}", doc["doc_id"], s, e, f"{doc['title']}\n" + t[s:e].strip()))
            a_i, w = i + 1, 0
    return out


STRATEGIES = {"fixed": fixed, "heading": heading, "hierarchical": hierarchical, "semantic": semantic}


def chunk_corpus(docs, strategy, emb=None, **kw):
    fn = STRATEGIES[strategy]
    return [c for d in docs for c in (fn(d, emb, **kw) if strategy == "semantic" else fn(d, **kw))]
