import json
c1=json.load(open('cand64.json')); c2=json.load(open('cand70.json'))
S=lambda i:(c1[i-1] if i<=64 else c2[i-65])
G={
 2:[("GenomicsDB datastore","contains","gVCFs")],
 4:[("These pages","is_a","tutorial workshop")],
 7:[("samtools","performs","coordinate-sorting of aligned reads"),("GATK MarkDuplicatesSpark","performs","duplicate marking")],
 8:[("Varlociraptor","supports","different scenario files")],
 9:[("sarek","performs","preprocessing"),("sarek","uses","Strelka")],
 13:[("VEP","uses","output files")],
 21:[("This repo","contains","scripts for creating and pushing two docker images"),("gatkbase","is_a","basic docker image")],
 24:[("samtools sort","performs","coordinate sorting of aligned reads")],
 27:[("VQSR","is_a","filtering tool")],
 34:[("Funcotator","supports","user's own annotations"),("Funcotator","uses","set of data sources")],
 41:[("image","contains","GATK4")],
 44:[("pipeline","uses","one container per process")],
 46:[("M2 WDL","uses","Funcotator"),("M2 WDL","produces","TCGA MAF")],
 49:[("It","uses","Docker/Singularity containers")],
 59:[("It","contains","vcf* commands")],
 60:[("GATK Resource Bundle","contains","PathSeq reference files")],
 66:[("Strelka","performs","somatic variant calling"),("Strelka","uses","candidate indels from Manta"),("Manta","produces","candidate indels")],
 68:[("variant_vcf_to_funcotate","contains","variants to annotate")],
 69:[("Some tools","uses","tabix- or CSI-indexed files")],
 70:[("pipeline","performs","variant calling"),("pipeline","uses","Sentieon DNAscope"),("Sentieon DNAscope","uses","machine learning model")],
 71:[("Research variants","contains","all the variants"),("Research variants","contains","candidate variants")],
 72:[("Default supported datasources","contains","GENCODE"),("Default supported datasources","contains","dbSNP"),("Default supported datasources","contains","gnomAD"),("Default supported datasources","contains","COSMIC")],
 73:[("UMIs","performs","identification of reads from the same original DNA molecule")],
 77:[("BBSplit","is_a","tool"),("BBSplit","performs","binning reads"),("BBSplit","uses","BBMap")],
 80:[("This repository","contains","next generation of the Genome Analysis Toolkit (GATK)")],
 82:[("REViewer","uses","files generated")],
 83:[("Each read","supports","presence of an allele")],
 84:[("Sentieon's sort utility","performs","coordinate sorting of aligned reads")],
 86:[("Annotation-cache","is_a","open AWS registry resource"),("Annotation-cache","contains","mirror of some cache files"),("Annotation-cache","supports","Sarek")],
 87:[("bcftools isec","performs","intersection and complements of two sets")],
 88:[("Sarek","supports","some of the functions in Sentieon")],
 90:[("The pipeline","uses","Nextflow"),("Nextflow","is_a","workflow tool")],
 95:[("data sources","uses","hg19 reference")],
 103:[("These files","contains","table of data")],
 105:[("GATK4","supports","Spark cluster"),("GATK4","supports","Google Dataproc")],
 108:[("tar.gz","contains","data sources for Funcotator")],
 110:[("Funcotator","is_a","functional annotation tool"),("core GATK toolset","contains","Funcotator")],
 113:[("MultiQC","performs","summarizing analysis results for multiple tools and samples")],
 125:[("GATK4 docker image","uses","this one"),("gatk4","is_a","official docker image for GATK4")],
 12:[],18:[],26:[],31:[],36:[],39:[],53:[],65:[],89:[],109:[],112:[],
}
import random; ids=sorted(G); random.Random(1).shuffle(ids)
rows=[]
for n,i in enumerate(ids,1):
    d,s=S(i); rows.append({"id":f"S{n:02d}","doc":d,"sentence":s,"gold":[list(t) for t in G[i]]})
print(len(rows),sum(len(r['gold']) for r in rows),sum(not r['gold'] for r in rows))
json.dump(rows,open('gold.json','w'),ensure_ascii=False,indent=1)
json.dump([{"id":r['id'],"sentence":r['sentence']} for r in rows],open('sentences_only.json','w'),ensure_ascii=False,indent=1)
