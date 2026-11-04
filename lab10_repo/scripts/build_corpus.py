"""R1: raw sources -> cleaned documents (data/docs_clean/*.md) -> fragments with metadata (data/corpus.jsonl)."""
import json, re, subprocess, shutil, sys, datetime
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT))
from src import chunking

import os
SRC = Path(os.environ.get("DKH_SRC", "/tmp/src")); LAB = Path(os.environ.get("DKH_LAB", "/home/claude"))  # live sources (optional; offline rebuild uses data/raw)
# (doc_id, repo, path, type, license)
EXT = [
 ("sarek_readme", "nf-core/sarek", "README.md", "readme", "MIT"),
 ("sarek_usage", "nf-core/sarek", "docs/usage.md", "usage-guide", "MIT"),
 ("sarek_output", "nf-core/sarek", "docs/output.md", "output-reference", "MIT"),
 ("sarek_vc_intro", "nf-core/sarek", "docs/usage/variantcalling/introduction.md", "tutorial", "MIT"),
 ("sarek_vc_theory", "nf-core/sarek", "docs/usage/variantcalling/theory.md", "tutorial", "MIT"),
 ("sarek_vc_sarek", "nf-core/sarek", "docs/usage/variantcalling/sarek.md", "tutorial", "MIT"),
 ("sarek_vc_interp", "nf-core/sarek", "docs/usage/variantcalling/interpretation.md", "tutorial", "MIT"),
 ("sarek_citations", "nf-core/sarek", "CITATIONS.md", "citations", "MIT"),
 ("rare_readme", "nf-core/raredisease", "README.md", "readme", "MIT"),
 ("rare_usage", "nf-core/raredisease", "docs/usage.md", "usage-guide", "MIT"),
 ("rare_output", "nf-core/raredisease", "docs/output.md", "output-reference", "MIT"),
 ("rare_citations", "nf-core/raredisease", "CITATIONS.md", "citations", "MIT"),
 ("bcftools_readme", "samtools/bcftools", "README.md", "readme", "MIT/Expat"),
 ("bcftools_manual", "samtools/bcftools", "doc/bcftools.txt", "manual", "MIT/Expat"),
 ("gatk_readme", "broadinstitute/gatk", "README.md", "readme", "Apache-2.0"),
 ("gatk_mutect2_wdl", "broadinstitute/gatk", "scripts/mutect2_wdl/README.md", "pipeline-readme", "Apache-2.0"),
 ("gatk_cnv_germline", "broadinstitute/gatk", "scripts/cnv_wdl/germline/README.md", "pipeline-readme", "Apache-2.0"),
 ("gatk_cnv_somatic", "broadinstitute/gatk", "scripts/cnv_wdl/somatic/README.md", "pipeline-readme", "Apache-2.0"),
 ("gatk_funcotator_wdl", "broadinstitute/gatk", "scripts/funcotator_wdl/README.md", "pipeline-readme", "Apache-2.0"),
 ("gatk_pathseq_wdl", "broadinstitute/gatk", "scripts/pathseq/wdl/README.md", "pipeline-readme", "Apache-2.0"),
 ("gatk_docker", "broadinstitute/gatk", "scripts/docker/README.md", "pipeline-readme", "Apache-2.0"),
 ("gatk_funco_tutorial", "broadinstitute/gatk", "docs/funcotator/forum_info/forum_post_tutorial.md", "tutorial", "Apache-2.0"),
 ("gatk_funco_spec", "broadinstitute/gatk", "docs/funcotator/forum_info/forum_post_annotation_specifications.md", "reference", "Apache-2.0"),
 ("gatk_funco_refdiff", "broadinstitute/gatk", "docs/funcotator/forum_info/forum_post_human_reference_discrepancies.md", "reference", "Apache-2.0"),
]
INT = [  # own project documents (Ukrainian); restricted = contain synthetic pedigree/patient-like records
 ("int_cq_scope", "lab4_repo/docs/scope_cq.md", "internal-report"), ("int_rules", "lab4_repo/docs/rules_analysis.md", "internal-report"),
 ("int_reasoner", "lab7_repo/docs/reasoner_log.md", "internal-report"), ("int_onto_eval", "lab7_repo/docs/onto_eval.md", "internal-report"),
 ("int_situations", "lab7_repo/docs/situations_check.md", "internal-report"), ("int_sparql", "lab8_repo/docs/sparql_results.md", "internal-report"),
 ("int_shacl", "lab8_repo/docs/shacl_report.md", "internal-report"), ("int_cq_map", "lab9_repo/docs/cq_mapping.md", "internal-report"),
 ("int_cypher", "lab9_repo/docs/cypher_results.md", "internal-report"),
]
PERSON = re.compile(r"\b(Olena|Iryna|Petro|Marta|Sofiia|Halyna|Andrii)\b")


def md_clean(t: str) -> str:
    t = re.sub(r"\A---\n.*?\n---\n", "", t, flags=re.S)                       # R1 front matter
    t = re.sub(r"<!--.*?-->", "", t, flags=re.S)                               # R2 html comments
    t = re.sub(r"```mermaid.*?```", "", t, flags=re.S)                         # R3 diagrams
    t = re.sub(r"\[!\[[^\]]*\]\([^)]*\)\]\([^)]*\)", "", t)                    # R4 badges
    t = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", t)                                 # R5 images
    t = re.sub(r"</?(img|p|picture|source|br|div|a|details|summary|b|i|sup|sub|kbd|code|h\d|table|tr|td|th)\b[^>]*>", " ", t, flags=re.I)  # R6 html tags
    t = re.sub(r"\[([^\]]+)\]\(([^)]*)\)", r"\1", t)                           # R7 links -> text
    t = re.sub(r"^\s*>\s*\[!(\w+)\]\s*$", lambda m: m.group(1).upper() + ":", t, flags=re.M)  # R8 callouts
    t = re.sub(r"^>\s?", "", t, flags=re.M)
    t = re.sub(r"^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)*\|?\s*$", "", t, flags=re.M)  # R9 table separators
    t = re.sub(r"^#{1,6}\s*(table of contents|contents|toc)\s*$.*?(?=^#{1,6}\s|\Z)", "", t, flags=re.S | re.M | re.I)  # R10 TOC
    t = re.sub(r"^\s*[-*]\s*\[[^\]]+\]\(#[^)]*\)\s*$", "", t, flags=re.M)      # R11 anchor-only list items
    return finish(t)


def adoc_clean(t: str) -> str:
    t = "\n".join(l for l in t.split("\n") if not l.startswith("//"))          # R12 asciidoc comments
    lines, out, i = t.split("\n"), [], 0
    lv = {"=": 1, "-": 2, "~": 3, "^": 4}
    while i < len(lines):
        if i + 1 < len(lines) and lines[i].strip() and re.fullmatch(r"([=\-~^])\1{2,}", lines[i + 1].strip()) and abs(len(lines[i + 1].strip()) - len(lines[i].strip())) <= 2:
            out.append("#" * lv[lines[i + 1].strip()[0]] + " " + lines[i].strip()); i += 2
        else:
            out.append(lines[i]); i += 1
    t = "\n".join(out)
    t = re.sub(r"^(={2,})\s+(\S.*)$", lambda m: "#" * (len(m.group(1)) - 1) + " " + m.group(2), t, flags=re.M)   # inline "=== X" headings
    t = t.replace("\\<", "<").replace("\\>", ">").replace("{date}", "").replace("{version}", "")
    t = re.sub(r"^(\+|--)\s*$", "", t, flags=re.M)                              # R13 list continuation / block delimiters
    t = re.sub(r"^:\w+:.*$", "", t, flags=re.M)
    t = re.sub(r"\*\*?([^*\n]+)\*\*?", r"\1", t); t = re.sub(r"'([A-Za-z_ -]+)'", r"\1", t)  # R14 emphasis marks
    return finish(t)


def finish(t: str) -> str:
    t = re.sub(r"[ \t]+\n", "\n", t); t = re.sub(r"[ \t]{2,}", " ", t)          # R15 whitespace
    t = re.sub(r"\n{3,}", "\n\n", t)
    t = re.sub(r"^(#{1,6}[^\n]*)\n(?=\s*#{1,6}\s)", "", t, flags=re.M)         # R16 empty headings (heading followed directly by heading)
    return t.strip() + "\n"


def title_of(t, fb):
    m = re.search(r"^#\s+(.+)$", t, re.M); return m.group(1).strip() if m else fb


def main():
    (ROOT / "data/raw").mkdir(parents=True, exist_ok=True); (ROOT / "data/docs_clean").mkdir(exist_ok=True)
    docs, shas = [], {}
    meta_f = ROOT / "data/sources.json"; meta = json.load(open(meta_f)) if meta_f.exists() else {}
    for did, repo, path, typ, lic in EXT:
        d = SRC / repo.split("/")[1]; rawf = ROOT / "data/raw" / f"{did}{Path(path).suffix}"
        if (d / path).exists():   # live clone available: record commit + date, refresh the raw copy
            shas[repo] = shas.get(repo) or subprocess.check_output(["git", "-C", str(d), "rev-parse", "HEAD"], text=True).strip()
            date = subprocess.check_output(["git", "-C", str(d), "log", "-1", "--format=%cs", "--", path], text=True).strip()
            shutil.copy(d / path, rawf); meta[did] = dict(sha=shas[repo], date=date)
        else:                     # offline rebuild from data/raw + data/sources.json (what the zip contains)
            shas[repo] = meta[did]["sha"]; date = meta[did]["date"]
        raw = rawf.read_text(encoding="utf-8", errors="replace")
        clean = adoc_clean(raw) if path.endswith(".txt") else md_clean(raw)
        docs.append(dict(doc_id=did, title=title_of(clean, did), type=typ, date=date, sensitivity="public", lang="en", license=lic,
                         source_url=f"https://github.com/{repo}/blob/{shas[repo]}/{path}", text=clean, raw_chars=len(raw)))
    for did, path, typ in INT:
        p = LAB / path; rawf = ROOT / "data/raw" / f"{did}.md"
        if p.exists(): shutil.copy(p, rawf); meta[did] = dict(date=datetime.date.fromtimestamp(p.stat().st_mtime).isoformat())
        raw = rawf.read_text(encoding="utf-8")
        clean = md_clean(raw)
        sens = "restricted" if PERSON.search(raw) else "internal"
        docs.append(dict(doc_id=did, title=title_of(clean, did), type=typ, date=meta[did]["date"],
                         sensitivity=sens, lang="uk", license="author's own work (not redistributed)", source_url="local:" + path, text=clean, raw_chars=len(raw)))
    json.dump(meta, open(meta_f, "w"), indent=1)
    for d in docs: (ROOT / "data/docs_clean" / f"{d['doc_id']}.md").write_text(d["text"], encoding="utf-8")
    json.dump([{k: v for k, v in d.items() if k != "text"} for d in docs], open(ROOT / "data/docs_manifest.json", "w"), ensure_ascii=False, indent=1)
    ch = chunking.chunk_corpus(docs, "heading")
    by = {d["doc_id"]: d for d in docs}
    with open(ROOT / "data/corpus.jsonl", "w", encoding="utf-8") as f:
        for c in ch:
            d = by[c.doc_id]
            f.write(json.dumps(dict(chunk_id=c.id, doc_id=c.doc_id, title=d["title"], section=c.section, type=d["type"], date=d["date"],
                                    sensitivity=d["sensitivity"], source_url=d["source_url"], lang=d["lang"], start=c.start, end=c.end,
                                    n_words=chunking.nwords(c.text), text=c.text), ensure_ascii=False) + "\n")
    print(len(docs), "docs", len(ch), "chunks", sum(d["raw_chars"] for d in docs), "->", sum(len(d["text"]) for d in docs), "chars")


if __name__ == "__main__": main()
