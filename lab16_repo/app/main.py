"""FastAPI demonstrator. uvicorn app.main:app --port 8000"""
from __future__ import annotations
import pathlib
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from .core import Hub
HUB = {}
@asynccontextmanager
async def lifespan(_):
    hub(); yield
app = FastAPI(title="Domain Knowledge Hub — recommender demonstrator", version="1.0", lifespan=lifespan)
def hub():
    if "h" not in HUB: HUB["h"] = Hub()
    return HUB["h"]
class Ask(BaseModel): q: str; role: str = "reader"
class NewUser(BaseModel): role: str = "reader"; topics: list[str] = []; history: list[str] = []; k: int = 5
class NewDoc(BaseModel): id: str; section: str; text: str; sensitivity: str = "public"
@app.get("/health")
def health(): h = hub(); return dict(status="ok", items=len(h.items), users=len(h.hist), graph=h.G.stats())
@app.get("/api/search")
def search(q: str, role: str = "reader", k: int = 5): return hub().search(q, role, k)
@app.post("/api/ask")
def ask(a: Ask): return hub().ask(a.q, a.role)
@app.get("/api/users")
def users(): h = hub(); return [dict(user=u, role=h.role[u], events=len(h.hist[u])) for u in sorted(h.hist)]
@app.get("/api/recommend/{user}")
def reco(user: str, k: int = 5, role: str | None = None, max_age_days: int | None = None):
    try: return hub().recommend_user(user, k, role, max_age_days)
    except KeyError: raise HTTPException(404, "unknown user")
@app.post("/api/recommend/new-user")
def new_user(n: NewUser): return hub().recommend_new_user(n.role, n.topics, n.history, n.k)
@app.post("/api/items")
def new_item(d: NewDoc): return hub().add_document(d.id, d.section, d.text, d.sensitivity)
@app.get("/", response_class=HTMLResponse)
def index(): return (pathlib.Path(__file__).parent / "static/index.html").read_text(encoding="utf-8")
