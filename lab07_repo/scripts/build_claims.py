"""claims/claims.csv + llm_log/log.csv. Цитати перевіряються в sources/*.txt (V1); V2 — перевірка інструментами; V3 — збіг із незалежним джерелом; V4 — людина (поки немає)."""
import csv
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def norm(t):
    t = unicodedata.normalize("NFKC", t).lower().replace("–", "-").replace("—", "-").replace("−", "-")
    return re.sub(r"\s+", " ", re.sub(r"[^\w<>=.%\- ]", " ", t)).strip()


TXT = {"gatk": norm((ROOT / "sources/gatk_hard_filtering.txt").read_text(encoding="utf-8")), "cdc": norm((ROOT / "sources/cdc_cascade_testing.txt").read_text(encoding="utf-8"))}
SRC = {"gatk": "sources/gatk_hard_filtering.txt", "cdc": "sources/cdc_cascade_testing.txt"}
# (claim, type, src, quote, level_if_quote_ok, status_if_ok, comment)
Q = [
 ("Поріг QD < 2 для прапорця LowQD", "факт", "gatk", "filter out variants with QD below 2", "V2", "verified", "цитата є; HermiT виводить LowQDVariant для VAR-002 (QD 1.5) і не виводить для VAR-001 (QD 25)"),
 ("Поріг FS > 60 для SNP", "факт", "gatk", "FS>60.0", "V2", "verified", "цитата є; HermiT виводить HighFSSnpVariant для VAR-004 (FS 62)"),
 ("Поріг SOR > 3", "факт", "gatk", "SOR>3.0", "V1", "verified", "цитата є; не змодельовано як окремий означений клас (лише в об'єднанні FlaggedVariant)"),
 ("Поріг MQ < 40", "факт", "gatk", "fail any variant with an MQ value less than 40.0", "V1", "verified", "цитата є"),
 ("Поріг MQRankSum < −12,5", "факт", "gatk", "MQRankSum < -12.5", "V1", "verified", "цитата є"),
 ("Поріг ReadPosRankSum < −8", "факт", "gatk", "ReadPosRankSum value less than -8.0", "V1", "verified", "цитата є"),
 ("Будь-яке значення поза порогом → варіант відкидається", "правило", "gatk", "throwing out any variants that have annotation values above or below the set thresholds", "V2", "verified", "реалізовано як FlaggedVariant ≡ об'єднання порогів; CQ10 проходить"),
 ("VQSR потребує великого набору варіантів і відомих ресурсів", "правило", "gatk", "requires a large number of variants and well-curated known variant", "V1", "verified", "аксіоми VQSR ⊑ ∃requires.LargeVariantSet / CuratedKnownVariants; CQ05"),
 ("SOR створено, бо FS штрафує варіанти на кінцях екзонів", "правило", "gatk", "SOR was created because FS tends to penalize variants that occur at the ends of exons", "V1", "verified", "аксіома StrandOddsRatio ⊑ ∃recommendedFor.ExonEndVariant; CQ07"),
 ("Шанс успадкування для родичів першого ступеня — 50%", "факт", "cdc", "1 in 2 (50%) chance", "V2", "verified", "FirstDegreeRelative ⊑ hasInheritanceProbability 0.5; CQ11"),
 ("Шанс успадкування для родичів другого ступеня — 25%", "факт", "cdc", "1 in 4 (25%) chance", "V2", "verified", "CQ12"),
 ("Шанс успадкування для родичів третього ступеня — 12,5%", "факт", "cdc", "1 in 8 (12.5%) chance", "V2", "verified", "верхня межа («до 12,5%»); CQ13"),
 ("Тестування лише дорослих (≥ 18 років)", "правило", "cdc", "should only be done on adults (18 years of age and older)", "V2", "verified", "AdultRelative/MinorRelative; HermiT виводить MinorRelative для Sofiia (17); CQ15; виняток для ризиків раку в дитинстві не змодельовано"),
 ("Тестування починають із найближчих родичів", "правило", "cdc", "genetic testing should start with family members who are most closely related", "V1", "verified", "CascadeTesting ⊑ ∃recommendedFor.FirstDegreeRelative; CQ14"),
]
rows = []
for c, t, s, q, lvl, st, com in Q:
    ok = norm(q) in TXT[s]
    rows.append((c, t, SRC[s], lvl if ok else "V0", st if ok else "pending", com if ok else "цитату не знайдено в тексті"))
rows += [
 ("Поріг FS > 200 для INDEL", "факт", "коментар читача до статті GATK (не основний текст)", "V0", "pending", "значення з коментаря; змодельовано (HighFSIndelVariant), але потребує перевірки за документацією GATK (V4)"),
 ("hard filtering рекомендовано для малої панелі генів", "правило", "карта ЛР6 v2 (експерт); gatk", "V3", "pending", "аксіома HardFiltering ⊑ ∃recommendedFor.GenePanel; CQ08; у тексті прямої цитати «для панелей» немає — потрібна перевірка"),
 ("Ланцюг hasParent∘hasSibling = родич другого ступеня (тітка/дядько)", "правило", "загальне знання генетики/родоводу (джерела не цитовано)", "V2", "pending", "HermiT виводить Halyna ∈ SecondDegreeRelative; для зведених родичів нюанси ймовірності; потрібна перевірка фахівцем (V4)"),
 ("Двоюрідний родич — третього ступеня (ланцюг hasAuntOrUncle∘hasChild)", "правило", "cdc (2: «third-degree relative»); загальне знання", "V2", "pending", "HermiT виводить Andrii ∈ ThirdDegreeRelative"),
 ("Proband і Relative — диз'юнктні класи", "гіпотеза", "моделювання (рішення автора)", "V2", "pending", "перевірено лише узгодженістю; у реальних родоводах особа може бути пробандом в одній сім'ї й родичем в іншій"),
 ("Person ⊑ hasParent ≤ 2", "факт", "біологія (загальне знання)", "V2", "verified", "навмисна суперечність 2 показує реакцію HermiT; джерела не цитовано — але твердження загальновідоме"),
 ("Означення 77 класів за схемою «рід + відмінність» коректні", "гіпотеза", "чернетка LLM, правлена автором", "V2", "pending", "перевірено форму й відсутність циклів (скрипт), зміст не перевірено експертом (V4)"),
 ("Зіставлення з MeSH (gene, SNP, genetic counseling, breast/ovarian cancer)", "факт", "MeSH Lookup API (ЛР5)", "V2", "pending", "URI й мітки підтверджено в ЛР5; смислову еквівалентність оцінила LLM"),
 ("Чернетка LLM: part_of/derived_from транзитивні, is_kin_of симетрична", "факт", "llm_log/raw/step_llm_draft_notes_raw.md", "V2", "rejected", "у файлі чернетки характеристика записана як значення rdfs:label, тобто не оголошена (0 транзитивних, 0 симетричних)"),
 ("Чернетка LLM: «BRCA1_gene increases_risk_of Olena_breast_cancer»", "факт", "llm_log/raw/step_llm_draft_raw_output.ttl", "V3", "rejected", "ген не підвищує ризик конкретного випадку раку; носій ризику — патогенний варіант (змішування гена й варіанта)"),
 ("Чернетка LLM: gene panel — підклас Genomic element", "факт", "llm_log/raw/step_llm_draft_raw_output.ttl", "V3", "rejected", "панель — спроєктований набір (артефакт), а не біологічний елемент (OntoClean)"),
 ("Чернетка LLM: BRCA1 і BRCA2 — класи", "факт", "llm_log/raw/step_llm_draft_raw_output.ttl", "V3", "rejected", "це конкретні гени, тобто індивіди; клас з одним індивідом свідчить про змішування типу й екземпляра"),
 ("Чернетка LLM: object-властивості мають domain/range", "факт", "llm_log/raw/step_llm_draft_notes_raw.md", "V2", "rejected", "32 з 32 властивостей без domain або range (перевірено скриптом eval_onto.py)"),
]
with open(ROOT / "claims/claims.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f); w.writerow(["id", "claim", "type", "source", "verification_level", "status", "comment"])
    for i, r in enumerate(rows, 1): w.writerow([f"C{i:03d}", *r])
n = len(rows); ver = sum(r[4] == "verified" for r in rows); rej = sum(r[4] == "rejected" for r in rows)
(ROOT / "claims/README.md").write_text(f"""# claims.csv — реєстр тверджень, отриманих від LLM

Тип: факт / правило / гіпотеза. Рівні: **V0** — не перевірено; **V1** — дослівна цитата знайдена в тексті джерела (скрипт); **V2** — перевірено інструментом (HermiT, CQ-запит, парсер) і/або цитатою;
**V3** — збіг із незалежним джерелом чи експертною картою; **V4** — підтверджено людиною за першоджерелом (**жодного V4 ще немає**).
Статуси: verified / rejected / pending.

Підсумок: усього {n}; verified {ver} ({ver/n:.0%}); rejected {rej} (пояснено в `comment`); pending {n-ver-rej}.
Відхилені твердження — це помилки чернетки LLM; pending — потребують перевірки людиною.
""", encoding="utf-8")
LOG = [
 ("l7-s1", "Пропозиція класів, властивостей, аксіом, індивідів і шаблонів ситуацій (основна сесія)", "interactive (без версіонування; скрипти scripts/onto_model.py, build_onto.py, build_data.py)", "scripts/onto_model.py; scripts/build_onto.py; scripts/build_data.py; data/situations_src.py", "ввела людина: рішення про склад класів; перевірено HermiT і тестами"),
 ("l7-s2", "Чернетка онтології за таксономією й картою (наосліп, окремий запуск)", "draft_prompt_v1 (llm_log/prompts/l7_draft_prompt_v1.md)", "llm_log/raw/step_llm_draft_raw_output.ttl; llm_log/raw/step_llm_draft_notes_raw.md", "використано як об'єкт порівняння; взято isDeceased, решту відхилено (docs/onto_eval.md)"),
]
with open(ROOT / "llm_log/log.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f); w.writerow(["step", "task", "date", "model", "temperature_seed", "prompt_version", "raw_output", "human_decision"])
    for s, t, p, raw, dec in LOG:
        w.writerow([s, t, "2026-10-25", "claude-sonnet-5-5 (фактична модель могла відрізнятися)", "не доступні в цьому середовищі", p, raw, dec + "; очікує перегляду студентом"])
print(n, ver, rej, n - ver - rej)
