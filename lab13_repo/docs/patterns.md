# Закономірності в графі знань (ЛР13, результат R5)

Дані: 616 фрагментів (heading-chunks ЛР10, лише зовнішня документація, 24 документів), елементи — сутності методу A (Tool, FileFormat, Metric, Resource, Procedure), ключ — нормалізована назва + тип. Алгоритм: правила з одним антецедентом, мінімум 12 фрагментів (support ≥ 0.019), confidence ≥ 0.6, lift ≥ 1.5; кандидатів: **28** (таблиця — `eval/patterns_rules.csv`, топ-40 за lift·support).

## Перевірки (як відрізнити закономірність від збігу)

1. **Випадковість**: перестановковий тест — стовпець наслідку перемішується *всередині кожного документа* (зберігає базову частоту в документі, тож усуває ефект «документ про X»), 2000 перестановок, p = частка null-lift ≥ спостереженого.
2. **Стабільність**: бутстреп за *документами* (300 повторів, документи — кластер залежності фрагментів) → частка повторів, де confidence ≥ 0,6 і lift ≥ 1,5; плюс lift у двох половинах (парні/непарні документи).
3. **Широта/механізм**: правило має спиратися на ≥ 3 документи; для кожного — доменне пояснення механізму.
**Правило рішення (задано до перегляду таблиці):** accept, якщо p < 0,01 І bootstrap-частка ≥ 0,8 І ≥ 3 документи І lift > 1 в обох половинах; інакше reject.

Підсумок: 6 прийнято, 22 відхилено з 28 перевірених.

## Правила: метрики, перевірки, рішення

| Правило A → B | support (фрагм.) | conf | lift | док. | p (перест.) | bootstrap | lift 2 половин | Рішення |
|---|---|---|---|---|---|---|---|---|
| ac → an | 0.024 (15) | 0.79 | 32.4 | 3 | 0.0005 | 0.90 | 12.9 / 383.0 | **accept** |
| an → ac | 0.024 (15) | 1.00 | 32.4 | 3 | 0.0005 | 0.97 | 12.9 / 383.0 | **accept** |
| singularity → docker | 0.028 (17) | 0.94 | 12.7 | 7 | 0.0005 | 1.00 | 12.9 / 12.5 | **accept** |
| vep → annotation | 0.039 (24) | 0.83 | 4.2 | 6 | 0.0005 | 0.98 | 3.1 / 4.1 | **accept** |
| snpeff → annotation | 0.026 (16) | 0.80 | 4.1 | 4 | 0.0005 | 0.95 | 4.2 / 3.8 | **accept** |
| vcfanno → annotation | 0.019 (12) | 0.92 | 4.7 | 4 | 0.0005 | 0.97 | 6.3 / 4.2 | **accept** |
| raredisease → nextflow | 0.073 (45) | 0.92 | 3.8 | 3 | 0.0615 | 0.67 | 12.9 / 2.6 | **reject** |
| mutect2 multi → funcotator | 0.019 (12) | 0.92 | 10.0 | 1 | 0.3373 | 0.65 | 0.0 / 6.9 | **reject** |
| tabix → vcf | 0.054 (33) | 0.81 | 2.3 | 4 | 0.0005 | 0.70 | 1.4 / 4.5 | **reject** |
| bcf → vcf | 0.044 (27) | 0.96 | 2.7 | 1 | 1.0 | 0.63 | 1.5 / 0.0 | **reject** |
| bcftools → vcf | 0.058 (36) | 0.61 | 1.7 | 4 | 0.7551 | 0.33 | 1.4 / 1.3 | **reject** |
| deepvariant → variant calling | 0.021 (13) | 0.65 | 4.6 | 6 | 0.0005 | 0.71 | 5.2 / 4.1 | **reject** |
| filtering → vcf | 0.045 (28) | 0.70 | 2.0 | 5 | 0.0085 | 0.59 | 1.3 / 3.2 | **reject** |

## Механізм і обґрунтування рішень

- **ac → an** — accept (passes chance, stability and breadth checks). AC (allele count) and AN (allele number) are standard INFO fields always listed together in annotation tables; mechanism = co-documentation of a field set. Only 3 documents, all GATK/Funcotator-family.
- **an → ac** — accept (passes chance, stability and breadth checks). Converse of the previous rule (confidence 1.0).
- **singularity → docker** — accept (passes chance, stability and breadth checks). Both are container engines that the Nextflow-based pipelines document side by side (profiles -profile docker / singularity); mechanism = documentation boilerplate, true but low informational value (lift 12.7 is inflated by rarity).
- **vep → annotation** — accept (passes chance, stability and breadth checks). VEP is by definition a variant-annotation tool; the documents describe it in annotation context (mechanism: the tool's function).
- **snpeff → annotation** — accept (passes chance, stability and breadth checks). Same mechanism as VEP: SnpEff is an annotation tool; confirms that the rule reflects function, not text layout.
- **vcfanno → annotation** — accept (passes chance, stability and breadth checks). vcfanno annotates VCFs with other files; mechanism = function. Caveat: the three annotation rules share one consequent and one mechanism, they are not independent evidence.
- **raredisease → nextflow** — reject (chance not excluded (p=0.0615); unstable (bootstrap share 0.67)). Nextflow boilerplate (run commands) in every usage chunk of the pipeline; not excluded as chance (p=0.06) and driven by 3 documents.
- **mutect2 multi → funcotator** — reject (chance not excluded (p=0.3373); unstable (bootstrap share 0.65); only 1 document(s); lift <= 1 in one document half). Artefact of one WDL document that lists both workflows in the same input table (1 document).
- **tabix → vcf** — reject (unstable (bootstrap share 0.70)). Mechanism is real (tabix indexes bgzipped VCF) and p<0.001, but only 70% of bootstrap resamples keep the rule: borderline, rejected by the pre-set threshold (0.8).
- **bcf → vcf** — reject (chance not excluded (p=1.0); unstable (bootstrap share 0.63); only 1 document(s); lift <= 1 in one document half). One document (bcftools manual) discusses BCF and VCF together; a single-document pattern.
- **bcftools → vcf** — reject (chance not excluded (p=0.7551); unstable (bootstrap share 0.33)). Plausible mechanism (bcftools works on VCF/BCF), but lift is only 1.7 and the rule is not stable under document resampling.
- **deepvariant → variant calling** — reject (unstable (bootstrap share 0.71)). Mechanism real (DeepVariant is a variant caller); bootstrap share 0.71 < 0.8 -> rejected by threshold although plausible; decision may change with more documents.
- **filtering → vcf** — reject (unstable (bootstrap share 0.59)). Plausible (filters act on VCF records) but unstable under resampling and weak lift (2.0).

## Обмеження

- Сутності цього аналізу — з методу A (правила + словник, зібраний на dev), тому словник визначає, які патерни взагалі можливі; точність A на тесті (F1 сутностей 0,59) означає шум в елементах.
- Лише правила з одним антецедентом; 24 документи, деякі (sarek, bcftools) домінують; accepted-правила про анотацію мають спільний наслідок і спільний механізм — це один висновок, а не три.
- «Прийнято» означає «пройшло задані перевірки на цьому корпусі», а не «закон предметної області»; AC→AN та singularity→docker істинні, але тривіальні (документаційна спільність).
