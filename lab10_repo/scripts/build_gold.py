"""LLM-generated candidate queries (llm_log/raw/*) + human-review corrections -> eval/gold.jsonl with char-span evidence."""
import json, re
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
docs = {p.stem: p.read_text(encoding="utf-8") for p in (ROOT / "data/docs_clean").glob("*.md")}
corp = {c["chunk_id"]: c for c in map(json.loads, open(ROOT / "data/corpus.jsonl", encoding="utf-8"))}
S = json.load(open(ROOT / "llm_log/raw/gold_single_out.json")); P = json.load(open(ROOT / "llm_log/raw/gold_pairs_out.json"))
DROP = {"sarek_readme#h006"}  # reviewer decision: list of names, not a retrievable fact
# NA queries replaced by the reviewer: the LLM's candidates were partially answerable (VQSR tranches, Strelka2, GLnexus appear in the docs)
NA = ["How should polygenic risk scores be calculated from a VCF file?", "Which spot instance type is cheapest for running Nextflow pipelines in the cloud?",
      "How do I call variants from Oxford Nanopore long-read data?", "What are the HIPAA requirements for storing patient VCF files?",
      "How is pharmacogenomic drug response predicted from variant calls?", "How do I run a genome-wide association study (GWAS) on the called variants?"]


def span(chunk_id, quote):
    c = corp[chunk_id]; d = docs[c["doc_id"]]; i = d.find(quote, c["start"] - 5)
    if i < 0: i = d.find(quote)
    assert i >= 0, (chunk_id, quote[:60])
    return dict(doc_id=c["doc_id"], start=i, end=i + len(quote), quote=quote)


def main():
    out = []
    for x in S:
        if x["chunk_id"] in DROP: continue
        out.append(dict(type=x["kind"], lang="uk" if x["kind"].startswith("uk") else "en", query=x["query"], answerable=True, evidence=[span(x["chunk_id"], x["evidence"])], source_chunks=[x["chunk_id"]]))
    for x in P["pairs"]:
        out.append(dict(type="multi_step", lang="en", query=x["query"], answerable=True, evidence=[span(x["chunk_a"] if isinstance(x["chunk_a"], str) else x["chunk_a"]["chunk_id"] if isinstance(x["chunk_a"], dict) else x["chunk_a"], x["evidence_a"]),
                       span(x["chunk_b"] if isinstance(x["chunk_b"], str) else x["chunk_b"]["chunk_id"], x["evidence_b"])], source_chunks=x["pair_id"].split("+")))
    for i, o in enumerate(out): o["_tmp"] = f"Q{i + 1:02d}"
    for q in NA: out.append(dict(type="no_answer", lang="en", query=q, answerable=False, evidence=[], source_chunks=[], _tmp=""))
    # adjudication of annotator disagreements (eval/adjudication.json): accepted B labels become alternative evidence spans
    adj = json.load(open(ROOT / "eval/adjudication.json")); byq = {}
    for o in out: byq.setdefault(o["query"], o)
    for a in adj:
        if a["final"] == 1 and a.get("quote"):
            ck = a["key"].split("|")[1]; c = corp[ck]; d = docs[c["doc_id"]]; i = d.find(a["quote"], c["start"] - 5); assert i >= 0, a
            tgt = [o for o in out if o.get("_tmp") == a["qid"]][0]
            tgt["evidence"][a["span"]].setdefault("also", []).append(dict(doc_id=c["doc_id"], start=i, end=i + len(a["quote"]), quote=a["quote"]))
    for i, o in enumerate(out): o["qid"] = f"Q{i + 1:02d}"
    (ROOT / "eval").mkdir(exist_ok=True)
    with open(ROOT / "eval/gold.jsonl", "w", encoding="utf-8") as f:
        for o in out: f.write(json.dumps({k: o[k] for k in ("qid", "query", "type", "lang", "answerable", "evidence", "source_chunks")}, ensure_ascii=False) + "\n")
    import collections; print(len(out), collections.Counter(o["type"] for o in out))


if __name__ == "__main__": main()
