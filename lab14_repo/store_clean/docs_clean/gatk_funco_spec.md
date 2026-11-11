## 0 - Introduction
This page details the specification of the annotations that Funcotator can create.

Detailed information on Funcotator can be found in this forum post.

### 0.1 - Table of Contents
0. 0.0 Introduction
 1. 0.1 Table of Contents
1. 1.0 Annotation Specification
 1. 1.1 Annotations for Pre-Packaged Data Sources
 1. 1.1.1 Gencode Annotation Specification
 1. hugoSymbol
 2. ncbiBuild
 3. chromosome
 4. start
 5. end
 6. variantClassification
 7. secondaryVariantClassification
 8. variantType
 9. refAllele
 10. tumorSeqAllele1
 11. tumorSeqAllele2
 12. genomeChange
 13. annotationTranscript
 14. transcriptStrand
 15. transcriptExon
 16. transcriptPos
 17. cDnaChange
 18. codonChange
 19. proteinChange
 20. gcContent
 21. referenceContext
 22. otherTranscripts


## 1.1 Annotations for Pre-Packaged Data Sources
The pre-packaged data sources will create a set of baseline, or default annotations for an input data set.
Most of these data sources copy and paste values from their source files into the output of Funcotator to create annotations. In this sense they are trivial data sources.

### 1.1.1 - Gencode Annotation Specification
Funcotator performs some processing on the input data to create the Gencode annotations. Gencode is currently required, so Funcotator will create these annotations for all input variants.

The order and a specification of the Gencode annotations that Funcotator creates is as follows:

1. **hugoSymbol**
Type: _String_
The name of the gene in which the annotated variant allele occurs. If the variant allele occurs outside of any known gene boundaries, then this field is set to "Unknown".

2. **ncbiBuild**
Type: _String_
The reference which was used to create this Gencode annotation. Current valid values are: `hg19` or `hg38`.

3. **chromosome**
Type: _String_
The contig in which the variant occurs. Will always correspond to the contig in the variant position.

4. **start**
Type: _Integer_
The start position in genomic coordinates of the variant allele being annotated (1-based, inclusive). Will always correspond to the start in the variant position.

5. **end**
Type: _Integer_
The end position in genomic coordinates of the variant allele being annotated (1-based, inclusive). Will always correspond to the position last base in the variant allele.

6. **variantClassification**
Type: _String_
The classification of the variant being annotated. Will always be one of the following:

* `COULD_NOT_DETERMINE`
 Variant classification could not be determined.

* `INTRON`
 Variant lies between exons within the bounds of the chosen transcript.
 Only valid for Introns.

* `FIVE_PRIME_UTR`
 Variant is on the 5'UTR for the chosen transcript.
 Only valid for UTRs.

* `THREE_PRIME_UTR`
 Variant is on the 3'UTR for the chosen transcript
 Only valid for UTRs.

* `IGR`
 Intergenic region. Does not overlap any transcript.
 Only valid for IGRs.

* `FIVE_PRIME_FLANK`
 The variant is upstream of the chosen transcript
 Only valid for IGRs.

* `THREE_PRIME_FLANK`
 The variant is downstream of the chosen transcript
 Only valid for IGRs.

* `MISSENSE`
 The point mutation alters the protein structure by one amino acid.
 Can occur in Coding regions or Introns.

* `NONSENSE`
 A premature stop codon is created by the variant.
 Can occur in Coding regions or Introns.

* `NONSTOP`
 Variant removes stop codon.
 Can occur in Coding regions or Introns.

* `SILENT`
 Variant is in coding region of the chosen transcript, but protein structure is identical.
 Can occur in Coding regions or Introns.

* `SPLICE_SITE`
 The variant is within a configurable number of bases of a splice site. See the secondary classification to determine if it lies on the exon or intron side.
 Can occur in Coding regions or Introns.

* `IN_FRAME_DEL`
 Deletion that keeps the sequence in frame.
 Can occur in Coding regions or Introns.

* `IN_FRAME_INS`
 Insertion that keeps the sequence in frame.
 Can occur in Coding regions or Introns.

* `FRAME_SHIFT_INS`
 Insertion that moves the coding sequence out of frame.
 Can occur in Coding regions or Introns.

* `FRAME_SHIFT_DEL`
 Deletion that moves the sequence out of frame.
 Can occur in Coding regions or Introns.

* `START_CODON_SNP`
 Point mutation that overlaps the start codon.
 Can occur in Coding regions.

* `START_CODON_INS`
 Insertion that overlaps the start codon.
 Can occur in Coding regions.

* `START_CODON_DEL`
 Deletion that overlaps the start codon.
 Can occur in Coding regions.

* `DE_NOVO_START_IN_FRAME`
 New start codon is created by the given variant using the chosen transcript.
 However, it is in frame relative to the coded protein, meaning that if the coding sequence were extended
 then the new start codon would be in frame with the
 existing start and stop codons.

 This can only occur in a 5' UTR.

* `DE_NOVO_START_OUT_FRAME`
 New start codon is created by the given variant using the chosen transcript.
 However, it is out of frame relative to the coded protein, meaning that if the coding sequence were extended
 then the new start codon would NOT be in frame with
 the existing start and stop codons.

 This can only occur in a 5' UTR.

* `RNA`
 Variant lies on one of the RNA transcripts.
 (special catch-all case)

* `LINCRNA`
 Variant lies on one of the lincRNAs.
 (special catch-all case)

7. **secondaryVariantClassification**
Type: _String_
Additional variant classification information for variant alleles that have a `VariantClassification` of `SPLICE_SITE`.
For a variant allele with the `VariantClassification` of `SPLICE_SITE`, this will indicate the specific classification of the variant.
For all variants that do **not** have the `VariantClassification` of `SPLICE_SITE`, this will be the empty string.

8. **variantType**
Type: _String_
Basic information about the variant allele being annotated. Can be one of:
* `INS` - The variant allele is some kind of insertion.</li>
* `DEL` - The variant allele is some kind of deletion.</li>
* `SNP` - The variant allele is a single nucleotide polymorphism.</li>
* `DNP` - The variant allele is a di-nucleotide polymorphism.</li>
* `TNP` - The variant allele is a tri-nucleotide polymorphism.</li>
* `ONP` - The variant allele is an oligo-nucleotide polymorphism (Synonymous with MNP).</li>
* `MNP` - The variant allele is a multi-nucleotide polymorphism (Synonymous with ONP).</li>
* `NA` - The variant allele type cannot be determined.</li>

9. **refAllele**
Type: _String_
The reference allele for the position at which this this variant allele occurs.
For insertions, this will be set to `-`.

10. **tumorSeqAllele1**
Type: _String_
Always the same as the reference allele. This field is a hold-over required for MAF annotations.
For insertions, this will be set to `-`.

11. **tumorSeqAllele2**
Type: _String_
The variant allele being annotated. This field only includes the bases that are different from the reference.
For the input VCF records, this field may slightly differ from the alternate allele reported in the base data for the `VariantContext`.
For deletions, this will be set to `-`.

12. **genomeChange**
Type: _String_
A _String_ summarizing the change resulting from this variant allele within the context of the whole genome sequence.
Generally the format of this field is:
`g.[CONTIG]:[POSITION][BASES CHANGED]`

The format of this field slightly varies based on `VariantType`:

* **_Insertion_**
 `g.[CONTIG]:[POSITION OF BASE PRIOR TO INSERTION]_[POSITION OF BASE AFTER INSERTION]ins[BASES INSERTED]`
 E.g.:
 `g.chr19:2018023_2018024insAATCG`
 This indicates that the bases AATCG were inserted between bases 2018023 and 2018024 on chromosome 19.

* **_Deletion_**
 `g.[CONTIG]:[POSITION OF BASE DELETED]del[BASE DELETED]`
 E.g.:
 `g.chr19:2018023delT`
 This indicates that the base T was deleted at position 2018023 on chromosome 19.
 _OR_
 `g.[CONTIG]:[POSITION OF FIRST BASE DELETED]_[POSITION OF LAST BASE DELETED]del[BASES DELETED]`
 E.g.:
 `g.chr19:2018023_2018025delTTG`
 This indicates that the bases TTG were deleted starting at position 2018023 and ending at position 2018025 on chromosome 19.

* **_SNP_**
 `g.[CONTIG]:[POSITION OF BASE ALTERED][REFERENCE BASE]>[ALTERNATE BASE]`
 E.g.:
 `g.chr19:2018023T>G`
 This indicates that the base T was changed to G at position 2018023 on chromosome 19.

* **_MNP (including DNPs, TNPs)_**
 `g.[CONTIG]:[POSITION OF FIRST BASE ALTERED]_[POSITION OF LAST BASE ALTERED][REFERENCE BASES]>[ALTERNATE BASES]`
 E.g.:
 `g.chr19:2018023_2018025TTG>GAT`
 This indicates that the bases TTG were changed to GAT from position 2018023 to position 2018025 on chromosome 19.

13. **annotationTranscript**
Type: _String_
The ID of the transcript chosen for the detailed Gencode annotation reporting.
E.g.: `ENST00000435064.1`
If the variant allele does not occur within the bounds of any transcript (e.g. is of type `IGR`), then this field is empty.

14. **transcriptStrand**
Type: _String_
The strand direction associated with the transcript on which this variant allele occurs.
Either `+` or `-`.

15. **transcriptExon**
Type: _Integer_ or Empty
The exon number on the transcript in which this variant allele occurs (1-based). Corresponds directly to the Gencode exon number.
If the variant does not occur in the expressed transcript of the corresponding gene (e.g. is of type `INTRON` or `IGR`), then this field is empty.

16. **transcriptPos**
Type: _Integer_ or Empty
Position in the chosen transcript of the variant allele. All positions listed are 1-based and inclusive (meaning that the first base in the transcript starts at position 1).
For variant alleles that occur at a single base, the format is simply the position at which that variant occurs in the transcript (e.g. `1294`)
For variant alleles spanning multiple bases, the format is:
`[START]_[END]`
E.g.: `1236_1237`
If the variant does not occur in the expressed transcript of the corresponding gene (e.g. is of type`INTRON` or `IGR`), then this field is empty.

17. **cDnaChange**
Type: _String_
A _String_ that summarizes the change resulting from this variant allele in the coding sequence for the transcript in which it occurs.
Positions in this field are _**relative to the start of the transcript (1-based, inclusive)**_ unless otherwise noted.
Generally the format of this field is:
`c.[POSITION][BASES CHANGED]`

The format of this field slightly varies based on `VariantType`, the number of affected bases, and whether the variant allele is a `SPLICE_SITE`:

* _**Insertions**_
 `c.[POSITION OF BASE PRIOR TO INSERTION]_[POSITION OF BASE AFTER INSERTION]ins[BASES INSERTED]`
 E.g.:
 `c.2018_2019insAA`
 This indicates that the bases AA were inserted between bases 2018 and 2019 in the transcript associated with this variant allele.

* _**Deletions of One Base**_
 `c.[POSITION OF BASE DELETED]del[BASE DELETED]`
 E.g.:
 `c2018delT`
 This indicates that the base T was deleted at position 2018 in the transcript associated with this variant allele.

* _**Deletions of Multiple Bases**_
 `c.[POSITION OF FIRST BASE DELETED]_[POSITION OF LAST BASE DELETED]del[BASES DELETED]`
 E.g.:
 `c2018_2022delTTCAG`
 This indicates that the bases TTCAG were deleted from position 2018 to position 2022 in the transcript associated with this variant allele.

* _**SNPs**_
 `c.[POSITION OF BASE CHANGED]>[NEW BASE]`
 E.g.:
 `c.1507T>G`
 This indicates that the base T was changed to G at position 1507 in the transcript associated with this variant allele.

* _**MNPs (including DNPs, TNPs)**_
 `c.[POSITION OF FIRST BASE CHANGED]_[POSITION OF LAST BASE CHANGED]>[NEW BASES]`
 E.g.:
 `c.12899_12900AG>TA`
 This indicates that the bases AG were changed to TA from position 12899 to position 12900 in the transcript associated with this variant allele.

* _**INTRONIC Variants**_
 For variants occuring in INTRONs, the cDNA string position indicates the offset from the exon boundary for the start of the variant. The whole string takes the form:
 `c.e[EXON NUMBER][+|-][BASES FROM EXON][REF ALLELE]>[ALT ALLELE]`
 E.g.:
 `c.e81-4TAA>A`
 This indicates that the bases TAA were changed to A starting four bases before exon 81 in the transcript associated with this variant allele.

If the variant does not occur in the expressed transcript of the corresponding gene (e.g. is of type `IGR`), then this field is empty.

18. **codonChange**
Type: _String_
A _String_ that representing the codon-aligned change resulting from this variant allele in the coding sequence for the transcript in which it occurs.
Positions in this field are relative to the start of the transcript (1-based, inclusive) and aligned to the coding sequence unless otherwise noted.
Unlike the cDnaChange, the bases reported in the codonChange string will always have a length evenly divisble by 3 (except for frameshifts) and represent what the codons would be if the variant alternate allele were expressed in the reference sequence.
Capitalized bases represent the bases changed by the variant alternate allele. Lower-case bases represent reference bases.
Generally the format of this field is:
`c.[POSITION][BASES CHANGED]`
The format of this field slightly varies based on `VariantType`, the number of affected bases, and whether the variant allele occurs in an Intron:

* _**In-Frame Insertions**_
 `c.([POSITION OF FIRST BASE IN FIRST CODON IN THE REFERENCE AFFECTED BY THIS VARIANT]-[POSITION OF LAST BASE IN LAST CODON IN THE REFERENCE AFFECTED BY THIS VARIANT][REFERENCE CODONS]>[EXPRESSED CODONS]`
 E.g.:
 `c.(19-21)ctt>ctCGTt`
 This indicates that the bases CGT were inserted before the 6th codon (starting at base 19, ending at base 21) in the transcript associated with this variant allele, and the resulting expressed codons would be `ctCGTt`.

* _**In-Frame Deletions of Complete Codons (codon-aligned deletions)**_
 `c.([POSITION OF FIRST BASE IN FIRST CODON DELETED]-[POSITION OF LAST BASE IN LAST CODON DELETED][REFERENCE CODONS]del`
 E.g.:
 `c.(997-999)gcadel`
 This indicates that the 332nd codon (starting at base 997, ending at base 999) was deleted in the transcript associated with this variant allele, and the deleted codon bases are `gca`.

* _**In-Frame Deletions Spanning Multiple Codons**_
 `c.([POSITION OF FIRST BASE IN FIRST CODON DELETED]-[POSITION OF LAST BASE IN LAST CODON DELETED][REFERENCE CODONS]>[EXPRESSED CODONS]`
 E.g.:
 `c.(997-1002)gcactc>gtc`
 This indicates that bases in the 332nd codon (starting at base 997) and 333rd codon (ending at base 1002) were deleted in the transcript associated with this variant allele, and the resulting expressed codon would be gtc .

* _**Frame Shift Insertions and Deletions**_
 `c.([POSITION OF FIRST BASE IN LAST CORRECTLY EXPRESSED/REFERENCE CODON]-[POSITION OF LAST BASE IN LAST CORRECTLY EXPRESSED/REFERENCE CODON][REFERENCE CODONS]fs`
 E.g.:
 `c.(997-999)gcafs`
 This indicates that bases just _**AFTER**_ the 332nd codon (starting at base 997, ending at base 999) were inserted or deleted in the transcript associated with this variant allele resulting in a frame shift, and that the last correctly transcribed codon would be codon 332 (starting at base 997, ending at base 999), `gca`.

* _**SNPs / MNPs**_
 `c.([POSITION OF FIRST BASE IN FIRST CODON IN THE REFERENCE AFFECTED BY THIS VARIANT]-[POSITION OF LAST BASE IN LAST CODON IN THE REFERENCE AFFECTED BY THIS VARIANT][REFERENCE CODONS]>[EXPRESSED CODONS]`
 E.g. 1:
 `c.(39871-39873)cCC>cTT`
 This indicates that the bases `CC`were changed to `TT` in the 13290th codon (starting at base 39871, ending at base 39873) in the transcript associated with this variant allele, and the resulting expressed codon would be `cTT`.
 E.g. 2:
 `c.(4-9)ctAAgc>ctGCgc`
 This indicates that the bases `AA` starting in the 2nd codon (starting at base 4) and ending in the 3rd codon (ending at base 9) were changed to `GC` in the transcript associated with this variant allele, and the resulting expressed codons would be `ctGCgc`.

19. **proteinChange**
Type: _String_
A short string representing the predicted amino acid sequence change in the product of the gene transcript in which this variant alternate allele occurs.
Positions in this field are relative to the start of the amino acid sequence (1-based, inclusive) resulting from decoding the codons in the transcript in which this variant alternate allele occurs unless otherwise noted.
Amino acid abbreviations are the standard letters as can be found in this table with the exception of the stop codon, which is represented by `*`.
It is important to note that the positions and amino acids reported in this string may not directly align to the codons in which the variant alternate allele occurs. This is most often due to the variant occurring in a set of tandem repeats which would cause the amino acid change to be "pushed" to the end of the tandem repeats.
For protein change strings in the Mitochondrial contig, the mitochondrial genetic code is used (rather than the standard code).
The format of this field takes two forms:

* **_Protein Changes with One Amino Acid Changed_**
 `p.[REFERENCE AMINO ACID][POSITION][PREDICTED EXPRESSED AMINO ACID]`
 E.g. 1:
 `p.V5T`
 The amino acid at protein position 5 was `V` (Valine) in the reference and would become `T` (Threonine) with the variant alternate allele expressed.
 E.g. 2:
 `p.R2R`
 The amino acid at protein position 2 was `R` (Argenine) in the reference and would become `R` (Argenine) with the variant alternate allele expressed (no change in amino acid sequence / silent variant classification).

* _**Protein Changes with Multiple Amino Acids Changed**_
 `p.[FIRST AFFECTED AMINO ACID POSITION]_[LAST AFFECTED AMINO ACID POSITION][REFERENCE AMINO ACIDS]>[PREDICTED EXPRESSED AMINO ACIDS]`
 E.g.:
 `p.100_101Q*>FL`
 The amino acid sequence starting at protein position 100 and ending at protein position 101 was `Q*` (Glutamine,STOP) in the reference and would become `FL` (Phenylalanine,Leucine) with the variant alternate allele expressed.

If the variant alternate allele does not occur in a coding region, this field will be empty.

20. **gcContent**
Type: _Double_
Represents the fraction of Guanine and Cytosine bases in a window of a given size around a variant. This window size does not include any bases in the variant alternate allele itself. By default the window size is 200 bases.

21. **referenceContext**
Type: _String_
The _**strand-correct**_ reference coding sequence in a given window around the reference allele. By default the window size is `10 bases`.
E.g. For the reference context around a variant with the reference allele `C` on the `+` strand:
```
 [REF ALLELE]
 |
 v
 GAACCCACGTCGGTGAGGGCC
 |________| |________|
 v v
 10 bases 10 bases
 (window size) (window size)
```
_**Strand-correct**_ specifically means that if the strand of this transcript is determined to be `-` then the sequence is reverse complemented.
E.g. For the reference context around a variant with the reference allele `C` on the `-` strand:
```
 [REF ALLELE]
 |
 v
 CACGAAAGTCGTTGCGGATCT
 |________| |________|
 v v
 10 bases 10 bases
 (window size) (window size)
```

22. **otherTranscripts**
Type: _String_
A summary of the other transcripts in which this variant occurs, which were not chosen for detailed reporting due to the transcript selection scheme.
Each other transcript is represented by a condensed string that indicates how that transcript would be affected by this variant alternate allele.
Each other transcript takes the form:
`[HUGO SYMBOL]_[TRANSCRIPT ID]_[VARIANT CLASSIFICATION]_[PROTEIN CHANGE STRING]`
E.g.:
`SDF4_ENST00000263741.7_MISSENSE_p.R243Q`
If the other transcript does not have a protein change string, then that part is not rendered.
In the event that there are multiple other transcripts, these transcripts are separated by `/`
E.g.:
`SDF4_ENST00000263741.7_MISSENSE_p.R243Q/TNFRSF4_ENST00000379236.3_FIVE_PRIME_FLANK`
If this variant alternate allele occurs in only one transcript, this field will be empty.

Other annotations will follow the Gencode annotations and will be based on the data sources included in the data sources directory.
<hr>
