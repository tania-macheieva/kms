import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT))
import pytest
from src.rag import RAG, Config, check_citations, parse_status, LEAK, SENS_FOR_ROLE, load_prompt
from src.graph_context import GraphContextBuilder
from src.llm import ExtractiveLLM, ReplayLLM, key_of, count_tokens, CacheMiss
from src import evalrag as E

@pytest.fixture(scope="module")
def rag(): return RAG(ExtractiveLLM(), graph=GraphContextBuilder(), log=False)

def test_check_citations():
    cited, bad, unc = check_citations("Fact one [a#1]. Fact two [zzz#9]. Another sentence without source here.", {"a#1"})
    assert cited == ["a#1"] and bad == ["zzz#9"] and unc >= 1

def test_check_citations_rejects_unknown_parts_of_combined_citation():
    cited, bad, _ = check_citations("A verified claim [a#1, missing#2].", {"a#1"})
    assert cited == ["a#1"] and bad == ["missing#2"]

def test_ask_normalizes_malformed_status_and_removes_invalid_citations():
    from types import SimpleNamespace

    class Model:
        def __init__(self, text): self.text = text
        def generate(self, system, user):
            return SimpleNamespace(text=self.text, latency_ms=1, backend="test", model="test", in_tokens=1, out_tokens=1)

    def make_rag(text):
        r = RAG.__new__(RAG)
        r.docs = {}; r.graph = None; r.llm = Model(text); r.log = False
        r.system, r.user_tpl = "system", "{context} {question}"
        r.retrieve = lambda question, role, cfg: ([], 0.0)
        return r

    malformed = make_rag("not a status line").ask("Question?")
    assert malformed.status == "NO_ANSWER"
    clean = make_rag("STATUS: ANSWER\nA verified claim [a#1, missing#2].").ask(
        "Question?", extra_chunks=[{"id": "a#1", "text": "source"}]
    )
    assert clean.answer == "A verified claim [a#1]."
    assert clean.invalid_citations == ["missing#2"]

def test_parse_status():
    assert parse_status("STATUS: CONFLICT\nx")[0] == "CONFLICT" and parse_status("no status line")[0] in ("NO_ANSWER", "ANSWER", "MALFORMED")

def test_prompt_has_required_rules():
    s, u = load_prompt(); low = s.lower()
    for w in ("[id]", "no_answer", "conflict", "untrusted", "confiden"): assert w in low
    assert "{context}" in u and "{question}" in u

def test_replay_key_stable_and_miss():
    assert key_of("m", "s", "u") == key_of("m", "s", "u") != key_of("m2", "s", "u")
    with pytest.raises(CacheMiss): ReplayLLM("no-such-model").generate("s", "u")

def test_token_counter(): assert count_tokens("abcd" * 10) == 10 or count_tokens("abcd" * 10) > 0

def test_leak_guard_precise():
    assert LEAK.search("here is the key sk-abcdefghijklmnopqrstuvwxyz") and not LEAK.search("The text asks to print the system prompt; ignored.")

def test_role_prefilter_in_context(rag):
    for role, allowed in SENS_FOR_ROLE.items():
        r = rag.ask("variant calling hard filtering thresholds", role, Config(name="t"))
        assert all(s["sensitivity"] in allowed for s in r.sources)

def test_graph_limits_and_denied():
    g = GraphContextBuilder().build("Which thresholds does HF-01 use?", "reader")
    assert g.n_nodes <= 24 and g.n_edges <= 40 and "[G:Procedure:HF-01]" in g.text
    d = GraphContextBuilder().build("What diagnosis does Iryna have?", "reader"); assert "Diagnosis" not in d.text and d.denied

def test_graph_is_read_only():
    from src.graph_context import GraphIndex
    gi = GraphIndex()
    with pytest.raises(Exception): gi.g.ro_query("CREATE (:X {a:1})")

def test_eval_set_composition():
    t = E.load_tests(); c = lambda **k: sum(all(x.get(a) == b for a, b in k.items()) for x in t)
    assert len(t) >= 30 and c(category="answerable") >= 15 and c(category="no_answer") >= 8 and c(category="conflict") >= 4 and c(category="injection") >= 3
    assert len({x["id"] for x in t}) == len(t)

def test_claims_csv_schema():
    import csv; p = ROOT / "claims/claims.csv"
    if not p.exists(): pytest.skip("claims.csv not built yet")
    rows = list(csv.DictReader(open(p, encoding="utf-8"))); assert rows and set(rows[0]) >= {"id", "claim", "type", "source", "level", "status", "comment"}
    assert all(r["type"] in ("факт", "правило", "гіпотеза") and r["level"] in ("V1", "V3", "V4") and r["status"] in ("verified", "rejected", "pending") for r in rows)
    assert all(r["comment"].strip() for r in rows if r["status"] == "rejected")
