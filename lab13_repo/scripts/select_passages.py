"""Select the passages to annotate: 24 external documents (tool documentation), 3-4 heading-chunks each (60-200 words) with enough domain terms; split dev/test BY DOCUMENT. Seed 13."""
import json, random, re
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; random.seed(13)
chunks = [json.loads(l) for l in open(ROOT / "data/corpus_lab10.jsonl", encoding="utf-8")]
DOCS = ["sarek_readme", "sarek_usage", "sarek_output", "sarek_citations", "sarek_vc_theory", "sarek_vc_sarek", "sarek_vc_interp", "sarek_vc_intro", "rare_readme", "rare_usage", "rare_output", "rare_citations",
        "bcftools_manual", "bcftools_readme", "gatk_readme", "gatk_docker", "gatk_mutect2_wdl", "gatk_funco_tutorial", "gatk_funco_spec", "gatk_funco_refdiff", "gatk_cnv_germline", "gatk_cnv_somatic", "gatk_funcotator_wdl", "gatk_pathseq_wdl"]
TEST = {"bcftools_manual", "sarek_output", "rare_usage", "gatk_funco_tutorial", "gatk_readme", "sarek_vc_sarek", "rare_citations", "gatk_cnv_somatic"}
N = {"bcftools_manual": 8, "sarek_usage": 5, "sarek_output": 5, "gatk_funco_tutorial": 5, "rare_usage": 5, "gatk_readme": 5}   # default 3
HINT = re.compile(r"\b(VCF|BAM|CRAM|FASTA|BED|GTF|GFF|FASTQ|bcftools|GATK|Mutect2|Funcotator|HaplotypeCaller|samtools|BWA|VEP|snpEff|Strelka|dbSNP|gnomAD|ClinVar|GRCh3\d|MultiQC|Nextflow|Docker|Singularity|QD|FS|SOR|MQ|DP|QUAL)\b")
out = []
for d in DOCS:
    cs = [c for c in chunks if c["doc_id"] == d and 40 <= c["n_words"] <= 220 and len(set(HINT.findall(c["text"]))) >= 1]
    random.shuffle(cs); k = N.get(d, 3)
    for c in sorted(cs[:k], key=lambda c: c["start"]): out.append(dict(doc_id=d, chunk_id=c["chunk_id"], section=c["section"], start=c["start"], end=c["end"], text=c["text"], split="test" if d in TEST else "dev", source_url=c["source_url"]))
for i, p in enumerate(out, 1): p["id"] = f"P{i:03d}"
(ROOT / "data/passages.jsonl").write_text("\n".join(json.dumps(p, ensure_ascii=False) for p in out) + "\n", encoding="utf-8")
import collections; print(len(out), "passages,", len({p["doc_id"] for p in out}), "docs;", collections.Counter(p["split"] for p in out), "words", sum(len(p["text"].split()) for p in out))
