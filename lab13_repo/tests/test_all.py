import json, sys, pathlib, csv
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
import pytest
from common import norm, load_passages, REL_TYPES, ENT_TYPES
import extract_llm as xl
from evaluate import evaluate, prf
from llm_client import LLM, CacheMiss
import jsonschema

def gold(): return [json.loads(l) for l in open(ROOT / "data/gold.jsonl", encoding="utf-8")]

def test_norm():
    assert norm("`nf-core/sarek`") == "sarek" and norm("--vep_condel") == "--vep_condel" and norm("QD.") == "qd"

def test_gold_size_and_docs():
    g = gold(); assert len(g) >= 150 and len({x["doc_id"] for x in g}) >= 20

def test_gold_offsets_match_text():
    P = {p["id"]: p["text"] for p in load_passages()}
    for x in gold():
        t = P[x["passage_id"]]
        span = x["text"] if x["kind"] == "entity" else x["evidence"]
        assert x["start"] >= 0 and t[x["start"]:x["end"]].lower() == span.lower()

def test_gold_split_by_document():
    g = gold(); dev = {x["doc_id"] for x in g if x["split"] == "dev"}; test = {x["doc_id"] for x in g if x["split"] == "test"}
    assert dev and test and not dev & test

def test_gold_type_constraints():
    for x in gold():
        if x["kind"] == "relation": assert x["relation"] in REL_TYPES
        else: assert x["type"] in ENT_TYPES

def test_validate_rejects_bad_vocab_and_evidence():
    txt = "bcftools view reads a VCF file."
    ok = {"entities": [{"text": "VCF", "type": "FileFormat"}], "relations": [{"subject": "bcftools view", "relation": "ACCEPTS", "object": "VCF", "evidence": "reads a VCF file"}]}
    assert xl.validate(ok, txt) == []
    bad = json.loads(json.dumps(ok)); bad["entities"][0]["type"] = "Database"; bad["relations"][0]["evidence"] = "made up quote"
    errs = xl.validate(bad, txt); assert len(errs) == 2

class Fake(LLM):
    def __init__(self, outs): self.outs, self.calls = list(outs), []; self.model = "fake"
    def complete(self, system, user, meta=None): self.calls.append(user); return self.outs.pop(0)

def test_retry_then_success():
    p = {"id": "PX", "text": "bcftools view reads a VCF file."}
    bad = '{"entities": [], "relations": [{"subject": "a", "relation": "ACCEPTS", "object": "VCF", "evidence": "invented"}]}'
    good = '{"entities": [{"text": "VCF", "type": "FileFormat"}], "relations": []}'
    llm = Fake([bad, good]); obj, att, first, log = xl.run_passage(llm, "sys", p)
    assert att == 2 and obj["entities"][0]["text"] == "VCF" and "rejected by the validator" in llm.calls[1] and first[1]

def test_retries_exhausted_drops_fabricated():
    p = {"id": "PX", "text": "bcftools view reads a VCF file."}
    bad = '{"entities": [], "relations": [{"subject": "a", "relation": "ACCEPTS", "object": "VCF", "evidence": "invented"}]}'
    llm = Fake([bad] * 3); obj, att, first, log = xl.run_passage(llm, "sys", p)
    assert att == xl.MAX_RETRIES + 1 == 3 and obj["relations"] == []

def test_cache_miss_records_pending(tmp_path):
    llm = LLM("claude-haiku-4-5"); llm.cache = {}
    import os; os.environ.pop("ANTHROPIC_API_KEY", None)
    with pytest.raises(CacheMiss): llm.complete("s", "u")
    assert len(llm.pending) == 1

def test_cached_outputs_valid_against_json_schema():
    schema = json.load(open(ROOT / "schema/extraction_output.schema.json"))
    n = 0
    for l in open(ROOT / "llm_cache/cache.jsonl", encoding="utf-8"):
        out = xl.parse(json.loads(l)["output"])
        if out is not None and "PASSAGE" not in l[:0]:
            try: jsonschema.validate(out, schema); n += 1
            except jsonschema.ValidationError: pass
    assert n >= 100   # most replies are schema-valid (validator also checks evidence)

def test_evaluate_perfect_and_empty():
    g = gold(); pred = [dict(x, method="x") for x in g if x["split"] == "test"]
    r = evaluate(g, pred, "test"); assert r["entity"]["overall"]["F1"] == 1.0 and r["relation"]["overall"]["F1"] == 1.0
    assert evaluate(g, [], "test")["entity"]["overall"]["F1"] == 0.0
    assert prf(1, 1, 1)["F1"] == 0.5

def test_rules_extract_finds_option_and_format():
    from extract_rules import extract
    p = {"id": "PX", "doc_id": "sarek_usage", "start": 0, "text": "The tool reads a VCF file. Use `--outdir` and --input to set paths."}
    ents, rels = extract(p)
    assert ("--outdir", "Option") in {(e[2], e[3]) for e in ents} and ("VCF", "FileFormat") in {(e[2], e[3]) for e in ents}
    assert any(r["relation"] == "HAS_OPTION" for r in rels)

def test_graph_has_provenance_properties():
    c = (ROOT / "data/graph_load.cypher").read_text(encoding="utf-8")
    for prop in ("source:", "start:", "end:", "model:", "confidence:", "prompt_version:", "evidence:"): assert prop in c
    t = (ROOT / "data/graph_load.ttl").read_text(encoding="utf-8")
    assert "ex:confidence" in t and "ex:model" in t and "ex:startOffset" in t

def test_linked_entities_at_least_20():
    rows = list(csv.DictReader(open(ROOT / "data/entities_linked.csv", encoding="utf-8")))
    assert sum(bool(r["onto_class"]) for r in rows) >= 20

def test_patterns_have_three_accepted_rules():
    rows = list(csv.DictReader(open(ROOT / "eval/patterns_rules.csv", encoding="utf-8")))
    assert sum(r["decision"] == "accept" for r in rows) >= 3 and all(float(r["lift"]) > 1 for r in rows)
