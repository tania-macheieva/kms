## Introduction

**nf-core/sarek** is a workflow designed to detect variants on whole genome or targeted sequencing data. Initially designed for Human, and Mouse, it can work on any species with a reference genome. Sarek can also handle tumour / normal pairs and could include additional relapses.

The pipeline is built using Nextflow, a workflow tool to run tasks across multiple compute infrastructures in a very portable manner. It uses Docker/Singularity containers making installation trivial and results highly reproducible. The Nextflow DSL2 implementation of this pipeline uses one container per process which makes it much easier to maintain and update software dependencies. Where possible, these processes have been submitted to and installed from nf-core/modules in order to make them available to all nf-core pipelines, and to everyone within the Nextflow community!

On release, automated continuous integration tests run the pipeline on a full-sized dataset on the AWS cloud infrastructure. This ensures that the pipeline runs on AWS, has sensible resource allocation defaults set to run on real-world datasets, and permits the persistent storage of results to benchmark between pipeline releases and other analysis sources. The results obtained from the full-sized test can be viewed on the nf-core website.

It's listed on Elixir - Tools and Data Services Registry and Dockstore.

## Pipeline summary

Depending on the options and samples provided, the pipeline can currently perform the following:

- Form consensus reads from UMI sequences (`fgbio`)
- Sequencing quality control and trimming (enabled by `--trim_fastq`) (`FastQC`, `fastp`)
- Contamination removal (`BBSplit`, enabled by `--tools bbsplit`)
- Map Reads to Reference (`BWA-mem`, `BWA-mem2`, `dragmap` or `Sentieon BWA-mem`)
- Process BAM file (`GATK MarkDuplicates`, `GATK BaseRecalibrator` and `GATK ApplyBQSR` or `Sentieon LocusCollector` and `Sentieon Dedup`)
- _Experimental Feature_: Use GPU-accelerated parabricks implementation as alternative to "Map Reads to Reference" + "Process BAM file" (`--aligner parabricks`)
- Summarise alignment statistics (`samtools stats`, `mosdepth`)
- Variant calling (enabled by `--tools`, see compatibility):
 - `ASCAT`
 - `CNVkit`
 - `Control-FREEC`
 - `DeepSomatic`
 - `DeepVariant`
 - `freebayes`
 - `GATK HaplotypeCaller`
 - `GATK Mutect2`
 - `Parabricks DeepSomatic` (GPU-accelerated)
 - `Parabricks HaplotypeCaller` (Experimental Feature)
 - `Parabricks Deepvariant` (Experimental Feature)
 - `indexcov`
 - `Lofreq`
 - `Manta`
 - `mpileup`
 - `MSIsensor2`
 - `MSIsensor-pro`
 - `MuSE`
 - `Sentieon Haplotyper`
 - `Strelka`
 - `TIDDIT`
- Post-variant calling options, one of:
 - Filtering (`bcftools view` (default: filter by `PASS,.`)), normalisation (`bcftools norm`) and consensus calling (`bcftools isec`, default: called by at least 2 tools `-n+2`) on all vcfs and/or `bcftools concat` for germline vcfs
 - `Varlociraptor` for all vcfs
- Variant filtering and annotation (`SnpEff`, `Ensembl VEP`, `BCFtools annotate`, `SnpSift`)
- Summarise and represent QC (`MultiQC`)

## Usage
NOTE:
If you are new to Nextflow and nf-core, please refer to this page on how to set-up Nextflow. Make sure to test your setup with `-profile test` before running the workflow on actual data.

First, prepare a samplesheet with your input data that looks as follows:

`samplesheet.csv`:

```csv
patient,sample,lane,fastq_1,fastq_2
ID1,S1,L002,ID1_S1_L002_R1_001.fastq.gz,ID1_S1_L002_R2_001.fastq.gz
```

Each row represents a pair of fastq files (paired end).

Now, you can run the pipeline using:

```bash
nextflow run nf-core/sarek \
 -profile <docker/singularity/.../institute> \
 --input samplesheet.csv \
 --outdir <OUTDIR>
```
WARNING:
Please provide pipeline parameters via the CLI or Nextflow `-params-file` option. Custom config files including those provided by the `-c` Nextflow option can be used to provide any configuration _**except for parameters**_; see docs.

For more details and further functionality, please refer to the usage documentation and the parameter documentation.

## Pipeline output

To see the results of an example test run with a full size dataset refer to the results tab on the nf-core website pipeline page.
For more details about the output files and reports, please refer to the
output documentation.

## Benchmarking

On each release, the pipeline is run on 3 full size tests:

- `test_full` runs tumor-normal data for one patient from the SEQ2C consortium
- `test_full_germline` runs a WGS 30X Genome-in-a-Bottle(NA12878) dataset
- `test_full_germline_ncbench_agilent` runs two WES samples with 75M and 200M reads (data available here). The results are uploaded to Zenodo, evaluated against a truth dataset, and results are made available via the NCBench dashboard.

## Credits

Sarek was originally written by Maxime U Garcia and Szilveszter Juhos at the National Genomics Infastructure and National Bioinformatics Infastructure Sweden which are both platforms at SciLifeLab, with the support of The Swedish Childhood Tumor Biobank (Barntumörbanken).
Friederike Hanssen and Gisela Gabernet at QBiC later joined and helped with further development.

The Nextflow DSL2 conversion of the pipeline was lead by Friederike Hanssen and Maxime U Garcia.

Maintenance is now lead by Friederike Hanssen (now at Seqera) and Maxime U Garcia.

Main developers:

- Maxime U Garcia
- Friederike Hanssen

We thank the following people for their extensive assistance in the development of this pipeline:

- Abhinav Sharma
- Adam Talbot
- Adrian Lärkeryd
- Àitor Olivares
- Alexander Peltzer
- Alison Meynert
- Anders Sune Pedersen
- arontommi
- BarryDigby
- Bekir Ergüner
- bjornnystedt
- cgpu
- Chela James
- David Mas-Ponte
- Edmund Miller
- Famke Bäuerle
- Francesco Lescai
- Francisco Martínez
- Gavin Mackenzie
- Gisela Gabernet
- Grant Neilson
- gulfshores
- Harshil Patel
- Hongwei Ye
- James A. Fellows Yates
- Jesper Eisfeldt
- Johannes Alneberg
- Jonas Kjellin
- José Fernández Navarro
- Júlia Mir Pedrol
- Ken Brewer
- Lasse Westergaard Folkersen
- Lucia Conde
- Louis Le Nézet
- Malin Larsson
- Marcel Martin
- Nick Smith
- Nicolas Schcolnicov
- Nilesh Tawari
- Nils Homer
- Olga Botvinnik
- Oskar Wacker
- pallolason
- Paul Cantalupo
- Peter Zoescher
- Phil Ewels
- Pierre Lindenbaum
- Sabrina Krakau
- Sam Minot
- Sebastian-D
- Silvia Morini
- Simon Pearce
- Solenne Correard
- Susanne Jodoin
- Szilveszter Juhos
- Tobias Koch
- Winni Kretzschmar
- Patricie Skaláková

## Acknowledgements

| | |

| | |
| | |
| | |

## Contributions & Support

If you would like to contribute to this pipeline, please see the contributing guidelines.

For further information or help, don't hesitate to get in touch on the Slack `#sarek` channel, or contact the dev team on the Slack `#sarek_dev` channel. (you can join with this invite).

## Citations

If you use `nf-core/sarek` for your analysis, please cite the `Sarek` article as follows:

Friederike Hanssen, Maxime U Garcia, Lasse Folkersen, Anders Sune Pedersen, Francesco Lescai, Susanne Jodoin, Edmund Miller, Oskar Wacker, Nicholas Smith, nf-core community, Gisela Gabernet, Sven Nahnsen **Scalable and efficient DNA sequencing analysis on different compute infrastructures aiding variant discovery** _NAR Genomics and Bioinformatics_ Volume 6, Issue 2, June 2024, lqae031, doi: 10.1093/nargab/lqae031.

Garcia M, Juhos S, Larsson M et al. **Sarek: A portable workflow for whole-genome sequencing analysis of germline and somatic variants [version 2; peer review: 2 approved]** _F1000Research_ 2020, 9:63 doi: 10.12688/f1000research.16665.2.

You can cite the sarek zenodo record for a specific version using the following doi: 10.5281/zenodo.3476425

An extensive list of references for the tools used by the pipeline can be found in the `CITATIONS.md` file.

You can cite the `nf-core` publication as follows:

**The nf-core framework for community-curated bioinformatics pipelines.**
Philip Ewels, Alexander Peltzer, Sven Fillinger, Harshil Patel, Johannes Alneberg, Andreas Wilm, Maxime Ulysse Garcia, Paolo Di Tommaso & Sven Nahnsen.
_Nat Biotechnol._ 2020 Feb 13. doi: 10.1038/s41587-020-0439-x.

## CHANGELOG

- CHANGELOG
