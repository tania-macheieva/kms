# Три карти для оцінювання (порядок і назви умовні)

## Карта A

Поняття: genetic variant; single nucleotide polymorphism; insertion-deletion; germline variant; pathogenic variant; gene; BRCA1; BRCA2; gene panel; VCF file; BAM file; variant calling; sequence alignment; variant filtering; hard filtering; variant quality score recalibration; quality by depth; Fisher strand bias; strand odds ratio; mapping quality; rank sum test; read depth; exon; hereditary cancer; breast cancer; ovarian cancer; proband; relative; family history; genetic testing; cascade testing; genetic counseling; risk assessment; QD < 2 (приклад); FS > 60 (SNP) (приклад); SOR > 3 (приклад); MQ < 40 (приклад); рідний брат/сестра: 50% (приклад); двоюрідний родич: до 12,5% (приклад)

Пропозиції (s — відношення → o):
- single nucleotide polymorphism — є різновидом → genetic variant
- insertion-deletion — є різновидом → genetic variant
- germline variant — є різновидом → genetic variant
- pathogenic variant — є різновидом → genetic variant
- BRCA1 — є різновидом → gene
- BRCA2 — є різновидом → gene
- gene — є складовою → gene panel
- sequence alignment — створює → BAM file
- variant calling — використовує → BAM file
- variant calling — створює → VCF file
- variant calling — виявляє → genetic variant
- genetic variant — має показник → quality by depth
- genetic variant — має показник → Fisher strand bias
- genetic variant — має показник → strand odds ratio
- genetic variant — має показник → mapping quality
- hard filtering — є різновидом → variant filtering
- variant quality score recalibration — є різновидом → variant filtering
- variant filtering — застосовується до → VCF file  [КРОС-ЗВ'ЯЗОК: Поєднує кластер контролю якості з файлами результатів виклику варіантів: фільтрація працює над VCF.]
- hard filtering — використовує → quality by depth
- hard filtering — використовує → Fisher strand bias
- hard filtering — використовує → strand odds ratio
- hard filtering — використовує → mapping quality
- hard filtering — використовує → rank sum test
- rank sum test — застосовується до → mapping quality
- quality by depth — використовує → read depth
- strand odds ratio — рекомендований для → exon
- hard filtering — рекомендований для → gene panel  [КРОС-ЗВ'ЯЗОК: Поєднує контроль якості з типом тесту: для малих панелей (і немодельних організмів) доводиться використовувати hard filtering.]
- variant quality score recalibration — потребує → genetic variant
- breast cancer — є різновидом → hereditary cancer
- ovarian cancer — є різновидом → hereditary cancer
- pathogenic variant — підвищує ризик → hereditary cancer  [КРОС-ЗВ'ЯЗОК: Зв'язує геномну гілку з клінічною: патогенний варіант (BRCA1/BRCA2) підвищує ризик спадкового раку.]
- BRCA1 — підвищує ризик → breast cancer
- BRCA2 — підвищує ризик → ovarian cancer
- relative — є родичем → proband
- genetic testing — виявляє → pathogenic variant  [КРОС-ЗВ'ЯЗОК: Клінічне тестування виявляє той самий тип варіантів, що аналізують у геномному конвеєрі.]
- cascade testing — є різновидом → genetic testing
- cascade testing — застосовується до → relative
- cascade testing — потребує → pathogenic variant  [КРОС-ЗВ'ЯЗОК: Каскадне тестування можливе лише коли в пробанда вже відомий патогенний варіант.]
- genetic counseling — рекомендований для → relative
- genetic counseling — використовує → family history
- risk assessment — використовує → family history
- risk assessment — застосовується до → proband
- genetic testing — застосовується до → proband
- quality by depth — має приклад → QD < 2
- Fisher strand bias — має приклад → FS > 60 (SNP)
- strand odds ratio — має приклад → SOR > 3
- mapping quality — має приклад → MQ < 40
- relative — має приклад → рідний брат/сестра: 50%
- relative — має приклад → двоюрідний родич: до 12,5%

## Карта B

Поняття: hard filtering; variant filtering; variant quality score recalibration; quality by depth; Fisher strand bias; strand odds ratio; mapping quality; QD < 2 (приклад); read depth; sequencing read; rank sum test; allele; variant calling; VCF file; genetic variant; SOR > 3 (приклад); MQ < 40 (приклад); FS > 60 (приклад); germline variant; BRCA1; breast cancer; ovarian cancer; BRCA2; hereditary cancer; cascade testing; relative; proband; genetic testing; genetic counseling; risk assessment

Пропозиції (s — відношення → o):
- hard filtering — є різновидом → variant filtering
- variant quality score recalibration — є різновидом → variant filtering
- hard filtering — використовує → quality by depth
- hard filtering — використовує → Fisher strand bias
- hard filtering — використовує → strand odds ratio
- hard filtering — використовує → mapping quality
- quality by depth — має приклад → QD < 2
- quality by depth — використовує → read depth
- mapping quality — застосовується до → sequencing read
- rank sum test — використовує → mapping quality
- rank sum test — застосовується до → allele
- variant calling — створює → VCF file
- variant quality score recalibration — використовує → VCF file
- hard filtering — застосовується до → genetic variant
- variant quality score recalibration — потребує → genetic variant
- strand odds ratio — має приклад → SOR > 3
- mapping quality — має приклад → MQ < 40
- Fisher strand bias — має приклад → FS > 60
- hard filtering — використовує → rank sum test
- hard filtering — застосовується до → germline variant
- variant quality score recalibration — рекомендований для → germline variant
- genetic variant — має показник → Fisher strand bias
- genetic variant — має показник → strand odds ratio
- genetic variant — має показник → quality by depth
- BRCA1 — підвищує ризик → breast cancer
- BRCA1 — підвищує ризик → ovarian cancer
- BRCA2 — підвищує ризик → breast cancer
- BRCA2 — підвищує ризик → ovarian cancer
- BRCA1 — підвищує ризик → hereditary cancer
- genetic variant — підвищує ризик → hereditary cancer
- cascade testing — застосовується до → relative
- cascade testing — виявляє → genetic variant
- cascade testing — виявляє → BRCA1
- cascade testing — виявляє → BRCA2
- relative — є родичем → proband
- genetic testing — рекомендований для → breast cancer
- genetic testing — рекомендований для → ovarian cancer
- genetic testing — виявляє → BRCA1
- genetic testing — виявляє → BRCA2
- genetic counseling — застосовується до → relative
- genetic counseling — створює → risk assessment

## Карта C

Поняття: genetic variant; variant calling; VCF file; variant annotation; variant filtering; hard filtering; variant quality score recalibration; known variant resources; quality by depth; Fisher strand bias; strand odds ratio; mapping quality; rank sum test; data quality; gene panel; BRCA1; BRCA2; pathogenic variant; germline variant; hereditary cancer; breast cancer; ovarian cancer; proband; relative; first-degree relative; second-degree relative; third-degree relative; genetic testing; cascade testing; genetic counseling; risk assessment; family history; autosomal dominant inheritance; informed consent; carrier probability; QD < 2 (приклад); FS > 60 (приклад); SOR > 3 (приклад); MQ < 40 (приклад); 50 % (приклад); 25 % (приклад); 12,5 % (приклад)

Пропозиції (s — відношення → o):
- variant calling — створює → VCF file
- genetic variant — має показник → quality by depth
- genetic variant — має показник → Fisher strand bias
- genetic variant — має показник → strand odds ratio
- genetic variant — має показник → mapping quality
- genetic variant — має показник → rank sum test
- variant annotation — створює → quality by depth
- hard filtering — є різновидом → variant filtering
- variant quality score recalibration — є різновидом → variant filtering
- variant filtering — застосовується до → VCF file
- hard filtering — використовує → quality by depth
- hard filtering — використовує → Fisher strand bias
- hard filtering — використовує → strand odds ratio
- hard filtering — використовує → mapping quality
- hard filtering — використовує → rank sum test
- variant quality score recalibration — потребує → known variant resources
- quality by depth — має приклад → QD < 2
- Fisher strand bias — має приклад → FS > 60
- strand odds ratio — має приклад → SOR > 3
- mapping quality — має приклад → MQ < 40
- BRCA1 — є складовою → gene panel
- BRCA2 — є складовою → gene panel
- germline variant — є різновидом → genetic variant
- pathogenic variant — є різновидом → genetic variant
- pathogenic variant — підвищує ризик → hereditary cancer
- pathogenic variant — підвищує ризик → breast cancer
- pathogenic variant — підвищує ризик → ovarian cancer
- genetic testing — виявляє → pathogenic variant
- genetic testing — рекомендований для → breast cancer
- genetic testing — рекомендований для → ovarian cancer
- cascade testing — є різновидом → genetic testing
- cascade testing — застосовується до → relative
- relative — є родичем → proband
- first-degree relative — є різновидом → relative
- second-degree relative — є різновидом → relative
- third-degree relative — є різновидом → relative
- first-degree relative — має приклад → 50 %
- second-degree relative — має приклад → 25 %
- third-degree relative — має приклад → 12,5 %
- cascade testing — рекомендований для → first-degree relative
- genetic counseling — рекомендований для → cascade testing
- cascade testing — потребує → informed consent
- risk assessment — використовує → family history
- risk assessment — використовує → autosomal dominant inheritance
- risk assessment — створює → carrier probability
- carrier probability — застосовується до → relative
- data quality — застосовується до → VCF file
- variant filtering — рекомендований для → data quality
- hard filtering — застосовується до → pathogenic variant  [КРОС-ЗВ'ЯЗОК: Поріг, що відкидає варіант, може викинути справжній BRCA-варіант (хибнонегативний) або залишити артефакт; тому пороги лінійні й мають бути поблажливими.]
- cascade testing — потребує → pathogenic variant  [КРОС-ЗВ'ЯЗОК: Каскадне тестування запускається лише після надійно підтвердженого варіанта пробанда, тож якість фільтрації прямо визначає, чи і кого тестуватимуть.]
- hard filtering — рекомендований для → gene panel  [КРОС-ЗВ'ЯЗОК: BRCA1/BRCA2 лежать у малій панелі, де VQSR неможливий через брак варіантів, тому саме жорстка фільтрація є вимушеним вибором.]
- genetic testing — використовує → VCF file  [КРОС-ЗВ'ЯЗОК: Результат тесту є відфільтрованим VCF, тож якість анотацій переходить у клінічний висновок про варіант.]
- cascade testing — використовує → carrier probability  [КРОС-ЗВ'ЯЗОК: Ймовірність носійства (50/25/12,5 %) визначає, кого тестувати першим: найближчих родичів із найвищим шансом.]

