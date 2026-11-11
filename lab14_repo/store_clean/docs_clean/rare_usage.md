# nf-core/raredisease: Usage

**We recommend reading this documentation on the nf-core website: https://nf-co.re/raredisease/usage**

Table of contents:

- nf-core/raredisease: Usage
 - Introduction
 - Prerequisites
 - Run nf-core/raredisease with test data
 - Updating the pipeline
 - Run nf-core/raredisease with your data
 - Samplesheet
 - Samplesheet for BAM file input
 - Reference files and parameters
 - 1. Alignment
 - 2. QC stats from the alignment files
 - 3. Repeat expansions
 - 4. Variant calling - SNV
 - 5. Variant calling - Structural variants
 - 6. Copy number variant calling
 - 7. SNV annotation \& Ranking
 - 8. SV annotation \& Ranking
 - 9. Mitochondrial annotation
 - 10. Mobile element calling
 - 11. Mobile element annotation
 - 12. Variant evaluation
 - 13. Prepare data for CNV visualisation in Gens
 - Run the pipeline
 - Direct input in CLI
 - Import from a config file (recommended)
 - Best practices
 - Core Nextflow arguments
 - `-profile`
 - `-resume`
 - `-c`
 - Custom configuration
 - Resource requests
 - Custom Containers
 - Custom Tool Arguments
 - nf-core/configs
 - Run Sentieon
 - Running in the background
 - Nextflow memory requirements
 - Running the pipeline without Internet access

## Introduction

nf-core/raredisease is a bioinformatics best-practice analysis pipeline to call, annotate and score variants from WGS/WES of rare disease patients. The pipeline is built using Nextflow.

## Prerequisites

1. Install Nextflow (>=25.10.4) using the instructions here.
2. Install one of the following technologies for full pipeline reproducibility: Docker, Singularity, Podman, Shifter or Charliecloud.
 > Almost all nf-core pipelines give you the option to use conda as well. However, some tools used in the raredisease pipeline do not have a conda package so we do not support conda at the moment.

## Run nf-core/raredisease with test data

Before running the pipeline with your data, we recommend running it with the test dataset available here. You do not need to download the data as the pipeline is configured to fetch that data automatically for you when you use the test profile.

Run the following command, where YOURPROFILE is the package manager you installed on your machine. For example, `-profile test,docker` or `-profile test,singularity`:

```
nextflow run nf-core/raredisease \
 -revision dev -profile test,<YOURPROFILE> \
 --outdir <OUTDIR>
```

Check nf-core/configs to see if a custom config file to run nf-core pipelines already exists for your institute. If so, you can simply use `-profile test,<institute>` in your command. This enables the appropriate package manager and sets the appropriate execution settings for your machine.
NB: The order of profiles is important! They are loaded in sequence, so later profiles can overwrite earlier profiles.

Running the command creates the following files in your working directory:

```
work # Directory containing the Nextflow working files
<OUTDIR> # Finished results in specified location (defined with --outdir)
.nextflow_log # Log file from Nextflow
# Other Nextflow hidden files, like history of pipeline logs.
```

Test profile runs the pipeline with a case containing three samples, but if you would like to test the pipeline with one sample, use `-profile test_singleton,<YOURPROFILE>`.

:::note
The default cpu and memory configurations used in raredisease are written keeping the test profile (&dataset, which is tiny) in mind. You should override these values in configs to get it to work on larger datasets. Check the section `custom-configuration` below to know more about how to configure resources for your platform.
:::

### Updating the pipeline

The above command downloads the pipeline from GitHub, caches it, and tests it on the test dataset. When you run the command again, it will fetch the pipeline from cache even if a more recent version of the pipeline is available. To make sure that you're running the latest version of the pipeline, update the cached version of the pipeline by including `-latest` in the command.

## Run nf-core/raredisease with your data

Running the pipeline involves three steps:

1. Prepare a samplesheet
2. Gather all required references
3. Supply samplesheet and references, and run the command

#### Samplesheet

A samplesheet is used to provide information about the sample(s) to the pipeline in CSV format, including the path to the FASTQ files and other metadata such as sex and phenotype.

The nf-core/raredisease pipeline accepts FASTQ files, SPRING files, or BAM files as input. Currently, the pipeline does not support single-end data from Illumina. The pedigree information in the samplesheet (sex and phenotype) should be provided in the same format as a PED file, with sex indicated as 1 for male, 2 for female, and other for unknown.

| Fields | Description |

| `sample` | Custom sample name. This entry will be identical for multiple sequencing libraries/runs from the same sample. |
| `lane` | Used to generate separate channels during the alignment step. It is of string type, and we recommend using a combination of flowcell and lane to distinguish between different runs of the same sample. |
| `fastq_1` | Absolute path to FASTQ file for Illumina short reads 1. File has to be gzipped and have the extension ".fastq.gz" or ".fq.gz". |
| `fastq_2` | Absolute path to FASTQ file for Illumina short reads 2. File has to be gzipped and have the extension ".fastq.gz" or ".fq.gz". |
| `spring_1` | Full path to spring-compressed file for read 1 or for reads 1 and 2. The Fastq file has to be first gzipped, then spring-compressed, and it must have the extension `.spring`. |
| `spring_2` | Full path to spring-compressed file for read 2. The Fastq file has to be first gzipped, then spring-compressed, and it must have the extension `.spring`. |
| `bam` | Full path to a bam file containing alignments. |
| `bai` | Full path to a bam index file. |
| `sex` | Sex (1=male; 2=female; for unknown sex use 0 or 'other'). |
| `phenotype` | Affected status of patient (0 = missing; 1=unaffected; 2=affected). |
| `paternal_id` | Sample ID of the father, can be blank if the father isn't part of the analysis or for samples other than the proband. |
| `maternal_id` | Sample ID of the mother, can be blank if the mother isn't part of the analysis or for samples other than the proband. |
| `case_id` | Case ID, for the analysis used when generating a family VCF. |

It is also possible to include multiple runs of the same sample in a samplesheet. For example, when you have re-sequenced the same sample more than once to increase sequencing depth. In that case, the `sample` identifiers in the samplesheet have to be the same. The pipeline will align the raw read/read-pairs independently before merging the alignments belonging to the same sample. Below is an example for a trio with the proband sequenced across two lanes:

| sample | lane | fastq_1 | fastq_2 | sex | phenotype | paternal_id | maternal_id | case_id |

| AEG588A1 | 2 | AEG588A1_S1_L002_R1_001.fastq.gz | AEG588A1_S1_L002_R2_001.fastq.gz | 1 | 2 | AEG588A3 | AEG588A2 | fam_1 |
| AEG588A1 | 3 | AEG588A1_S1_L003_R1_001.fastq.gz | AEG588A1_S1_L003_R2_001.fastq.gz | 1 | 2 | AEG588A3 | AEG588A2 | fam_1 |
| AEG588A2 | 4 | AEG588A2_S1_L004_R1_001.fastq.gz | AEG588A2_S1_L004_R2_001.fastq.gz | 2 | 1 | | | fam_1 |
| AEG588A3 | 4 | AEG588A3_S1_L004_R1_001.fastq.gz | AEG588A3_S1_L004_R2_001.fastq.gz | 1 | 1 | | | fam_1 |

If you would like to see more examples of what a typical samplesheet looks like for a singleton and a trio, follow these links, singleton and trio.

##### Samplesheet for BAM file input

The nf-core/raredisease pipeline can handle duplicate-marked BAM files as input. In such cases, samplesheet should contain the following columns:

| Fields | Description |

| `sample` | Custom sample name. This entry will be identical for multiple sequencing libraries/runs from the same sample. |
| `bam` | Absolute path to a duplicate-marked BAM file. |
| `bai` | Absolute path to the BAM index file (.bai). |
| `sex` | Sex (1=male; 2=female; for unknown sex use 0 or 'other'). |
| `phenotype` | Affected status of patient (0 = missing; 1=unaffected; 2=affected). |
| `paternal_id` | Sample ID of the father, can be blank if the father isn't part of the analysis or for samples other than the proband. |
| `maternal_id` | Sample ID of the mother, can be blank if the mother isn't part of the analysis or for samples other than the proband. |
| `case_id` | Case ID, for the analysis used when generating a family VCF. |

If you would like to see an example of what a typical samplesheet looks like in this case, follow this link.

#### Reference files and parameters

In nf-core/raredisease, references can be supplied using parameters listed here.
WARNING:
Do not use `-c <file>` to specify parameters as this will result in errors. Custom config files specified with `-c` must only be used for tuning process resource specifications, other infrastructural tweaks (such as output directories), or module arguments (args).

The above pipeline run specified with a params file in yaml format:

```bash
nextflow run nf-core/raredisease -profile docker -params-file params.yaml
```

with:

```yaml title="params.yaml"
input: "./samplesheet.csv"
outdir: "./results/"
genome: "GRCh37"
```

Note that the pipeline is modular in architecture. It offers you the flexibility to choose between different tools. For example, you can align with bwamem2 or bwa or Sentieon BWA mem and call SNVs with either DeepVariant or Sentieon DNAscope. You also have the option to turn off sections of the pipeline if you do not want to run the. For example, snv annotation can be turned off by adding `--skip_subworkflows snv_annotation` flag in the command line, or by setting it to true in a parameter file. This flexibility means that in any given analysis run, a combination of tools included in the pipeline will not be executed. So the pipeline is written in a way that can account for these differences while working with reference parameters. If a tool is not going to be executed during the course of a run, parameters used only by that tool need not be provided. For example, for SNV calling if you use DeepVariant as your variant caller, you need not provide the parameter `--ml_model`, which is only used by Sentieon DNAscope.

The pipeline is modular — individual tools and subworkflows can be skipped using `--skip_tools` and `--skip_subworkflows` (comma-separated). The valid values are:

| `--skip_tools` |

| `fastp`, `fastqc`, `gens`, `germlinecnvcaller`, `ngsbits`, `peddy`, `smncopynumbercaller`, `vcf2cytosure` |

| `--skip_subworkflows` |

| `generate_clinical_set`, `me_annotation`, `me_calling`, `mt_annotation`, `mt_subsample`, `repeat_annotation`, `repeat_calling`, `snv_annotation`, `snv_calling`, `sv_annotation`, `sv_calling` |

nf-core/raredisease consists of several tools used for various purposes. For convenience, we have grouped those tools under the following categories:

1. Alignment (bwamem2/bwa/bwameme/Sentieon BWA mem)
2. QC stats from the alignment files
3. Repeat expansions (ExpansionsHunter & Stranger)
4. Variant calling - SNV (DeepVariant/Sentieon DNAscope)
5. Variant calling - Structural variants (SV) (Tiddit & Manta)
6. Copy number variant calling (GATK's GermlineCNVCaller)
7. SNV annotation & ranking (rohcall, vcfanno, ensembl VEP, GENMOD)
8. SV annotation & ranking (SVDB query, ensembl VEP, GENMOD)
9. Mitochondrial annotation

We have only listed the groups that require at least one input from the user. For example, the pipeline also runs SMNCopyNumberCaller, but it does not require any input other than the bam files passed by the pipeline. Hence, it is not mentioned in the list above. To know more about the tools used in the pipeline check the README.

The mandatory and optional parameters for each category are tabulated below.

Alignment, QC stats, repeat expansions, SNV & SV variant calling are run by default. Hence, the mandatory parameters used by those features will always have to be provided to the pipeline.

##### 1. Alignment

| Mandatory | Optional |

| aligner 1 | fasta_fai 4 |
| fasta 2 | bwamem2 4 |
| platform | bwa 4 |
| mito_name/mt_fasta 3 | bwameme 4 |
| | known_dbsnp 5 |
| | known_dbsnp_tbi 5 |
| | min_trimmed_length 6 |
| | extract_alignments |
| | restrict_to_contigs 7 |
| | exclude_alt 8 |

 1 Default value is bwamem2. Other alternatives are bwa, bwameme and sentieon (requires valid Sentieon license ).
 2 Analysis set reference genome in fasta format, first 25 contigs need to be chromosome 1-22, X, Y and the mitochondria.
 3 If mito_name is provided, mt_fasta can be generated by the pipeline.
 4 fasta_fai, bwa, bwamem2 and bwameme, if not provided by the user, will be generated by the pipeline when necessary.
 5 Used only by Sentieon.
 6 Default value is 40. Used only by fastp.
 7 Used to limit your analysis to specific contigs. Can be used to remove alignments to unplaced contigs to minimize potential errors. This parameter should be used in conjunction with the `extract_alignments` parameter.
 8 When set to true, alignments to alt/unplaced contigs are removed after alignment using samtools view, retaining only primary chromosomes (GRCh37: 1-22,X,Y,MT / GRCh38: chr1-chr22,chrX,chrY,chrM). Note that this will affect all downstream variant calling, as variants will only be called on these primary chromosomes.

##### 2. QC stats from the alignment files

| Mandatory | Optional |

| intervals_wgs 1 | |
| intervals_y 1 | |
| target_bed / (bait_intervals & target_intervals) 2 | |
| | verifybamid_svd_bed 3 |
| | verifybamid_svd_mu 3 |
| | verifybamid_svd_ud 3 |

 1 These files are Picard's style interval list files, comprising the entire genome or only the chromosome Y. A version of these files for GRCh37 and for GRCh38 is supplied in the pipeline assets. These files are not necessary if you are using Sentieon.
 2 If a target_bed file is provided, bait_intervals and target_intervals can be generated by the pipeline.
 3 Used by VerifyBamID2 to check for contamination. These files can either be downloaded from VerifyBamID2 repository or created using VerifyBamID2 with custom files as described here.

##### 3. Repeat expansions

| Mandatory | Optional |

| variant_catalog 1 | |

 1 We reccomend using the catalogs found here. These catalogs have been extended from the illumina ones to include information on pathogenicity, which is neccesarry for the workflow.

##### 4. Variant calling - SNV

| Mandatory | Optional |

| variant_caller 1 | known_dbsnp 2 |
| ml_model 2 | known_dbsnp_tbi 2 |
| analysis_type 3 | call_interval 2 |
| | known_dbsnp_tbi 2 |
| | par_bed 4 |
| | skip_split_multiallelics 5 |

 1 Default variant caller is DeepVariant, but you have the option to use Sentieon as well.
 2 These parameters are only used by Sentieon.
 3 Default is `WGS`, but you have the option to choose `WES` and `mito` as well.
 4 This parameter is only used by Deepvariant.
 5 Skips `bcftools norm --multiallelics -both` in both DeepVariant and Sentieon SNV calling. Recommended for single-interval runs to avoid indel quality degradation. See #813 for details.

##### 5. Variant calling - Structural variants

| Mandatory | Optional |

| | target_bed |
| | bwa |
| | manta_call_regions 1 |
| | manta_call_regions_tbi 1 |

 1 A bgzipped BED file (`.bed.gz`) and its tabix index (`.bed.gz.tbi`) restricting Manta's SV calling to specific regions. Both parameters must be supplied together. Only applied for WGS; for WES, Manta always uses `target_bed` and these parameters have no effect. Useful for reducing runtime on references with many short contigs such as GRCh38 by limiting analysis to primary chromosomes.

##### 6. Copy number variant calling

| Mandatory | Optional |

| ploidy_model 1,4 | |
| gcnvcaller_model 1,2,4 | |
| readcount_intervals 3,4 | |

 1 Output from steps 3 & 4 of GATK's CNV calling pipeline run in cohort mode as described here.
 2 Sample file can be found here (Note the header 'models' in the sample file).
 3 Output from step 1 of GATK's CNV calling pipeline as described here.
 4 All these files can be generated using the germlinecnvcaller tool option in nf-core/createpanelrefs.

##### 7. SNV annotation & Ranking

| Mandatory | Optional |

| genome 1 | reduced_penetrance 9 |
| vcfanno_resources 2 | vcfanno_lua |
| vcfanno_toml 3 | vep_filters/vep_filters_scout_fmt 10 |
| vep_cache_version | cadd_resources 11 |
| vep_cache 4 | run_vcfanno_db_sanity_check 12 |
| gnomad_af 5 | |
| score_config_snv 6 | |
| variant_consequences_snv 7 | |
| vep_plugin_files 8 | |

 1 Genome version is used by VEP. You have the option to choose between GRCh37 and GRCh38.
 2 Path to VCF files and their indices used by vcfanno. Sample file here.
 3 Path to a vcfanno configuration file. Sample file here.
 4 VEP caches can be downloaded here.
VEP plugins may be installed in the cache directory, and the plugin pLI is mandatory to install. To supply files required by VEP plugins, use `vep_plugin_files` parameter.
See example cache here.
 5 GnomAD VCF files can be downloaded from here. The option `gnomad_af` expects a tab-delimited file with
no header and the following columns: `CHROM POS REF_ALLELE,ALT_ALLELE AF`. Sample file here.
 6 Used by GENMOD for ranking the variants. Sample file here.
 7 File containing list of SO terms listed in the order of severity from most severe to lease severe for annotating genomic and mitochondrial SNVs. Sample file here. You can learn more about these terms here.
 8 A CSV file that describes the files used by VEP's named and custom plugins. Sample file here.
 9 Used by GENMOD while modeling the variants. Contains a list of loci that show reduced penetrance in people. Sample file here.
 10 This file contains a list of candidate genes (with HGNC IDs) that is used to split the variants into candidate variants and research variants. Research variants contain all the variants, while candidate variants are a subset of research variants and are associated with candidate genes. Sample file here. Not required if `--skip_subworkflows generate_clinical_set` is set.
 11 Path to a folder containing cadd annotations. Equivalent of the data/annotations/ folder described here, and it is used to calculate CADD scores for small indels.
 12 When set to `true`, each vcfanno database file listed in `vcfanno_resources` is checked for records (non-header lines). Any database with zero records is removed from the vcfanno TOML config before annotation runs to prevent vcfanno from crashing on default resource files. Default: `false`.

:::note
We use CADD only to annotate small indels. To annotate SNVs with precomputed CADD scores, pass the file containing CADD scores as a resource to vcfanno instead. Files containing the precomputed CADD scores for SNVs can be downloaded from here (download files listed under the description: "All possible SNVs of GRCh3<7/8>/hg3<7/8>")
:::

##### 8. SV annotation & Ranking

| Mandatory | Optional |

| genome | reduced_penetrance |
| svdb_query_dbs/svdb_query_bedpedbs 1 | |
| vep_cache_version | vep_filters/vep_filters_scout_fmt |
| vep_cache | vep_plugin_files |
| score_config_sv | |
| variant_consequences_sv 2 | |

 1 A CSV file that describes the databases (VCFs or BEDPEs) used by SVDB for annotating structural variants. Sample file here. Information about the column headers can be found here.
 2 File containing list of SO terms listed in the order of severity from most severe to lease severe for annotating genomic SVs. Sample file here. You can learn more about these terms here.

##### 9. Mitochondrial annotation

Mitochondrial analysis runs automatically for `wgs` and `mito` analysis types. For WES runs, set `--run_mt_for_wes true` to enable it.

| Mandatory | Optional |

| genome | run_mt_for_wes 1 |
| mito_name | vep_filters/vep_filters_scout_fmt |
| vcfanno_resources | vep_plugin_files |
| vcfanno_toml | |
| vep_cache_version | |
| vep_cache | |
| score_config_mt | |
| variant_consequences_snv | |

 1 Set to `true` to enable mitochondrial analysis for WES runs. Default is `false`.

##### 10. Mobile element calling

| Mandatory | Optional |

| genome | |
| mobile_element_references 1 | |

 1 A TSV file that describes the references (BEDs) used by RetroSeq for calling mobile elements. Sample file here

##### 11. Mobile element annotation

| Mandatory | Optional |

| genome | vep_filters/vep_filters_scout_fmt |
| mobile_element_svdb_annotations 1 | |
| vep_cache_version | |
| vep_cache | |
| variant_consequences_sv | |

 1 A CSV file that describes the databases (VCFs) used by SVDB for annotating mobile elements with allele frequencies. Sample file here.

##### 12. Variant evaluation

| Mandatory | Optional |

| run_rtgvcfeval 1 | sdf |
| rtg_truthvcfs 2 | |

 1 This parameter is set to false by default, set it to true if if you'd like to run the evaluation subworkflow
 2 A CSV file that describes the truth VCF files used by RTG Tools' vcfeval for evaluating SNVs. Sample file here. The file contains four columns `samplename,vcf,bedregions,evaluationregions` where samplename is the user assigned samplename in the input samplesheet, vcf is the path to the truth vcf file, bedregions and evaluationregions are the path to the bed files that are supposed to be passed through --bed_regions and --evaluation_regions options of vcfeval.

##### 13. Prepare data for CNV visualisation in Gens

Optionally the read data can be prepared for CNV visualization in Gens. You can turn it off it by supplying the option `--skip_tools gens`.

| Mandatory | Optional |

| gens_pon_female 1 | |
| gens_pon_male 1 | |
| gens_interval_list 2 | |
| gens_gnomad_pos 3 | |

 1 Instructions on how to generate the panel of normals can be found here
 2 Interval list for CollectReadCounts. Instructions on how to generate the interval list file can be found here
 3 File containing SNVs to be used for the B-allele frequency calculations. The developers of gens uses SNVs in gnomad with an allele frecuency above 5%.

#### Run the pipeline

You can directly supply the parameters in the command line (CLI) or use a config file from which the pipeline can import the parameters.

##### Direct input in CLI

All of the pipeline parameters listed here can be passed using the CLI. For example, you can provide the samplesheet, reference FASTA, and turn off annotations for SNVs and SVs by running,

```
nextflow run nf-core/raredisease \
 -revision dev \
 -profile test,<YOURPROFILE> \
 --input samplesheet.csv \
 --fasta reference.fasta \
 --skip_subworkflows "snv_annotation,sv_annotation" \
 --outdir <OUTDIR>
```

##### Import from a config file (recommended)

To input or change the default parameters, we recommend using a config file instead. Create a config file that contains all the parameters and supply that file as shown below.

```
nextflow run nf-core/raredisease \
 -revision dev \
 -profile test,<YOURPROFILE> \
 -c <YOURCONFIG> \
 --outdir <OUTDIR>
```

A sample config file can be found here.

## Best practices

- **Singularity cache:** If you are using singularity, use the nf-core download command to download images first, before running the pipeline. Define NXF_SINGULARITY_CACHEDIR or singularity.cacheDir Nextflow options to store and re-use the images from a central location for future pipeline runs.

- **Save references:** While the pipeline can generate indices for the FASTA and some VCF files when they are not provided, it can be benficial to supply them to the pipeline as it saves computing resources. You can use the `--save_reference` parameter to publish those files, and then update your config file with the paths to these files for your subsequent runs.

- **Update pipeline:** If you would like to update the pipeline code stored in cache, in addition to running the command with `-latest` option, you can also run the command below:

```bash
nextflow pull nf-core/raredisease
```

- **Reproducibility:** Specify a pipeline version when running the pipeline on your data. This ensures that a specific version of the pipeline code and software are used when you run your pipeline. If you keep using the same tag, you'll be running the same version of the pipeline, even if there have been changes to the code since. First, go to the nf-core/raredisease releases page and find the latest pipeline version - numeric only (e.g. `1.3.1`). Then specify this when running the pipeline with `-r`, for example, `-r 1.3.1`. You can switch to another version by changing the number after the `-r` flag. The version number will be logged in reports when you run the pipeline. For example, you can view the version number at the bottom of the MultiQC reports.

To further assist in reproducibility, you can use share and reuse parameter files to repeat pipeline runs with the same settings without having to write out a command with every single parameter.
TIP:
If you wish to share such profile (such as upload as supplementary material for academic publications), make sure to NOT include cluster specific paths to files, nor institutional specific profiles.

- **Restart a previous run:** Add `-resume` to your command when restarting a pipeline. Nextflow will use cached results from any pipeline steps where inputs are the same, and resume the run from where it terminated previously. For input to be considered the same, names and the files' contents must be identical. For more info about `-resume`, see this blog post. You can also supply a run name to resume a specific run: `-resume [run-name]`. Use the `nextflow log` command to show previous run names.

- **Reusing parameters:** If you wish to repeatedly use the same parameters for multiple runs, rather than specifying each flag in the command, you can specify these in a params file.

Pipeline settings can be provided in a `yaml` or `json` file via `-params-file <file>`.

⚠️ Do not use `-c <file>` to specify parameters as this will result in errors. Custom config files specified with `-c` must only be used for tuning process resource specifications, other infrastructural tweaks (such as output directories), or module arguments (args).
The above pipeline run specified with a params file in yaml format:

```bash
nextflow run nf-core/raredisease -profile docker -params-file params.yaml
```

with:

```yaml title="params.yaml"
input: './samplesheet.csv'
outdir: './results/'
genome: 'GRCh37'
<...>
```

You can also generate such `YAML`/`JSON` files via nf-core/launch.

## Core Nextflow arguments
NOTE:
These options are part of Nextflow and use a _single_ hyphen (pipeline parameters use a double-hyphen)

### `-profile`

Use this parameter to choose a configuration profile. Profiles can give configuration presets for different compute environments.

Several generic profiles are bundled with the pipeline which instruct the pipeline to use software packaged using different methods (Docker, Singularity, Podman, Shifter, Charliecloud, Apptainer, Conda) - see below.
IMPORTANT:
We highly recommend the use of Docker or Singularity containers for full pipeline reproducibility, however when this is not possible, Conda is also supported.

The pipeline also dynamically loads configurations from https://github.com/nf-core/configs when it runs, making multiple config profiles for various institutional clusters available at run time. For more information and to check if your system is supported, please see the nf-core/configs documentation.

Note that multiple profiles can be loaded, for example: `-profile test,docker` - the order of arguments is important!
They are loaded in sequence, so later profiles can overwrite earlier profiles.

If `-profile` is not specified, the pipeline will run locally and expect all software to be installed and available on the `PATH`. This is _not_ recommended, since it can lead to different results on different machines dependent on the computer environment.

- `test`
 - A profile with a complete configuration for automated testing
 - Includes links to test data so needs no other parameters
- `docker`
 - A generic configuration profile to be used with Docker
- `singularity`
 - A generic configuration profile to be used with Singularity
- `podman`
 - A generic configuration profile to be used with Podman
- `shifter`
 - A generic configuration profile to be used with Shifter
- `charliecloud`
 - A generic configuration profile to be used with Charliecloud
- `apptainer`
 - A generic configuration profile to be used with Apptainer
- `wave`
 - A generic configuration profile to enable Wave containers. Use together with one of the above (requires Nextflow ` 24.03.0-edge` or later).
- `conda`
 - A generic configuration profile to be used with Conda. Please only use Conda as a last resort i.e. when it's not possible to run the pipeline with Docker, Singularity, Podman, Shifter, Charliecloud, or Apptainer.

### `-resume`

Specify this when restarting a pipeline. Nextflow will use cached results from any pipeline steps where the inputs are the same, continuing from where it got to previously. For input to be considered the same, not only the names must be identical but the files' contents as well. For more info about this parameter, see this blog post.

You can also supply a run name to resume a specific run: `-resume [run-name]`. Use the `nextflow log` command to show previous run names.

### `-c`

Specify the path to a specific config file (this is a core Nextflow command). See the nf-core website documentation for more information.


### Resource requests

Whilst the default requirements set within the pipeline will hopefully work for most people and with most input data, you may find that you want to customise the compute resources that the pipeline requests. Each step in the pipeline has a default set of requirements for number of CPUs, memory and time. For most of the pipeline steps, if the job exits with any of the error codes specified here it will automatically be resubmitted with higher resources request (2 x original, then 3 x original). If it still fails after the third attempt then the pipeline execution is stopped.

To change the resource requests, please see the max resources and tuning workflow resources section of the nf-core website.

### Custom Containers

In some cases, you may wish to change the container or conda environment used by a pipeline steps for a particular tool. By default, nf-core pipelines use containers and software from the biocontainers or bioconda projects. However, in some cases the pipeline specified version maybe out of date.

To use a different container from the default container or conda environment specified in a pipeline, please see the updating tool versions section of the nf-core website.

### Custom Tool Arguments

A pipeline might not always support every possible argument or option of a particular tool used in pipeline. Fortunately, nf-core pipelines provide some freedom to users to insert additional parameters that the pipeline does not include by default.

To learn how to provide additional arguments to a particular tool of the pipeline, please see the customising tool arguments section of the nf-core website.

#### nf-core/configs

In most cases, you will only need to create a custom config as a one-off but if you and others within your organisation are likely to be running nf-core pipelines regularly and need to use the same settings regularly it may be a good idea to request that your custom config file is uploaded to the `nf-core/configs` git repository. Before you do this test that the config file works with your pipeline of choice using the `-c` parameter. You can then create a pull request to the `nf-core/configs` repository with the addition of your config file, associated documentation file (see examples in `nf-core/configs/docs`), and amending `nfcore_custom.config` to include your custom profile.

See the main Nextflow documentation for more information about creating your own configuration files.

If you have any questions or issues please send us a message on Slack on the `#configs` channel.

### Run Sentieon

To use Sentieon you have to:

1. Ensure that Sentieon executable is in path.
2. If necessary, store license information as a secret in Nextflow's local store.
3. Set environmental variable `NXF_ENABLE_SECRETS` to an appropriate value.

To elaborate more on item #2 in the list above, if you are running nf-core/raredisease with Sentieon on AWS or on a local machine and you do not want other users to know your license details, we recommend that you use Nextflow's secrets feature to pass the that information. To do that run the command below after replacing LICENSE with the value corresponding to your license server (for example, 1.1.1.1:4000)

```
nextflow secrets set SENTIEON_LICENSE_BASE64 <LICENSE>
```

If you are using Nextflow secrets, you have to set the environment variable `NXF_ENABLE_SECRETS` to true. This will see to it that the pipeline can retrieve the secret from Nextflow's secrets store during the pipeline execution. Keep in mind that versions of Nextflow Version 22.09.2-edge and onwards have NXF_ENABLE_SECRETS to true by default. If you are not using secrets set `NXF_ENABLE_SECRETS` to false, but make sure that the environment variable `SENTIEON_LICENSE` is set to reflect the value of your license server on your machine.

### Running in the background

Nextflow handles job submissions and supervises the running jobs. The Nextflow process must run until the pipeline is finished.

The Nextflow `-bg` flag launches Nextflow in the background, detached from your terminal so that the workflow does not stop if you log out of your session. The logs are saved to a file.

Alternatively, you can use `screen` / `tmux` or similar tool to create a detached session which you can log back into at a later time.
Some HPC setups also allow you to run Nextflow within a cluster job submitted to your job scheduler (from where it submits more jobs).

### Nextflow memory requirements

In some cases, the Nextflow Java virtual machines can start to request a large amount of memory.
We recommend adding the following line to your environment to limit this (typically in `~/.bashrc` or `~./bash_profile`):

```bash
NXF_OPTS='-Xms1g -Xmx4g'
```

### Running the pipeline without Internet access

The pipeline and container images can be downloaded using nf-core tools. For running offline, you of course have to make all the reference data available locally, and specify `--fasta`, etc., see above.

Contrary to the paragraph about Nextflow on the page linked above, it is not possible to use the "-all" packaged version of Nextflow for this pipeline. The online version of Nextflow is necessary to support the necessary nextflow plugins. Download instead the file called just `nextflow`. Nextflow will download its dependencies when it is run. Additionally, you need to download the nf-schema plugin explicitly:

```
./nextflow plugin install nf-schema
```

Now you can transfer the `nextflow` binary as well as its directory `$HOME/.nextflow` to the system without Internet access, and use it there. It is necessary to use an explicit version of `nf-schema` offline, or Nextflow will check for the most recent version online. Find the version of nf-schema you downloaded in `$HOME/.nextflow/plugins`, then specify this version for `nf-schema` in your configuration file:

```
plugins {
 // Set the plugin version explicitly, otherwise nextflow will look for the newest version online.
 id 'nf-schema@2.1.1'
}
```

This should go in your Nextflow configuration file, specified with `-c <YOURCONFIG>` when running the pipeline.
