import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT))
C = [json.loads(l) for l in open(ROOT / "data/corpus.jsonl", encoding="utf-8")]
G = [json.loads(l) for l in open(ROOT / "eval/gold.jsonl", encoding="utf-8")]
DOCS = {p.stem: p.read_text(encoding="utf-8") for p in (ROOT / "data/docs_clean").glob("*.md")}


def test_corpus_size_and_metadata():
    assert len({c["doc_id"] for c in C}) >= 20 and len(C) >= 200
    for c in C:
        for k in ("doc_id", "title", "section", "type", "date", "sensitivity", "source_url"): assert k in c
        assert c["sensitivity"] in ("public", "internal", "restricted") and c["text"].strip()


def test_chunk_offsets_point_into_clean_docs():
    for c in C[::7]: assert DOCS[c["doc_id"]][c["start"]:c["end"]].strip() and c["text"].split("\n", 1)[-1].strip()[:30] in DOCS[c["doc_id"]]


def test_restricted_documents_are_the_ones_with_pedigree_names():
    import re
    pat = re.compile(r"\b(Olena|Iryna|Petro|Marta|Sofiia|Halyna|Andrii)\b")
    for c in C:
        raw = (ROOT / "data/raw" / f"{c['doc_id']}.md")
        if raw.exists() and c["lang"] == "uk": assert (c["sensitivity"] == "restricted") == bool(pat.search(raw.read_text(encoding="utf-8")))
        if c["lang"] == "en": assert c["sensitivity"] == "public"


def test_gold_shape_and_verbatim_evidence():
    assert len(G) >= 40 and sum(not g["answerable"] for g in G) >= 5
    for g in G:
        assert bool(g["evidence"]) == g["answerable"]
        for e in g["evidence"]:
            for s in [e] + e.get("also", []): assert DOCS[s["doc_id"]][s["start"]:s["end"]] == s["quote"]
