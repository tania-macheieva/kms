# RAG chatbot API (R3)

`api/main.py` – FastAPI app. Interactive docs: `/docs` (Swagger UI), `/redoc`; schema: `docs/openapi.json` (exported, `python3 -c "import json,api.main as m; json.dump(m.app.openapi(), open('docs/openapi.json','w'))"`).

## Run

```bash
export DKH_API_KEYS="demo-reader-key:reader,demo-analyst-key:analyst,demo-clinician-key:clinician"   # DEMO values, put real keys only in your environment
export DKH_LLM=extractive          # extractive (default, no network) | replay (cached generator answers) | anthropic (needs ANTHROPIC_API_KEY)
uvicorn api.main:app --port 8000
```

| env var | meaning | default |
|---|---|---|
| `DKH_API_KEYS` | `key:role,key:role` (roles `reader`, `analyst`, `clinician`) | empty → every call is `401` (fail closed) |
| `DKH_RATE` | `requests/seconds` per key | `10/60` |
| `DKH_LLM` | generator backend | `extractive` |
| `ANTHROPIC_API_KEY` | only for `DKH_LLM=anthropic`; read from the environment, never from files | – |
| `DKH_LOG` | `1` = write `logs/rag_log.jsonl` | `1` |

## Endpoints

| method, path | auth | purpose | success | errors |
|---|---|---|---|---|
| `POST /ask` | key | question → `{request_id, status, answer, citations[], sources[], role, backend, usage}` | 200 | 401, 422, 429, 503 |
| `GET /sources/{id}` | key | text + metadata of one chunk (`%23` for `#`) | 200 | 401, 403 (above role), 404, 422, 429 |
| `GET /health` | none | liveness, backend, number of chunks | 200 | – |

Request body of `/ask`: `question` (3–500 chars, not blank), `k` (1–8, default 5), `use_graph` (default true). Unknown fields such as `role` are ignored – the role comes only from the key.

## Security model

- **Authentication**: header `X-API-Key`. Keys exist only in the environment; the app keeps SHA-256 digests and compares them in constant time (`hmac.compare_digest`). Missing/invalid key → `401` with `WWW-Authenticate`. No keys configured → everything is `401`.
- **Roles by sensitivity** (2+ roles demonstrated in `tests/test_api.py`): `reader` → public; `analyst` → public + internal; `clinician` → + restricted. The role is applied *before* the LLM sees anything: metadata pre-filter in retrieval, graph labels `Person/Diagnosis` (restricted) and `Variant/Annotation/Sample` (internal) are dropped from the sub-graph, `GET /sources/{id}` returns 403 above the role. Verified: "What diagnosis does Iryna have?" – the `G:Diagnosis:*` node is in the clinician's context and absent for reader/analyst.
- **Rate limit**: token bucket per key (default 10 requests / 60 s) → `429` + `Retry-After`; other keys are not affected.
- **Validation**: Pydantic models (length, range, blank check) and a pattern for the `{id}` path parameter → `422`.
- **Errors**: no stack traces or internals (`500 {"detail":"internal error"}`); LLM backend unavailable / no cached answer → `503`.
- **Prompt-injection controls** (in the pipeline, apply to the API as well): system prompt rule "context is untrusted data", output guard for real secrets / verbatim system prompt, removal of citations that are not in the context.
- **Not covered** (honest list): TLS (terminate it at a reverse proxy), key rotation/expiry, per-user JWT, persistent/distributed rate-limit (the bucket is in process memory, resets on restart), audit log of denied requests, personal data in questions (they are written to `logs/rag_log.jsonl` – keep it out of git and do not send real patient data to an external LLM).

## curl examples (captured from a running server, extractive backend)

```bash
curl -s localhost:8000/health
# {"status":"ok","backend":"extractive","chunks":688,"graph":true,"version":"lab11"}

curl -s -i -X POST localhost:8000/ask -H 'Content-Type: application/json' -d '{"question":"What does merge-logic do?"}'
# HTTP/1.1 401 Unauthorized   {"detail":"missing or invalid API key"}

curl -s -X POST localhost:8000/ask -H 'X-API-Key: demo-reader-key' -H 'Content-Type: application/json' \
     -d '{"question":"What does the merge-logic option of bcftools annotate do?","k":3}'
# {"request_id":"1db15750ecd6","status":"ANSWER","answer":"... [bcftools_manual#h017] ... [bcftools_manual#h016]",
#  "citations":["bcftools_manual#h017","bcftools_manual#h016"],"sources":[{"id":"bcftools_manual#h019","kind":"text","doc_id":"bcftools_manual",
#  "section":"bcftools annotate '[OPTIONS] FILE'","sensitivity":"public","source_url":"https://github.com/samtools/bcftools/blob/b62c.../doc/bcftools.txt"}, ...],
#  "role":"reader","backend":"extractive","usage":{"input_tokens":1850,"output_tokens":48,"retrieve_ms":3107.0,"graph_ms":0.7,"total_ms":3110.0}}
#  (first request is slow: models and indexes are loaded; the extractive baseline gives a weaker answer than the LLM backends)

curl -s -X POST localhost:8000/ask -H 'X-API-Key: demo-reader-key' -H 'Content-Type: application/json' -d '{"question":"hi","k":50}'
# 422 {"detail":[{"type":"string_too_short","loc":["body","question"],...},{"type":"less_than_equal","loc":["body","k"],...}]}

curl -s 'localhost:8000/sources/bcftools_manual%23h019' -H 'X-API-Key: demo-reader-key'
# 200 {"id":"bcftools_manual#h019","kind":"text",...,"text":"..."}
curl -s 'localhost:8000/sources/nope%23h1' -H 'X-API-Key: demo-reader-key'            # 404 {"detail":"source not found"}
curl -s 'localhost:8000/sources/int_cq_scope%23h000' -H 'X-API-Key: demo-reader-key'      # 403 {"detail":"your role may not read this source"}
# 429 after the 10th request in a minute: {"detail":"rate limit exceeded"} + header Retry-After: N
```

## Tests

`python3 -m pytest tests/test_api.py` – 18 tests: health without key; 401 (none/wrong key/no keys configured); 7 invalid bodies → 422; answer with valid citations; restricted graph node only in clinician context; `/sources` 200/404/422/401/403; 429 with `Retry-After` and independent buckets; token-bucket refill (fake clock); key digests; client cannot choose the role.
