"""Підключення до графової БД. Рушій: FalkorDB (вбудований, falkordblite) — Neo4j-сервер у цьому середовищі встановити неможливо.
Для справжнього Neo4j 5 див. README (docker-compose.yml) та import/00_schema.neo4j.cypher."""
import os
import shutil
from pathlib import Path

from redislite.falkordb_client import FalkorDB

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "fdb" / "graph.db"
GRAPH = "dkh"
IMPORT_DIR = Path(os.environ.get("FALKORDB_IMPORT_DIR", "/var/lib/FalkorDB/import"))   # аналог каталогу import у Neo4j
_db = None


def db():
    global _db
    if _db is None:
        DB_PATH.parent.mkdir(exist_ok=True); _db = FalkorDB(str(DB_PATH))
    return _db


def graph(name=None): return db().select_graph(name or GRAPH)


def reset():
    try: graph().delete()
    except Exception: pass


def stage_csv():
    """Копіює data/*.csv у каталог імпорту сервера (LOAD CSV читає лише звідти)."""
    IMPORT_DIR.mkdir(parents=True, exist_ok=True)
    for f in (ROOT / "data").glob("*.csv"): shutil.copy(f, IMPORT_DIR / f.name)


def run(q, params=None):
    return graph().query(q, params=params)


def ro(q, params=None):
    """Read-only виклик (GRAPH.RO_QUERY): сервер відхиляє будь-який запис."""
    return graph().ro_query(q, params=params)
