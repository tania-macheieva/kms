import os, sys, pytest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fastapi.testclient import TestClient
from api.main import create_app, TokenBucket, KeyStore
from src.rag import RAG
from src.graph_context import GraphContextBuilder
from src.llm import ExtractiveLLM

KEYS = "test-reader-key:reader,test-clin-key:clinician"
RD, CL = {"X-API-Key": "test-reader-key"}, {"X-API-Key": "test-clin-key"}

@pytest.fixture(scope="module")
def rag(): return RAG(ExtractiveLLM(), graph=GraphContextBuilder(), log=False)
@pytest.fixture()
def client(rag):
    with TestClient(create_app(rag=rag, keys=KEYS, rate="100/60")) as c: yield c

def test_health_no_auth(client):
    r = client.get("/health"); assert r.status_code == 200 and r.json()["status"] == "ok" and r.json()["chunks"] > 100

def test_auth_required(client):
    assert client.post("/ask", json={"question": "what is bcftools?"}).status_code == 401
    assert client.post("/ask", json={"question": "what is bcftools?"}, headers={"X-API-Key": "wrong"}).status_code == 401

def test_fail_closed_without_keys(rag):
    with TestClient(create_app(rag=rag, keys="", rate="10/60")) as c: assert c.post("/ask", json={"question": "abc def"}, headers=RD).status_code == 401

@pytest.mark.parametrize("body", [{}, {"question": ""}, {"question": "ab"}, {"question": "x" * 501}, {"question": "valid question", "k": 0}, {"question": "valid question", "k": 99}, {"question": "   "}])
def test_validation_422(client, body): assert client.post("/ask", json=body, headers=RD).status_code == 422

def test_ask_answer_with_valid_citations(client):
    r = client.post("/ask", json={"question": "What does the merge-logic option of bcftools annotate do?"}, headers=RD); j = r.json()
    assert r.status_code == 200 and j["status"] == "ANSWER" and j["citations"] and set(j["citations"]) <= {s["id"] for s in j["sources"]} | {c for c in j["citations"] if c.startswith("G:")}
    assert j["role"] == "reader" and j["usage"]["input_tokens"] > 0

def test_role_filter_restricted_not_leaked(rag, client):
    q = "What diagnosis does Iryna have?"
    rd = client.post("/ask", json={"question": q}, headers=RD).json()
    assert "Iryna_OC" not in rd["answer"] and "ovarian" not in rd["answer"].lower() and not any(c.startswith("G:Diagnosis") for c in rd["citations"])
    from src.rag import Config                      # pipeline level: the restricted node is in the clinician's context only
    ids = {role: rag.ask(q, role, Config(name="t")).context_ids for role in ("reader", "analyst", "clinician")}
    assert any(i.startswith("G:Diagnosis") for i in ids["clinician"]) and not any(i.startswith("G:Diagnosis") for i in ids["reader"] + ids["analyst"])

def test_sources_ok_404_403(client):
    assert client.get("/sources/bcftools_manual%23h019", headers=RD).status_code == 200
    assert client.get("/sources/nonexistent_doc%23h999", headers=RD).status_code == 404
    assert client.get("/sources/bad%20id!", headers=RD).status_code == 422
    assert client.get("/sources/bcftools_manual%23h019").status_code == 401

def test_sources_sensitivity(rag, client):
    sens = {c.id: m["sensitivity"] for c, m in zip(rag.ret.chunks, rag.ret.metas)}
    hidden = [i for i, s in sens.items() if s != "public"]
    if hidden:
        i = hidden[0].replace("#", "%23"); assert client.get(f"/sources/{i}", headers=RD).status_code == 403; assert client.get(f"/sources/{i}", headers=CL).status_code == 200

def test_rate_limit_429(rag):
    with TestClient(create_app(rag=rag, keys=KEYS, rate="3/60")) as c:
        codes = [c.get("/sources/bcftools_manual%23h019", headers=RD).status_code for _ in range(5)]
        assert codes[:3] == [200] * 3 and codes[3:] == [429, 429]
        r = c.get("/sources/bcftools_manual%23h019", headers=RD); assert r.headers["Retry-After"].isdigit()
        assert c.get("/sources/bcftools_manual%23h019", headers=CL).status_code == 200   # other key has its own bucket

def test_token_bucket_refill():
    t = [0.0]; b = TokenBucket(2, 10, clock=lambda: t[0]); assert b.take("a") == 0 and b.take("a") == 0 and b.take("a") > 0; t[0] = 6; assert b.take("a") == 0

def test_keystore_hashes():
    ks = KeyStore("k1:reader,k2:bogusrole,k3:clinician"); assert ks.lookup("k1") == "reader" and ks.lookup("k3") == "clinician" and ks.lookup("k2") is None and ks.lookup("zzz") is None
    assert all(len(d) == 32 for d in ks.by_digest)

def test_role_cannot_be_chosen_by_client(client):
    r = client.post("/ask", json={"question": "valid question here", "role": "clinician"}, headers=RD); assert r.status_code == 200 and r.json()["role"] == "reader"
