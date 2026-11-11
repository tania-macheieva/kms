"""Entity vocabulary for the item graph (curated from term frequencies in the corpus, then pruned by hand) and extraction."""
from __future__ import annotations
import re, json, math, collections, csv
from .data import HUB
VOCAB = {
 "Tool": "GATK GATK4 BCFtools VEP MultiQC DeepVariant BWA Mutect2 ASCAT SnpEff VQSR HaplotypeCaller MarkDuplicates DNAscope TIDDIT FastQC SVDB SnpSift FastP FreeBayes CNVKit CNVkit MSIsensor2 DragMap MuSE BaseRecalibrator ApplyBQSR GermlineCNVCaller VerifyBamID2 GENMOD FREEC DeepSomatic HermiT OntoClean Funcotator Manta Nextflow Docker Singularity Conda Cypher SPARQL SHACL".split(),
 "Format": "BAM CRAM VCF BCF FASTQ FastQ BED GFF CSV TSV JSON WDL gVCF".split(),
 "Annotation": "QD FS SOR MQ MQRankSum ReadPosRankSum QUAL DP AF AC AN GQ PL AD GT MAF".split(),
 "Genome": "GRCh37 GRCh38 hg19 hg38 b37".split(),
 "Concept": "WGS WES SNP SNV INDEL CNV SV UMI PoN LLM".split(),
}
PHRASES = {"Concept": ["hard filtering", "joint calling", "joint genotyping", "germline", "somatic", "structural variant", "copy number", "reference genome", "mapping quality", "base quality", "annotation", "provenance", "ontology", "reasoner", "embedding", "docker", "workflow", "quality control", "tumor", "cascade"]}
def _genes():
    return [r["symbol"] for r in csv.DictReader(open(HUB / "graph/nodes_Gene.csv", encoding="utf-8"))]
def build_vocab():
    v = {}
    for t, names in VOCAB.items():
        for n in names: v[n] = t
    for g in _genes(): v[g] = "Gene"
    return v
def _canon(n):   # merge spelling variants
    return {"GATK4": "GATK", "FastQ": "FASTQ", "CNVkit": "CNVKit"}.get(n, n)
def extract(text: str, vocab: dict):
    toks = set(re.findall(r"[A-Za-z][A-Za-z0-9\-]*", text)); out = {}
    for n, t in vocab.items():
        if n in toks: out[_canon(n)] = t
    low = text.lower()
    for t, ps in PHRASES.items():
        for p in ps:
            if p in low: out[p] = t
    return out
def build_entities(items):
    """-> (ent_of: list[dict name->type] per item, idf: dict name->float, types: dict). Entities with document frequency < 2 or > 40% of items are dropped."""
    vocab = build_vocab(); ent_of = [extract(it["text"], vocab) for it in items]; df = collections.Counter(n for e in ent_of for n in e); N = len(items)
    keep = {n for n, c in df.items() if 2 <= c <= 0.4 * N}; types = {}
    for e in ent_of:
        for n, t in e.items(): types[n] = t
    ent_of = [{n: t for n, t in e.items() if n in keep} for e in ent_of]; idf = {n: math.log((N + 1) / (df[n] + 0.5)) for n in keep}
    return ent_of, idf, {n: types[n] for n in keep}
