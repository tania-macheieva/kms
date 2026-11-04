"""Domain Knowledge Hub – RAG chatbot API (FastAPI).

Endpoints: POST /ask, GET /health, GET /sources/{id}.
Auth: API key in header `X-API-Key`. Keys come ONLY from the environment (DKH_API_KEYS="key:role,key:role"), are stored as SHA-256 digests,
compared in constant time; the role (reader | analyst | clinician) is bound to the key, never taken from the request.
Roles -> max sensitivity of sources (public | internal | restricted) – enforced as a pre-filter in retrieval and in the graph sub-graph.
Rate limit: token bucket per key (DKH_RATE="requests/seconds", default 10/60) -> 429 + Retry-After.
LLM backend: DKH_LLM = extractive (default, no network) | replay | anthropic (needs ANTHROPIC_API_KEY in env).
Run: uvicorn api.main:app --port 8000
"""
import hashlib, hmac, os, sys, time, uuid
from contextlib import asynccontextmanager
from pathlib import Path
from threading import Lock
from typing import Annotated, Literal

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))
from fastapi import Depends, FastAPI, Header, HTTPException, Request, Path as PathParam
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator

from src.rag import RAG, Config
from src.graph_context import GraphContextBuilder
from src.llm import ExtractiveLLM, ReplayLLM, AnthropicLLM, CacheMiss

ROLES = ("reader", "analyst", "clinician")
DESCRIPTION = """
RAG chatbot over the Domain Knowledge Hub (biomedical data analysis): hybrid search (BM25 + dense, RRF) + optional re-ranking + knowledge-graph sub-graph.
Every answer starts from a **status** (`ANSWER`, `NO_ANSWER`, `CONFLICT`, `BLOCKED`) and cites sources as `[id]`; unknown ids are removed by an automatic check.

**Auth**: header `X-API-Key`. The key determines the role: `reader` (public), `analyst` (public+internal), `clinician` (public+internal+restricted).
**Limits**: per-key token bucket (default 10 requests / 60 s), `429` with `Retry-After`.
"""


def _digest(k: str) -> bytes: return hashlib.sha256(k.encode("utf-8")).digest()


class KeyStore:
    """key digest -> role. Raw keys are never stored or logged."""
    def __init__(self, spec: str):
        self.by_digest: dict[bytes, str] = {}
        for part in filter(None, (p.strip() for p in spec.split(","))):
            key, _, role = part.rpartition(":")
            if key and role in ROLES: self.by_digest[_digest(key)] = role
    def lookup(self, key: str) -> str | None:
        d = _digest(key); found = None
        for known, role in self.by_digest.items():           # constant-time compare against every digest
            if hmac.compare_digest(known, d): found = role
        return found


class TokenBucket:
    def __init__(self, capacity: int, per_seconds: float, clock=time.monotonic):
        self.cap, self.rate, self.clock = capacity, capacity / per_seconds, clock; self.state: dict[str, tuple[float, float]] = {}; self.lock = Lock()
    def take(self, who: str) -> float:
        """returns 0.0 if allowed, else seconds to wait"""
        with self.lock:
            now = self.clock(); tokens, last = self.state.get(who, (self.cap, now)); tokens = min(self.cap, tokens + (now - last) * self.rate)
            if tokens >= 1: self.state[who] = (tokens - 1, now); return 0.0
            self.state[who] = (tokens, now); return (1 - tokens) / self.rate


class AskRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=500, description="Question in natural language (3-500 characters)", examples=["What does the merge-logic option of bcftools annotate do?"])
    k: int = Field(5, ge=1, le=8, description="number of text chunks passed to the LLM")
    use_graph: bool = Field(True, description="add the knowledge-graph sub-graph to the prompt")
    @field_validator("question")
    @classmethod
    def not_blank(cls, v: str) -> str:
        if not v.strip(): raise ValueError("question must not be blank")
        if "\x00" in v: raise ValueError("control characters are not allowed")
        return v.strip()


class SourceRef(BaseModel):
    id: str; kind: str; doc_id: str; section: str = ""; sensitivity: str; source_url: str = ""
class Usage(BaseModel):
    input_tokens: int; output_tokens: int; retrieve_ms: float; graph_ms: float | None = None; total_ms: float
class AskResponse(BaseModel):
    request_id: str
    status: Literal["ANSWER", "NO_ANSWER", "CONFLICT", "BLOCKED"]
    answer: str
    citations: list[str] = Field(description="ids cited in the answer (all validated against the context)")
    sources: list[SourceRef] = Field(description="sources that were in the context (after the role filter)")
    role: str; backend: str; usage: Usage
class SourceResponse(SourceRef):
    text: str
class Health(BaseModel):
    status: Literal["ok"]; backend: str; chunks: int; graph: bool; version: str = "lab11"
class Error(BaseModel):
    detail: str


def make_llm():
    kind = os.environ.get("DKH_LLM", "extractive")
    if kind == "replay": return ReplayLLM(os.environ.get("DKH_MODEL", "claude-haiku-4-5-20251001"))
    if kind == "anthropic": return AnthropicLLM()        # key from env ANTHROPIC_API_KEY only
    return ExtractiveLLM()


def create_app(rag: RAG | None = None, keys: str | None = None, rate: str | None = None) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.rag = rag or RAG(make_llm(), graph=GraphContextBuilder(), log=os.environ.get("DKH_LOG", "1") == "1"); yield
    app = FastAPI(title="Domain Knowledge Hub RAG API", version="lab11", description=DESCRIPTION, lifespan=lifespan,
                  openapi_tags=[{"name": "chat", "description": "question answering"}, {"name": "sources", "description": "source lookup"}, {"name": "ops", "description": "service state"}])
    app.state.keys = KeyStore(keys if keys is not None else os.environ.get("DKH_API_KEYS", ""))      # empty store => every call is 401 (fail closed)
    n, _, per = (rate or os.environ.get("DKH_RATE", "10/60")).partition("/"); app.state.bucket = TokenBucket(int(n), float(per or 60))

    def auth(request: Request, x_api_key: Annotated[str | None, Header(description="API key; determines the role")] = None) -> dict:
        role = request.app.state.keys.lookup(x_api_key) if x_api_key else None
        if role is None: raise HTTPException(401, "missing or invalid API key", headers={"WWW-Authenticate": "ApiKey"})
        who = _digest(x_api_key).hex()[:12]; wait = request.app.state.bucket.take(who)
        if wait > 0: raise HTTPException(429, "rate limit exceeded", headers={"Retry-After": str(int(wait) + 1)})
        return dict(role=role, key_id=who)

    @app.exception_handler(Exception)
    async def unhandled(request: Request, exc: Exception): return JSONResponse({"detail": "internal error"}, status_code=500)   # no stack traces / internals to the client

    common = {401: {"model": Error, "description": "missing/invalid API key"}, 429: {"model": Error, "description": "rate limit exceeded (see Retry-After)"}}

    @app.post("/ask", response_model=AskResponse, tags=["chat"], summary="Ask a question", responses={**common, 503: {"model": Error, "description": "LLM backend unavailable"}})
    def ask(body: AskRequest, request: Request, who: Annotated[dict, Depends(auth)]):
        rid = uuid.uuid4().hex[:12]
        try: r = request.app.state.rag.ask(body.question, who["role"], Config(k=body.k, use_graph=body.use_graph, name="api"), qid=rid)
        except CacheMiss: raise HTTPException(503, "LLM backend has no answer for this prompt (replay mode)")
        except (ConnectionError, TimeoutError, OSError) as e: raise HTTPException(503, "LLM backend unavailable")
        return AskResponse(request_id=rid, status=r.status, answer=r.answer, citations=r.cited, sources=[SourceRef(**{k: s[k] for k in SourceRef.model_fields if k in s}) for s in r.sources],
                           role=who["role"], backend=r.backend, usage=Usage(input_tokens=r.in_tokens, output_tokens=r.out_tokens, retrieve_ms=round(r.latency["retrieve_ms"], 1), graph_ms=(round(r.latency["graph_ms"], 1) if r.latency.get("graph_ms") is not None else None), total_ms=round(r.latency["total_ms"], 1)))

    @app.get("/sources/{source_id:path}", response_model=SourceResponse, tags=["sources"], summary="Get a source chunk by id", responses={**common, 403: {"model": Error, "description": "source above the role's sensitivity"}, 404: {"model": Error, "description": "unknown id"}})
    def source(source_id: Annotated[str, PathParam(min_length=3, max_length=120, pattern=r"^[A-Za-z0-9_.#:\-]+$", description="chunk id, e.g. `bcftools_manual#h019` (use %23 for `#`)")], request: Request, who: Annotated[dict, Depends(auth)]):
        rec, allowed = request.app.state.rag.get_source(source_id, who["role"])
        if rec is None: raise HTTPException(404, "source not found")
        if not allowed: raise HTTPException(403, "your role may not read this source")
        return SourceResponse(**{k: rec[k] for k in SourceResponse.model_fields if k in rec})

    @app.get("/health", response_model=Health, tags=["ops"], summary="Liveness (no auth)")
    def health(request: Request):
        r = request.app.state.rag; return Health(status="ok", backend=r.llm.backend, chunks=len(r.ret.chunks), graph=r.graph is not None)
    return app


app = create_app()
