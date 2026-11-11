# Ручна таксономія «зверху вниз». Принцип поділу L1: ділянка транскрипта, на яку впливає варіант
# (CDS / сплайсинг / UTR / інтрони-екзони / некодувальні / неповні транскрипти); L2 — тип ефекту.
# Побудована за назвами й визначеннями термінів, до перегляду їхньої ієрархії в SO.
M = {
 "CDS: зміна амінокислоти": ["missense_variant","conservative_missense_variant","non_conservative_missense_variant","nonsynonymous_variant","protein_altering_variant","rare_amino_acid_variant","pyrrolysine_loss","selenocysteine_gain","selenocysteine_loss","coding_sequence_variant"],
 "CDS: без зміни білка": ["synonymous_variant","stop_retained_variant","start_retained_variant"],
 "CDS: зсув рамки": ["frameshift_variant","minus_1_frameshift_variant","minus_2_frameshift_variant","plus_1_frameshift_variant","plus_2_frameshift_variant","frameshift_elongation","frameshift_truncation","frame_restoring_variant","frameshift_variant_NMD_escaping","frameshift_variant_NMD_triggering"],
 "CDS: інфрейм-індели": ["inframe_variant","inframe_indel","inframe_insertion","inframe_deletion","conservative_inframe_deletion","conservative_inframe_insertion","disruptive_inframe_deletion","disruptive_inframe_insertion"],
 "CDS: старт/стоп-кодон": ["initiator_codon_variant","start_lost","stop_gained","stop_lost","terminator_codon_variant","stop_gained_NMD_escaping","stop_gained_NMD_triggering","redundant_inserted_stop_gained","incomplete_terminal_codon_variant"],
 "Сплайсинг: канонічні сайти": ["splice_acceptor_variant","splice_donor_variant","splice_site_variant","splice_acceptor_variant_NMD_escaping","splice_acceptor_variant_NMD_triggering","splice_donor_variant_NMD_escaping","splice_donor_variant_NMD_triggering"],
 "Сплайсинг: прилеглі регіони": ["splice_region_variant","splice_donor_5th_base_variant","splice_donor_region_variant","splice_polypyrimidine_tract_variant","exonic_splice_region_variant","extended_intronic_splice_region_variant","non_coding_transcript_splice_region_variant"],
 "Сплайсинг: нові сайти й екзони": ["cryptic_splice_acceptor","cryptic_splice_donor","cryptic_splice_site_variant","splicing_variant","exon_loss_variant","intron_gain_variant","pseudoexon_variant"],
 "UTR: 5' структура": ["5_prime_UTR_variant","5_prime_UTR_exon_variant","5_prime_UTR_intron_variant","5_prime_UTR_elongation","5_prime_UTR_truncation"],
 "UTR: 5' передчасний старт": ["5_prime_UTR_premature_start_codon_gain_variant","5_prime_UTR_premature_start_codon_loss_variant","5_prime_UTR_premature_start_codon_variant","five_prime_UTR_premature_start_codon_location_variant"],
 "UTR: 5' uORF": ["5_prime_UTR_uORF_variant","5_prime_UTR_uORF_stop_codon_variant","5_prime_UTR_uORF_stop_codon_gain_variant","5_prime_UTR_uORF_stop_codon_loss_variant","5_prime_UTR_uORF_frameshift_variant"],
 "UTR: 3'": ["3_prime_UTR_variant","3_prime_UTR_exon_variant","3_prime_UTR_intron_variant","3_prime_UTR_elongation","3_prime_UTR_truncation"],
 "UTR: загальне": ["UTR_variant"],
 "Інтрони й екзони: інтрони": ["intron_variant","coding_transcript_intron_variant","conserved_intron_variant","non_coding_transcript_intron_variant"],
 "Інтрони й екзони: екзони": ["exon_variant","non_coding_transcript_exon_variant"],
 "Некодувальні РНК": ["non_coding_transcript_variant","mature_miRNA_variant","transcript_secondary_structure_variant","compensatory_transcript_secondary_structure_variant"],
 "Неповні транскрипти": ["incomplete_transcript_variant","incomplete_transcript_3UTR_variant","incomplete_transcript_5UTR_variant","incomplete_transcript_CDS","incomplete_transcript_coding_splice_variant","incomplete_transcript_exonic_variant","incomplete_transcript_intronic_variant","incomplete_transcript_splice_region_variant"],
 "Інше": ["NMD_transcript_variant","coding_transcript_variant","complex_transcript_variant","intragenic_variant","partially_duplicated_transcript","five_prime_duplicated_transcript","three_prime_duplicated_transcript"],
}
L1_OF = {"CDS":"CDS","Сплайсинг":"Сплайсинг","UTR":"UTR","Інтрони й екзони":"Інтрони й екзони"}
def l1(l2):
    return l2.split(":")[0] if ":" in l2 else l2
