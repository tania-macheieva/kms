"""Локальне дзеркало «мітки Wikidata» за протоколом SPARQL (GET ?query=, JSON-результат).
НЕ є Wikidata: обслуговує лише data/wikidata_mirror.ttl (пари Q-id -> мітка зі списку пошуку 2026-10-27).
Потрібне, бо з робочого середовища query.wikidata.org недоступний. Студент може підставити реальний ендпоїнт (див. README)."""
import json
import threading
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import pyoxigraph as ox

ROOT = Path(__file__).resolve().parents[1]


def make_server(port=8765):
    st = ox.Store()
    st.load(path=str(ROOT / "data/wikidata_mirror.ttl"), format=ox.RdfFormat.TURTLE)

    class H(BaseHTTPRequestHandler):
        def log_message(self, *a): pass

        def do_GET(self):
            q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query).get("query", [""])[0]
            return self._run(q)

        def do_POST(self):
            body = self.rfile.read(int(self.headers.get("Content-Length", 0))).decode()
            q = urllib.parse.parse_qs(body).get("query", [body])[0] if "query=" in body else body
            return self._run(q)

        def _run(self, q):
            try:
                res = st.query(q)
                buf = res.serialize(format=ox.QueryResultsFormat.JSON)
                self.send_response(200); self.send_header("Content-Type", "application/sparql-results+json"); self.send_header("Content-Length", str(len(buf))); self.end_headers(); self.wfile.write(buf)
            except Exception as e:
                msg = str(e).encode(); self.send_response(400); self.send_header("Content-Length", str(len(msg))); self.end_headers(); self.wfile.write(msg)

    return HTTPServer(("127.0.0.1", port), H)


def start(port=8765):
    srv = make_server(port)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv
