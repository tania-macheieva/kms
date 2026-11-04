## Introduction

This document describes the output produced by the pipeline. Most of the plots are taken from the MultiQC report, which summarises results at the end of the pipeline.

The directories listed below will be created in the results directory after the pipeline has finished. All paths are relative to the top-level results directory.

## Pipeline overview

The pipeline is built using Nextflow and processes data using the following steps:

- nf-core/raredisease: Output
 - Introduction
 - Pipeline overview
 - Alignment
 - Mapping
 - Bwa-mem2
 - BWA
 - BWA-MEME
 - Sentieon bwa mem
 - Duplicate marking
 - Picard's MarkDuplicates
 - Sentieon Dedup
 - Subsample mitochondrial alignments
 - Quality control and reporting
 - Quality control
 - FastQC
 - Mosdepth
 - Picard tools
 - Chromograph coverage
 - Sention WgsMetricsAlgo
 - TIDDIT's cov and UCSC WigToBigWig
 - VerifyBamID2
 - Reporting
 - MultiQC
 - Variant calling - SNV
 - DeepVariant
 - Sentieon DNAscope
 - Variant calling - SV
 - Manta
 - TIDDIT sv
 - GATK GermlineCNVCaller - CNV calling
 - CNVnator - CNV calling
 - SVDB merge
 - Variant calling - repeat expansions
 - Expansion Hunter
 - Stranger
 - Annotation - SNV
 - bcftools roh
 - vcfanno
 - CADD
 - VEP
 - UPD
 - Chromograph
 - Rhocall viz
 - Annotation - SV
 - SVDB query
 - VEP
 - Mitochondrial analysis
 - Alignment and variant calling
 - MT deletion script
 - MitoSAlt
 - saltshaker
 - Annotation
 - vcfanno
 - CADD
 - VEP
 - Filtering and ranking
 - Filter_vep
 - GENMOD
 - Mobile element analysis
 - Calling mobile elements
 - Annotating mobile elements
 - Variant evaluation
 - Gens
 - Peddy
 - Pipeline information



##### Bwa-mem2

Bwa-mem2 used to map the reads to a reference genome. The aligned reads are coordinate sorted with samtools sort. These files are treated as intermediates and are not placed in the output folder by default.

##### BWA

BWA used to map the reads to a reference genome. The aligned reads are coordinate sorted with samtools sort. These files are treated as intermediates and are not placed in the output folder by default. It is not the default aligner, but it can be chosen by setting `--aligner` option to bwa.

##### BWA-MEME

BWA-MEME used to map the reads to a reference genome. The aligned reads are coordinate sorted with samtools sort. These files are treated as intermediates and are not placed in the output folder by default. It is not the default aligner, but it can be chosen by setting `--aligner` option to bwameme.

##### Sentieon bwa mem

Sentieon's bwa mem is the software accelerated version of the bwa-mem algorithm. It is used to efficiently perform the alignment using BWA. Aligned reads are then coordinate sorted using Sentieon's sort utility. These files are treated as intermediates and are not placed in the output folder by default. It is not the default aligner, but it can be chosen by setting `--aligner` option to "sentieon".


##### Picard's MarkDuplicates

Picard MarkDuplicates is used for marking PCR duplicates that can occur during library amplification. This is essential as the presence of such duplicates results in false inflated coverages, which in turn can lead to overly-confident genotyping calls during variant calling. Only reads aligned by Bwa-mem2, bwameme and bwa are processed by this tool. By default, alignment files are published in bam format. To publish cram files instead, use `--save_all_mapped_as_cram` for the full (unfiltered) alignment, or `--save_noalt_mapped_as_cram` for the alt-filtered alignment (requires `--exclude_alt`).

 Output files from Alignment

- `{outputdir}/alignment/`
 - `*_sorted_md.bam|*_sorted_md.cram`: Full (unfiltered) alignment file. Published as bam by default, or as cram when `--save_all_mapped_as_cram` is set.
 - `*_sorted_md_primary_contigs.cram`: Alt-filtered alignment file in cram format. Published when `--save_noalt_mapped_as_cram` is set (requires `--exclude_alt`). Contains only primary chromosomes (GRCh37: 1-22,X,Y,MT / GRCh38: chr1-chr22,chrX,chrY,chrM).
 - `*.bai|*.crai`: Index of the corresponding bam/cram file.
 - `*.txt`: Text file containing the dedup metrics.

##### Sentieon Dedup

Sentieon Dedup is the algorithm used by Sentieon's driver to remove duplicate reads. Only reads aligned by Sentieon's implementation of bwa are processed by this algorithm. By default, alignment files are published in bam format. To publish cram files instead, use `--save_all_mapped_as_cram` for the full (unfiltered) alignment, or `--save_noalt_mapped_as_cram` for the alt-filtered alignment (requires `--exclude_alt`).

 Output files from Alignment

- `{outputdir}/alignment/`
 - `*_sorted_md.bam|*_sorted_md.cram`: Full (unfiltered) alignment file. Published as bam by default, or as cram when `--save_all_mapped_as_cram` is set.
 - `*_sorted_md_primary_contigs.cram`: Alt-filtered alignment file in cram format. Published when `--save_noalt_mapped_as_cram` is set (requires `--exclude_alt`). Contains only primary chromosomes (GRCh37: 1-22,X,Y,MT / GRCh38: chr1-chr22,chrX,chrY,chrM).
 - `*.bai|*.crai`: Index of the corresponding bam/cram file.
 - `*.metrics`: Text file containing the dedup metrics.

#### Subsample mitochondrial alignments

Samtools view is used by the pipeline to subsample mitochondrial alignments to a user specified coverage. The file is mainly intended to be used for visualization of MT alignments in IGV. The non-subsampled bam file is used for variant calling and other downstream analysis steps.

 Output files from Alignment

- `{outputdir}/alignment/`
 - `<sampleid>_mt_subsample.bam`: Alignment file in bam format.
 - `<sampleid>_mt_subsample.bam.bai`: Index of the corresponding bam file.



##### FastQC

FastQC gives general quality metrics about your sequenced reads. It provides information about the quality score distribution across your reads, per base sequence content (%A/T/G/C), adapter contamination and overrepresented sequences. For further reading and documentation see the FastQC help pages.

 Output files

- `{outputdir}/fastqc/{sampleid}_T*/`
 - `*_fastqc.html`: FastQC report containing quality metrics.
 - `*_fastqc.zip`: Zip archive containing the FastQC report, tab-delimited data file and plot images.

:::note
The FastQC plots displayed in the MultiQC report shows _untrimmed_ reads. They may contain adapter sequence and potentially regions with low quality.
:::

##### Mosdepth

Mosdepth is used to report quality control metrics such as coverage, and GC content from alignment files. The global distribution file, generated by this program is passed to MultiQC for generating the following plots,

- Cumulative coverage distribution
- Coverage distribution
- Average coverage per contig

 Output files

- `{outputdir}/qc_bam/`
 - `<sampleid>_mosdepth.global.dist.txt`: This file contains a cumulative distribution indicating the proportion of total bases that were covered for at least a given coverage value across each chromosome and the whole genome.
 - `<sampleid>_mosdepth.summary.txt`: This file contains summary statistics, such as mean, minimum and maximum coverage per genomic contig.

##### Picard tools

Picard's CollectMutipleMetrics, CollectHsMetrics, and CollectWgsMetrics We use Picardtools' CollectWgsMetrics and CollectHsMetrics utilities to calculate metrics about coverage and performance of WGS & WES experiments. In addition to those metrics, we use CollectMultipleMetrics to gather information about alignment summary, insert size, GC content etc., The metrics generated by these three utilites are passed along to MultiQC to generate several plots as well.

 Output files

- `{outputdir}/qc_bam/`
 - `<sampleid>_hsmetrics.CollectHsMetrics.coverage_metrics`:
 - `<sampleid>_multiplemetrics.CollectMultipleMetrics.alignment_summary_metrics`:
 - `<sampleid>_multiplemetrics.CollectMultipleMetrics.base_distribution_by_cycle_metrics`:
 - `<sampleid>_multiplemetrics.CollectMultipleMetrics.insert_size_metrics`:
 - `<sampleid>_multiplemetrics.CollectMultipleMetrics.quality_by_cycle_metrics`:
 - `<sampleid>_multiplemetrics.CollectMultipleMetrics.quality_distribution_metrics`:
 - `<sampleid>_wgsmetrics.CollectWgsMetrics.coverage_metrics`:
 - `<sampleid>_wgsmetrics_y.CollectWgsMetrics.coverage_metrics`:

##### Chromograph coverage

Chromograph is a python package to create PNG images from genetics data such as BED and WIG files.

 Output files

- `{outputdir}/qc_bam/<sampleid>_chromographcov/*.png` plots showing coverage across chromosomes for each chromosome.

##### Sention WgsMetricsAlgo

Sentieon's WgsMetricsAlgo is the Sentieon's equivalent of Picard's CollectWgsMetrics.

 Output files

- `{outputdir}/qc_bam/`
 - `<sampleid>_wgsmetrics.txt`:

##### TIDDIT's cov and UCSC WigToBigWig

TIDDIT's cov is used to analyse the read depth of a bam file and generates a coverage report in wig format. This file is later passed to UCSC WigToBigWig to convert the file into a bigwig.

 Output files

- `{outputdir}/qc_bam/`
 - `<sampleid>_tidditcov.wig`:
 - `<sampleid>.bw`:

##### VerifyBamID2

VerifyBamID2 is used to analyse a bam file and generates a contamination report. The pipeline will only generate the following files when the parameters `verifybamid_svd_bed`, `verifybamid_svd_mu`, and `verifybamid_svd_ud` are provided.

 Output files

- `{outputdir}/qc_bam/`
 - `<sampleid>.selfSM`:
 - `<sampleid>.Ancestry`:


##### MultiQC

MultiQC is a visualization tool that generates a single HTML report summarising all samples in your project. Most of the pipeline QC results are visualised in the report and further statistics are available in the report data directory.

Results generated by MultiQC collate pipeline QC from supported tools e.g. FastQC. The pipeline has special steps which also allow the software versions to be reported in the MultiQC output for future traceability. For more information about how to use MultiQC reports, see <http://multiqc.info>.

 Output files

- `multiqc/`
 - `multiqc_report.html`: a standalone HTML file that can be viewed in your web browser.
 - `multiqc_data/`: directory containing parsed statistics from the different tools used in the pipeline.
 - `multiqc_plots/`: directory containing static images from the report in various formats.


#### DeepVariant

DeepVariant is a deep learning-based variant caller that takes aligned reads, produces pileup image tensors from them, classifies each tensor using a convolutional neural network and finally reports the results in a standard VCF or gVCF file. Variant calls generated by DeepVariant are joint genotyped using GLnexus, and then normalized using bcftools norm. Only the normalized vcfs are placed in the output folder by default.

**NB**: In case you are running the separate mitochondrial analysis, mitochondrial calls are filtered from the normalized vcfs before they are published using GATK SelectVariants.

 Output files

- `call_snv/genome`
 - `<case_id>_snv.vcf.gz`: normalized vcf file containing no MT variants.
 - `<case_id>_snv.vcf.gz.tbi`: index of the vcf file containing no MT variants.

#### Sentieon DNAscope

The pipeline performs variant calling using Sentieon DNAscope with a machine learning model. This approach identifies the candidate sites with a higher accuracy, and calculates genotypes for each sample at that site. These files are treated as intermediates and are not placed in the output folder by default. DNAscope is not run by default. To use DNAscope instead of DeepVariant, set `--variant_caller` to sentieon.

 Output files

- `call_snv/genome`
 - `<case_id>_snv.vcf.gz`: normalized vcf file containing no MT variants.
 - `<case_id>_snv.vcf.gz.tbi`: index of the vcf file containing no MT variants.


#### Manta

Manta calls structural variants (SVs) and indels from mapped paired-end sequencing reads. It combines paired and split-read evidence during SV discovery and scoring to improve accuracy, but does not require split-reads or successful breakpoint assemblies to report a variant in cases where there is strong evidence otherwise. Output vcf files are treated as intermediates and are not placed in the output folder.

#### TIDDIT sv

TIDDIT's sv is used to identify chromosomal rearrangements using sequencing data. TIDDIT identifies intra and inter-chromosomal translocations, deletions, tandem-duplications and inversions, using supplementary alignments as well as discordant pairs. TIDDIT searches for discordant reads and split reads (supplementary alignments). Output vcf files are treated as intermediates and are not placed in the output folder.

#### GATK GermlineCNVCaller - CNV calling

GATK GermlineCNVCaller is used to identify copy number variants in germline samples given their read counts and a model describing a sample's ploidy. Output vcf files are treated as intermediates and are not placed in the output folder.

#### CNVnator - CNV calling

CNVnator is used to identify copy number variants in germline samples given a bam file. Output vcf files are treated as intermediates and are not placed in the output folder.

#### SVDB merge

SVDB merge is used to merge the variant calls from GATK's GermlineCNVCaller (only if `skip_tools` doesn't include germlinecnvcaller), Manta, and TIDDIT. Output files are published in the output folder.

 Output files

- `call_sv/genome`
 - `<case_id>_sv_merge.vcf.gz`: file containing the merged variant calls. As of version 2.3.0, this file also contains mitochondrial structural variants.
 - `<case_id>_sv_merge.vcf.gz.tbi`: index of the file containing the merged variant calls.


#### Expansion Hunter

Expansion Hunter aims to estimate sizes of repeat sequences by performing a targeted search through alignments that span, flank, and are fully contained in each repeat. The files generated are ready to be used with REViewer.

 Output files

- `repeat_expansions/`
 - `<sample_id>_repeat_expansion.vcf`: file containing variant calls.
 - `<sample_id>_exphunter_sorted.bam`: A BAMlet containing alignments of reads that overlap or located in close proximity to each variant identified by ExpansionHunter
 - `<sample_id>_exphunter_sorted.bam.bai`: Index of the BAMlet file

#### Stranger

Stranger annotates output files from Expansion Hunter with the pathologic implications of the repeat sizes.

 Output files

- `repeat_expansions/`
 - `<case_id>_repeat_expansion_stranger.vcf.gz`: file containing variant calls.
 - `<case_id>_repeat_expansion_stranger.vcf.gz.tbi`: index of the file containing variant calls.


#### bcftools roh

bcftools roh is a program for detecting runs of homo/autozygosity.from only bi-allelic sites. The output files are not published in the output folder, and is passed to vcfanno for further annotation.

:::note
In the case of running a quattro, i.e. two affected children and their parents, only one of the probands will be used for annotating regions of homozygosity. This is a known limitation that we are hoping to solve in a future release.
:::

#### vcfanno

vcfanno allows you to quickly annotate your VCF with any number of INFO fields from any number of VCFs. It uses a simple configuration file to allow the user to specify the source annotation files and fields and how they will be added to the info of the query VCF. Values are pulled by name from the INFO field with special-cases of ID and FILTER to pull from those VCF columns. The output files are not published in the output folder, and is passed to CADD and/or VEP for further annotation.

We recommend using vcfanno to annotate SNVs with precomputed CADD scores (files can be downloaded from here).

#### CADD

CADD is a tool for scoring the deleteriousness of single nucleotide variants as well as insertion/deletions variants in the human genome. In nf-core/raredisease, SNVs can be annotated with precomputed CADD scores using vcfanno. However, for small indels they will be calculated on the fly by CADD. The output files are not published in the output folder, and is passed to VEP for further annotation.

#### VEP

VEP determines the effect of your variants on genes, transcripts, and protein sequence, as well as regulatory regions. We recommend annotating with the following plugins:

- LoFtool
- pLI
- SpliceAI
- MaxEntScan

Based on VEP annotations, custom scripts used by the pipeline further annotate each record with the most severe consequence, and pli scores.

**NB**: Output files described below do not include mitochondrial annotations only if --skip_subworklows includes mt_annotation.

 Output files

- `annotate_snv/genome`
 - `<case_id>_<rhocall_vcfanno|vcfanno>_filter_<cadd_vep|vep>.vcf.gz`: file containing bcftools roh, vcfanno, cadd and vep annotations.
 - `<case_id>_<rhocall_vcfanno|vcfanno>_filter_<cadd_vep|vep>.vcf.gz.tbi`: index of the file containing bcftools roh, vcfanno, cadd and vep annotations.

#### UPD

UPD calls regions of uniparental disomy from germline exome/wgs trios. Output from UPD is passed to chromograph for making plots.

#### Chromograph

Chromograph is a python package to create PNG images from genetics data such as BED and WIG files.

 Output files

- `annotate_snv/genome/*sites_chromograph`
 - `<sample_id>_rohann_vcfanno_upd_sites_<chr#>.png`: file containing a plot showing upd sites across chromosomes.
- `annotate_snv/genome/*regions_chromograph`
 - `<sample_id>_rohann_vcfanno_upd_regions_<chr#>.png`: file containing a plot showing upd regions across chromosomes.
- `annotate_snv/genome/*autozyg_chromograph`
 - `<sample_id>_rhocallviz_<chr#>.png`: file containing a plot showing regions of autozygosity across chromosomes.

#### Rhocall viz

Rhocall viz plots binned zygosity and RHO-regions.

 Output files

- `annotate_snv/genome/<sample_id>_rhocallviz/<sample_id>_rhocallviz.bed`: file containing regions of homozygosity in bed format.
- `annotate_snv/genome/<sample_id>_rhocallviz/<sample_id>_rhocallviz.wig`: file containing the fraction of homozygous SNPs in wig format.
- `annotate_snv/genome/<sample_id>_rhocallviz/<sample_id>_rhocallviz.bw`: file containing the fraction of homozygous SNPs in bigwig format.


#### SVDB query

SVDB query allows you to quickly annotate your VCF with data from one or more structural variant databases. The output files are not published in the output folder, and is passed to vep for further annotation.

#### VEP

VEP determines the effect of your variants on genes, transcripts, and protein sequence, as well as regulatory regions. We recommend annotating with pLI plugin, along with any other custom plugins you may want too use. Based on VEP annotations, custom scripts used by the pipeline further annotate each record with the most severe consequence, and pli scores.

 Output files

- `annotate_sv/`
 - `<case_id>_svdbquery_vep.vcf.gz`: file containing svdb query, and vep annotations.
 - `<case_id>_svdbquery_vep.vcf.gz.tbi`: index of the file containing bcftools roh, vcfanno, and vep annotations.
 - `<case_id>_svdbquery_vep_summary.html`: vep summary.

### Mitochondrial analysis

Mitochondrial analysis is run by default. If you want to turn off annotations set `--skip_subworkflows mt_annotation`.

#### Alignment and variant calling

Alignment and variant calling - GATK Mitochondrial short variant discovery pipeline The mitochondrial genome poses several challenges to the identification and understanding of somatic variants. The circularity of the mitochondrial genome means that the breakpoint in the reference genome is at an arbitrary position in the non-coding control region, creating a challenge in analyzing variation. Additionally, insertions of mitochondrial DNA into the nuclear genome (NuMTs) complicate the mapping of the mitochondrial genome and the distinction between NuMTs and the mitochondrial contig of interest. Lastly, mitochondrial variants often have very low heteroplasmy. Such low allele fraction (AF) variants can thus be mistaken for inherent sequencer noise.

The pipeline for mitochondrial variant discovery, using Mutect2, uses a high sensitivity to low AF and separate alignments using opposite genome breakpoints to allow for the tracing of lineages of rare mitochondrial variants.

- `call_snv/mitochondria`
 - `<case_id>_mitochondria.vcf.gz`: normalized vcf file containing MT variants.
 - `<case_id>_mitochondria.vcf.gz.tbi`: index of the vcf file containing MT variants.

##### MT deletion script

MT deletion script lists the fraction of mitochondrially aligning read pairs (per 1000) that appear discordant, as defined by an insert size of more than 1.2 kb (and less than 15 kb due to the circular nature of the genome) using samtools.

- `call_sv`
 - `<sample_id>_mitochondria_deletions.txt`: file containing deletions.

##### Saltshaker

MitoSAlt allows the detection and quantification of mtDNA strucutral variants.
Saltshaker allows for downstream clustering and classification of mtDNA strucutral variants. Called variants are combined with structural variants called in the nuclear genome.

- `call_sv`
 - `<sample_id>.saltshaker_classify.html`: report containing case-level classification of mitochondrial deletions.
 - `<sample_id>.saltshaker.png`: circos plot.


##### vcfanno

vcfanno allows you to quickly annotate your VCF with any number of INFO fields from any number of VCFs. It uses a simple conf file to allow the user to specify the source annotation files and fields and how they will be added to the info of the query VCF. Values are pulled by name from the INFO field with special-cases of ID and FILTER to pull from those VCF columns. The output files are not published in the output folder, and is passed to vep for further annotation.

We recommend using vcfanno to annotate SNVs with precomputed CADD scores (files can be downloaded from here).

##### CADD

CADD is a tool for scoring the deleteriousness of single nucleotide variants as well as insertion/deletions variants in the human genome. In nf-core/raredisease, SNVs can be annotated with precomputed CADD scores using vcfanno. However, for small indels they will be calculated on the fly by CADD. The output files are not published in the output folder, and is passed to VEP for further annotation.

##### VEP

VEP determines the effect of your variants on genes, transcripts, and protein sequence, as well as regulatory regions.

 Output files

- `annotate_snv/mitochondria`
 - `<case_id>_mitochondria_vcfanno_<cadd_vep|vep>.vcf.gz`: file containing mitochondrial annotations.
 - `<case_id>_mitochondria_vcfanno_<cadd_vep|vep>.vcf.gz.tbi`: index of the file containing mitochondrial annotations.


#### Filter_vep

filter_vep from VEP is used to subset the variants based on a list of HGNC ID:s. Typical use case is that you want to filter your results to only include variants in a predefined set of clinically relevant genes. This step is optional and can be disabled by using the flag `--skip_subworkflows generate_clinical_set`. You will always get the complete VCF together with the clinical VCF.

#### GENMOD

GENMOD is a simple to use command line tool for annotating and analyzing genomic variations in the VCF file format. GENMOD can annotate genetic patterns of inheritance in vcf files with single or multiple families of arbitrary size. Each variant will be assigned a predicted pathogenicity score. The score will be given both as a raw score and a normalized score with values between 0 and 1. The tags in the INFO field are `RankScore` and `RankScoreNormalized`. The score can be configured to fit your annotations and preferences by modifying the score config file.

 Output files

- `rank_and_filter/`
 - `<case_id>_mt_ranked_clinical.vcf.gz`: file containing clinically relevant mitochondrial SNVs, and only contains variants less than 5%VAF by default.
 - `<case_id>_mt_ranked_clinical.vcf.gz.tbi`: index of the file containing clinically relevant mitochondrial SNVs.
 - `<case_id>_mt_ranked_research.vcf.gz`: file containing mitochondrial SNV annotations with their rank scores.
 - `<case_id>_mt_ranked_research.vcf.gz.tbi`: index of the file containing mitochondrial SNV annotations with their rank scores.
 - `<case_id>_snv_ranked_clinical.vcf.gz`: file containing clinically relevant SNVs (does not include mitochondrial variants).
 - `<case_id>_snv_ranked_clinical.vcf.gz.tbi`: index of the file containing clinically relevant SNVs.
 - `<case_id>_snv_ranked_research.vcf.gz`: file containing SNV annotations with their rank scores (does not include mitochondrial variants).
 - `<case_id>_snv_ranked_research.vcf.gz.tbi`: index of the file containing SNV annotations with their rank scores.
 - `<case_id>_sv_ranked_clinical.vcf.gz`: file containing clinically relevant SVs (includes mitochondrial variants).
 - `<case_id>_sv_ranked_clinical.vcf.gz.tbi`: index of the file containing clinically relevant SVs.
 - `<case_id>_sv_ranked_research.vcf.gz`: file containing SV annotations with their rank scores (includes mitochondrial variants).
 - `<case_id>_sv_ranked_resarch.vcf.gz.tbi`: index of the file containing SV annotations with their rank scores.


#### Calling mobile elements

Mobile elements are identified from the bam file using RetroSeq and the indiviual calls are merged to case VCF using SVDB.

 Output files

- `call_mobile_elements/`
 - `<case_id>_mobile_elements.vcf.gz`: file containing mobile elements.
 - `<case_id>_mobile_elements.vcf.gz.tbi`: index of the file containing mobile elements.

#### Annotating mobile elements

The mobile elements are annotated with allele frequencies and allele counts using SVDB. These annotation files needed are preferably produced from a representative population. Further annoation is done using VEP and the resulting VCF is filtered using bcftools. The default filter is to only keep elements with `PASS` in the filter column but if no other post-processing is done we reccomend supplementing with an exclude expression based on population allele frequencies. The filtering key is dependent on the annotation files used but an example expression could look like this: `--exclude 'INFO/swegen_sva_FRQ > 0.1'`. If a list of HGNC id's have been supplied with the option `--vep_filters`, variants matching those id's will be presented in a seperate file using filter_vep from VEP. This option can be disabled using the flag `--skip_subworkflows generate_clinical_set`. A VCF corresponding to the complete set of variants will also be produced.

 Output files

- `rank_and_filter/`
 - `<case_id>_mobile_elements_annotated_research.vcf.gz`: VCF containting the complete set of annotated mobile elements.
 - `<case_id>_mobile_elements_annotated_research.vcf.gz.tbi`: Index for VCF containting the complete set of annotated mobile elements.
 - `<case_id>_mobile_elements_annotated_clinical.vcf.gz`: VCF containing selected annotated mobile elements.
 - `<case_id>_mobile_elements_annotated_clincial.vcf.gz.tbi`: Index for VCF containing selected annotated mobile elements.

### Variant evaluation

Provided a truth set, SNVs can be evaluated using RTG Tools' vcfeval engine. Output files generated are listed below with a short description, but if you'd like to know more about what's in each of the files, refer to RTG Tools documentation here.

 Output files

- `rtgvcfeval/`
 - `<sample_id>_vcfeval.fn.vcf.gz`: contains variants from the baseline VCF which were not correctly called.
 - `<sample_id>_vcfeval.fn.vcf.gz.tbi`: index of the \*fn.vcf file
 - `<sample_id>_vcfeval.fp.vcf.gz`: contains variants from the calls VCF which do not agree with baseline variants.
 - `<sample_id>_vcfeval.fp.vcf.gz.tbi`: index of the \*fp.vcf file
 - `<sample_id>_vcfeval.non_snp_roc.tsv.gz`: contains ROC data derived from those variants which were not represented as
 SNPs.
 - `<sample_id>_vcfeval.phasing.txt`: containing the data on the phasing
 - `<sample_id>_vcfeval.snp_roc.tsv.gz`: contains ROC data derived from only those variants which were represented as SNPs.
 - `<sample_id>_vcfeval.summary.txt`: contains the match summary statistics printed to standard output.
 - `<sample_id>_vcfeval.tp-baseline.vcf.gz`: contains those variants from the baseline VCF which agree with variants in the
 calls VCF.
 - `<sample_id>_vcfeval.tp-baseline.vcf.gz.tbi`: index of the \*tp-baseline.vcf file
 - `<sample_id>_vcfeval.tp.vcf.gz`: contains those variants from the calls VCF which agree with variants in the baseline VCF
 - `<sample_id>_vcfeval.tp.vcf.gz.tbi`: index of the \*tp.vcf file
 - `<sample_id>_vcfeval.weighted_roc.tsv.gz`: contains ROC data derived from all analyzed call variants, regardless of their
 representation.

### Gens

The sequencing data can be prepared for visualization of CNVs in Gens. You can turn it off by supplying the option `--skip_tools gens`. You can read more about how to setup Gens here.

 Output files

- `gens/`
 - `<sample_id>_gens.baf.bed.gz`: contains sample b-allele frequencies in bed format.
 - `<sample_id>_gens.baf.bed.gz.tbi`: index of the \*baf.bed.gz file.
 - `<sample_id>_gens.cov.bed.gz`: contains sample coverage in bed format.
 - `<sample_id>_gens.cov.bed.gz.tbi`: index of the \*cov.bed.gz file.

### Peddy

Peddy compares familial-relationships and sexes as reported in a PED file with those inferred from a VCF.

 Output files

- `peddy/`
 - `*.het_check.csv`: CSV file containing heterozygosity check results — rate of het calls, allele-balance at het calls, mean and median depth, and a PCA projection onto 1000 Genomes.
 - `*.het_check.png`: PNG plot of heterozygosity check results — rate of het calls, allele-balance at het calls, mean and median depth, and a PCA projection onto 1000 Genomes.
 - `*.html`: interactive HTML report with plots for sex check (HET rate on chrX), depth and heterozygosity, and pedigree relatedness, plus an interactive pedigree table.
 - `*.ped_check.csv`: CSV file containing pedigree check results — pairwise relatedness statistics comparing reported vs. inferred relationships.
 - `*.ped_check.png`: PNG plot of pedigree check results — comparison between reported and inferred relatedness.
 - `*.ped_check.rel-difference.csv`: CSV file with the comparison between inferred and reported relatedness for sample pairs where they differ.
 - `*.peddy.ped`: extended PED file augmented with key columns from the het-check and sex-check results.
 - `*.sex_check.csv`: CSV file with sex check results — comparison between the sex reported in the PED file and that inferred from genotypes on the non-PAR regions of the X chromosome.
 - `*.sex_check.png`: PNG plot of sex check results — comparison between reported and inferred sex.
 - `*.vs.html`: interactive scatter plot of observed vs. expected (pedigree-reported) relatedness for all sample pairs.

### Pipeline information

Nextflow provides excellent functionality for generating various reports relevant to the running and execution of the pipeline. This will allow you to troubleshoot errors with the running of the pipeline, and also provide you with other information such as launch commands, run times and resource usage.

 Output files

- `pipeline_info/`
 - Reports generated by Nextflow: `execution_report.html`, `execution_timeline.html`, `execution_trace.txt` and `pipeline_dag.dot`/`pipeline_dag.svg`.
 - Reports generated by the pipeline: `pipeline_report.html`, `pipeline_report.txt` and `software_versions.yml`. The `pipeline_report*` files will only be present if the `--email` / `--email_on_fail` parameter's are used when running the pipeline.
 - Reformatted samplesheet files used as input to the pipeline: `samplesheet.valid.csv`.
 - Parameters used by the pipeline run: `params.json`.
