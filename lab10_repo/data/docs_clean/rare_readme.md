## Introduction

**nf-core/raredisease** is a best-practice bioinformatic pipeline for calling and scoring variants from WGS/WES data from rare disease patients. This pipeline is heavily inspired by MIP.
NOTE:
Right now, we only support paired-end data from Illumina. If you've got other types of data and the pipeline doesn't work for you, just open an issue. We'd be happy to chat about a solution.

The pipeline is built using Nextflow, a workflow tool to run tasks across multiple compute infrastructures in a very portable manner. It uses Docker/Singularity containers making installation trivial and results highly reproducible. The Nextflow DSL2 implementation of this pipeline uses one container per process which makes it much easier to maintain and update software dependencies. Where possible, these processes have been submitted to and installed from nf-core/modules in order to make them available to all nf-core pipelines, and to everyone within the Nextflow community!

On release, automated continuous integration tests run the pipeline on a full-sized dataset on the AWS cloud infrastructure. This ensures that the pipeline runs on AWS, has sensible resource allocation defaults set to run on real-world datasets, and permits the persistent storage of results to benchmark between pipeline releases and other analysis sources. The results obtained from the full-sized test can be viewed on the nf-core website.

## Pipeline summary

**1. Preprocessing:**

- fastp
- Spring

**2. Alignment:**

- Bwa-mem2
- BWA-MEME
- BWA
- Sentieon DNAseq

**3. Metrics:**

- FastQC
- Mosdepth
- MultiQC
- Picard's CollectMultipleMetrics, CollectHsMetrics, and CollectWgsMetrics
- Sambamba
- Sentieon's WgsMetricsAlgo
- TIDDIT's cov
- VerifyBamID2

**4. Sex check:**

- NGSbits SampleGender
- Peddy

**5. Variant calling - SNV:**

- DeepVariant
- Sentieon DNAscope

**6. Variant calling - SV:**

- Manta
- TIDDIT's sv
- Copy number variant calling:
 - CNVnator
 - GATK GermlineCNVCaller
 - SMNCopyNumberCaller
- Mitochondrial SV calling:
 - MitoSAlt
 - Saltshaker

**7. Annotation - SNV:**

- bcftools roh
- vcfanno
- CADD
- VEP
- UPD
- Chromograph

**8. Annotation - SV:**

- SVDB query
- VEP

**9. Mitochondrial analysis:**

- Alignment and variant calling - GATK Mitochondrial short variant discovery pipeline
- Annotation:
 - vcfanno
 - CADD
 - VEP

**10. Variant calling - repeat expansions:**

- Expansion Hunter
- Stranger

**11. Variant calling - mobile elements:**

- RetroSeq

**12. Rank variants - SV and SNV:**

- GENMOD

**13. Variant evaluation:**

- RTG Tools

Note that it is possible to include/exclude certain tools or steps.

## Usage
NOTE:
If you are new to Nextflow and nf-core, please refer to this page on how to set-up Nextflow. Make sure to test your setup with `-profile test` before running the workflow on actual data.

First, prepare a samplesheet with your input data that looks as follows:

`samplesheet.csv`:

```csv
sample,lane,fastq_1,fastq_2,sex,phenotype,paternal_id,maternal_id,case_id
hugelymodelbat,1,reads_1.fastq.gz,reads_2.fastq.gz,1,2,,,justhusky
```

Each row represents a pair of fastq files (paired end).

Second, ensure that you have defined the path to reference files and parameters required for the type of analysis that you want to perform. More information about this can be found here.

Now, you can run the pipeline using:

```bash
nextflow run nf-core/raredisease \
 -profile <docker/singularity/podman/shifter/charliecloud/conda/institute> \
 --input samplesheet.csv \
 --outdir <OUTDIR>
```
WARNING:
Please provide pipeline parameters via the CLI or Nextflow `-params-file` option. Custom config files including those provided by the `-c` Nextflow option can be used to provide any configuration _**except for parameters**_; see docs.

For more details and further functionality, please refer to the usage documentation and the parameter documentation.

## Pipeline output

For more details about the output files and reports, please refer to the
output documentation.

## Credits

nf-core/raredisease was written in a collaboration between the Clinical Genomics nodes in Sweden, with major contributions from Ramprasad Neethiraj, Anders Jemt, Lucia Pena Perez, and Mei Wu at Clinical Genomics Stockholm.

Additional contributors were Sima Rahimi, Gwenna Breton and Emma Västerviga (Clinical Genomics Gothenburg); Halfdan Rydbeck and Lauri Mesilaakso (Clinical Genomics Linköping); Subazini Thankaswamy Kosalai (Clinical Genomics Örebro); Annick Renevey, Peter Pruisscher and Eva Caceres (Clinical Genomics Stockholm); Ryan Kennedy (Clinical Genomics Lund); Anders Sune Pedersen (Danish National Genome Center) and Lucas Taniguti.

We thank the nf-core community for their extensive assistance in the development of this pipeline.

## Contributions and Support

If you would like to contribute to this pipeline, please see the contributing guidelines.

For further information or help, don't hesitate to get in touch on the Slack `#raredisease` channel (you can join with this invite).

## Citations

If you use nf-core/raredisease for your analysis, please cite it using the following doi: 10.5281/zenodo.7995798

An extensive list of references for the tools used by the pipeline can be found in the `CITATIONS.md` file.

You can cite the `nf-core` publication as follows:

**The nf-core framework for community-curated bioinformatics pipelines.**
Philip Ewels, Alexander Peltzer, Sven Fillinger, Harshil Patel, Johannes Alneberg, Andreas Wilm, Maxime Ulysse Garcia, Paolo Di Tommaso & Sven Nahnsen.
_Nat Biotechnol._ 2020 Feb 13. doi: 10.1038/s41587-020-0439-x.

You can read more about MIP's use in healthcare in,

Stranneheim H, Lagerstedt-Robinson K, Magnusson M, et al. Integration of whole genome sequencing into a healthcare setting: high diagnostic rates across multiple clinical entities in 3219 rare disease patients. Genome Med. 2021;13(1):40. doi:10.1186/s13073-021-00855-5
