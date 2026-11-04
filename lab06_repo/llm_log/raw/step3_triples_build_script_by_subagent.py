import json
B="/tmp/claude-0/-home-claude/124a6d6b-6bc8-5383-8146-bc49bf72ace0/scratchpad/"
txt={s:open(B+"l6in/"+f,encoding="utf-8").read() for s,f in [("gatk","gatk_hard_filtering.txt"),("cdc","cdc_cascade_testing.txt")]}
G=[
("hard filtering","is_a","variant filtering","Hard-filtering consists of choosing specific thresholds for one or more annotations"),
("variant quality score recalibration","is_a","variant filtering","Even with VQSR, variant sites are being filtered out, not individual sample's data."),
("hard filtering","uses_input","quality by depth","For filtering purposes it is better to use QD than"),
("hard filtering","uses_input","Fisher strand bias","recommendations tell us to fail variants with an FS value greater than 60."),
("hard filtering","uses_input","strand odds ratio","our hard filtering recommendation of failing variants with an SOR value greater than 3 will at"),
("hard filtering","uses_input","mapping quality","You may argue that hard filtering any variant with an MQ value less than 50 is fine as well."),
("quality by depth","has_example","QD < 2","The generic filtering recommendation for QD is to filter out variants with QD below 2."),
("quality by depth","uses_input","read depth","divided by the unfiltered depth of non-"),
("mapping quality","applies_to","sequencing read","This is the root mean square mapping quality over all the reads at the site."),
("rank sum test","uses_input","mapping quality","This is the u-based z-approximation from the Rank Sum Test for mapping qualities."),
("rank sum test","applies_to","allele","compares the mapping qualities of the reads supporting the reference allele and the alternate"),
("variant calling","produces","VCF file","then joint-called the GVCFs using GenotypeGVCFs, yielding an unfiltered VCF callset for the"),
("variant quality score recalibration","uses_input","VCF file","Finally, we ran VQSR on the trio VCF, yielding the filtered callset."),
("hard filtering","applies_to","genetic variant","throwing out any variants that have annotation values above or below the set thresholds."),
("variant quality score recalibration","requires","genetic variant","Unfortunately this method requires a large number of variants and well-curated known variant"),
("strand odds ratio","has_example","SOR > 3","SOR>3.0, MQ<40.0, MQRankSum < -12.5 and ReadPosRankSum < -8.0."),
("mapping quality","has_example","MQ < 40","Our recommendation is to fail any variant with an MQ value less than 40.0."),
("Fisher strand bias","has_example","FS > 60","recommended thresholds for getting passed variants are QD<2.0, FS>60.0,"),
("hard filtering","uses_input","rank sum test","threshold removes any variant with a ReadPosRankSum value less than -8.0."),
("hard filtering","applies_to","germline variant","Hard-filtering germline short variants"),
("variant quality score recalibration","recommended_for","germline variant","recommend for filtering germline short variants)"),
("genetic variant","has_annotation","Fisher strand bias","Notice most of the variants that fail have an FS value greater than 55."),
("genetic variant","has_annotation","strand odds ratio","Notice most of the variants that have an SOR value greater than 3 fail the VQSR filter."),
("genetic variant","has_annotation","quality by depth","This is the variant confidence (from the QUAL field)"),
]
A="diagnosed with a BRCA1, BRCA2, or another genetic change that makes you more likely to get breast, ovarian, and"
H="BRCA1, BRCA2, and most other genetic changes that cause hereditary breast and ovarian cancers"
C=[
("BRCA1","increases_risk_of","breast cancer",A),
("BRCA1","increases_risk_of","ovarian cancer",A),
("BRCA2","increases_risk_of","breast cancer",A),
("BRCA2","increases_risk_of","ovarian cancer",A),
("BRCA1","increases_risk_of","hereditary cancer",H),
("genetic variant","increases_risk_of","hereditary cancer","other genetic changes that cause hereditary breast and ovarian cancers"),
("cascade testing","applies_to","relative","Cascade testing can find family members who have the same genetic change."),
("cascade testing","detects","genetic variant","Cascade testing can find family members who have the same genetic change."),
("cascade testing","detects","BRCA1","Cascade testing for BRCA1, BRCAZ, and other genetic changes"),
("cascade testing","detects","BRCA2","Cascade testing for BRCA1, BRCAZ, and other genetic changes"),
("relative","is_kin_of","proband","family members who are most closely related to the person who has the BRCA1, BRCA2, or"),
("genetic testing","recommended_for","breast cancer","Genetic testing for BRCA1, BRCA2, and other genetic changes is currently recommended for some women with breast cancer"),
("genetic testing","recommended_for","ovarian cancer","and women with ovarian, peritoneal, or fallopian tube cancer."),
("genetic testing","detects","BRCA1","Genetic testing for BRCA1, BRCA2, and other genetic changes"),
("genetic testing","detects","BRCA2","Genetic testing for BRCA1, BRCA2, and other genetic changes"),
("genetic counseling","applies_to","relative","help schedule genetic counseling and testing for your family"),
("genetic counseling","produces","risk assessment","A healthcare provider, such as a genetic counselor, can help with personalized risk estimates for each person in your family."),
]
voc={l.split(" | ")[0] for l in open(B+"l6in/vocabulary.md",encoding="utf-8") if " | " in l}
out=[];n=0
for src,L in (("gatk",G),("cdc",C)):
    for s,p,o,e in L:
        n+=1
        assert e in txt[src],(src,e)
        assert len(e)<=300
        assert s in voc,s
        if p!="has_example": assert o in voc,o
        out.append({"id":"L%03d"%n,"s":s,"p":p,"o":o,"evidence":e,"source":src})
open(B+"l6out/triples_llm_raw.jsonl","w",encoding="utf-8").write("\n".join(json.dumps(x,ensure_ascii=False) for x in out)+"\n")
U=[
("gatk","strand bias","Strand Bias tells us","whether the alternate allele was seen","no concept 'strand bias' in vocabulary"),
]
def u(src,sur,ev,r): return {"surface":sur,"source":src,"evidence":ev,"reason":r}
U=[
u("gatk","strand bias","SB gives the raw counts of reads supporting each allele on the forward and reverse","немає поняття у словнику"),
u("gatk","QUAL","This is the variant confidence (from the QUAL field)","поле QUAL відсутнє у словнику"),
u("gatk","HaplotypeCaller","using HaplotypeCaller in GVCF mode, yielding a GVCF file for each sample.","конкретний інструмент відсутній у словнику"),
u("gatk","GenotypeGVCFs","then joint-called the GVCFs using GenotypeGVCFs, yielding an unfiltered VCF callset for the","конкретний інструмент відсутній у словнику"),
u("gatk","GVCF file","yielding a GVCF file for each sample.","формат GVCF відсутній у словнику"),
u("gatk","Genome in a Bottle truthset","annotating the raw callset using the Genome in a Bottle truthset for","еталонний набір відсутній у словнику"),
u("gatk","MQRankSum","This is the u-based z-approximation from the Rank Sum Test for mapping qualities.","конкретний показник відсутній (є лише загальний rank sum test)"),
u("gatk","ReadPosRankSum","from the Rank Sum Test for site position within reads.","конкретний показник відсутній (є лише загальний rank sum test)"),
u("gatk","heterozygous (het)","These two peaks correspond to variants that are mostly observed in heterozygous","поняття зиготності відсутнє у словнику"),
u("gatk","truth set","One of the most helpful ways to approach hard-filtering is to visualize the distribution of","поняття відсутнє у словнику"),
u("cdc","siblings","your mother, father, children, and siblings have a 1 in 2 (50%) chance of having the same","типи родичів відсутні у словнику (лише relative)"),
u("cdc","cousins","Your cousins and other more distantly related family members can have as much as a 1 in 8 (12.5%) chance of having the same","типи родичів відсутні у словнику (лише relative)"),
u("cdc","genetic counselor","A genetic counselor can help you decide if genetic testing is recommended.","роль фахівця відсутня у словнику"),
u("cdc","genetic test report","Provide your genetic test report to any genetic counselor or healthcare provider who orders testing for your family.","артефакт відсутній у словнику"),
u("cdc","fallopian tube cancer","and women with ovarian, peritoneal, or fallopian tube cancer.","окремі види раку відсутні у словнику"),
u("cdc","adults (18 years of age and older)","testing for these genetic changes should only be done on adults (18 years of age and older).","вікова група відсутня у словнику"),
u("cdc","insurance coverage","Some insurance companies will cover genetic testing for families if a known genetic change is found.","поняття відсутнє у словнику"),
]
for x in U: assert x["evidence"] in txt[x["source"]],x["evidence"]
json.dump(U,open(B+"l6out/unmapped_raw.json","w",encoding="utf-8"),ensure_ascii=False,indent=1)
print(sum(1 for x in out if x["source"]=="gatk"),sum(1 for x in out if x["source"]=="cdc"),len(U))
