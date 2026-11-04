"""claims/claims.csv, claims/README.md, llm_log/log.csv для ЛР7.
Рівні перевірки (за завданням ЛР7): V1 — джерело/цитата; V2 — парсер + reasoner (HermiT); V3 — експерт (людина); V4 — CQ-тест.
Жодне твердження ще не має V3 (потрібен експерт-людина)."""
import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
t6 = {(r["s"], r["p"], r["o"]): r for r in csv.DictReader(open(ROOT / "models/triples_final.csv", encoding="utf-8-sig"))}
cmp = json.loads((ROOT / "docs/evidence/onto_compare.json").read_text(encoding="utf-8"))
cq = {r["cq"]: r for r in csv.DictReader(open(ROOT / "docs/evidence/cq_results_mine.csv", encoding="utf-8-sig"))}
rows = []


def add(claim, typ, source, level, status, comment):
    rows.append((claim, typ, source, level, status, comment))


# 1. аксіоми
MAP = {
 "HardFiltering ⊑ ∃ usesInput.QualityByDepth": ("hard filtering", "uses_input", "quality by depth", "CQ09"),
 "HardFiltering ⊑ ∃ usesInput.FisherStrandBias": ("hard filtering", "uses_input", "Fisher strand bias", "CQ09"),
 "HardFiltering ⊑ ∃ usesInput.StrandOddsRatio": ("hard filtering", "uses_input", "strand odds ratio", "CQ09"),
 "HardFiltering ⊑ ∃ usesInput.MappingQuality": ("hard filtering", "uses_input", "mapping quality", "CQ09"),
 "HardFiltering ⊑ ∃ usesInput.RankSumAnnotation": ("hard filtering", "uses_input", "rank sum test", "CQ09"),
 "VQSR ⊑ ∃ requires.LargeVariantSet": ("variant quality score recalibration", "requires", "large variant set", "CQ05"),
 "VQSR ⊑ ∃ requires.CuratedKnownVariants": ("variant quality score recalibration", "requires", "curated known variants", "CQ05"),
 "CascadeTesting ⊑ ∃ requires.PathogenicVariant": ("cascade testing", "requires", "pathogenic variant", "CQ20"),
 "CascadeTesting ⊑ ∃ recommendedFor.FirstDegreeRelative": ("cascade testing", "recommended_for", "first-degree relative", "CQ14"),
 "PathogenicVariant ⊑ ∃ increasesRiskOf.BreastCancer": ("pathogenic variant", "increases_risk_of", "breast cancer", "CQ19"),
 "PathogenicVariant ⊑ ∃ increasesRiskOf.OvarianCancer": ("pathogenic variant", "increases_risk_of", "ovarian cancer", "CQ19"),
 "HardFiltering ⊑ ∃ recommendedFor.GenePanel": ("hard filtering", "recommended_for", "gene panel", "CQ08"),
 "StrandOddsRatio ⊑ ∃ recommendedFor.ExonEndVariant": ("strand odds ratio", "recommended_for", "variant at exon end", "CQ07"),
 "CascadeTesting ⊑ ∀ appliesTo.Relative": ("cascade testing", "applies_to", "relative", "CQ14"),
}
for line in (ROOT / "docs/evidence/axioms.txt").read_text(encoding="utf-8").splitlines()[1:]:
    ax = line.strip().replace(" ⊑ ", " ⊑ ", 1)
    ax = re.sub(r"\s+", " ", ax)
    key = next((k for k in MAP if re.sub(r"\s+", " ", k) == ax), None)
    if key:
        s, p, o, q = MAP[key]; r = t6.get((s, p, o))
        st6 = r["status"] if r else "—"
        qpass = cq.get(q, {}).get("passed") == "1"
        add("Аксіома: " + ax, "правило", f"ЛР6 triples_final.csv ({st6}): " + (r["evidence"][:90] if r and r["evidence"] != "—" else "твердження експерта без цитати"),
            "V4" if qpass else "V2", "verified" if st6 == "verified" else "pending", f"HermiT: онтологія узгоджена; CQ {q} {'пройдено' if qpass else 'не пройдено'}" + ("" if st6 == "verified" else "; джерело — твердження експерта, цитати немає (потрібна перевірка V3)"))
    else:
        add("Аксіома: " + ax, "правило", "модельне рішення (не з тексту)", "V2", "verified", "HermiT: онтологія узгоджена; змістовність потребує оцінки експерта (V3)")
# 2. числові факти (з ЛР6)
for lab, trip in (("QD < 2", None), ("FS > 60 (SNP)", None), ("SOR > 3", None), ("MQ < 40", None)):
    add(f"Поріг {lab}", "факт", "GATK Hard-filtering (ЛР6 claims)", "V4" if lab[:2] in ("QD", "FS") else "V1", "verified", "цитата в тексті; CQ01/CQ02 пройдено" if lab[:2] in ("QD", "FS") else "цитата в тексті")
add("Поріг MQRankSum < −12,5; ReadPosRankSum < −8", "факт", "GATK (ЛР6 claims)", "V1", "verified", "цитата в тексті")
add("Поріг FS > 200 для INDEL", "факт", "коментар читача до статті GATK", "V4", "pending", "CQ03 технічно пройдено (значення є в онтології), але саме значення з коментаря: потрібна перевірка за документацією GATK")
for deg, prob in (("першого", "0.5"), ("другого", "0.25"), ("третього", "0.125")):
    add(f"Ймовірність успадкування для родичів {deg} ступеня = {prob}", "факт", "CDC About Cascade Testing (ЛР6 claims)", "V4", "verified", "цитата «1 in 2/4/8» у ЛР6; CQ11–CQ13 пройдено")
add("Тестування лише дорослих (≥ 18 років); виняток — ризик раку в дитинстві", "правило", "CDC About Cascade Testing", "V4", "verified", "цитата в тексті (ЛР6); у онтології — AdultRelative/MinorRelative і шаблон S06; виняток не моделюється")
# 3. ситуації
for sid, status, lvl, c in (("S01", "verified", "V4", "запит SPARQL повертає VAR-002"), ("S02", "pending", "V2", "запит не виконувався; логіка ідентична S01 для FS"), ("S03", "verified", "V4", "запит SPARQL повертає VAR-004; правило «кінець екзона → перевірити SOR» з тексту GATK"),
                            ("S04", "pending", "V2", "запит не виконувався"), ("S05", "pending", "V2", "запит не виконувався"), ("S06", "verified", "V4", "запит SPARQL повертає Sofiia")):
    add(f"Шаблон ситуації {sid} коректно описує стан-подію-guard-дію", "правило", "models/situations.csv; GATK/CDC", lvl, status, c)
# 4. висновки чернетки LLM
CL = [
 ("Чернетка LLM: part_of і derived_from транзитивні; is_kin_of, sibling_of, cousin_of симетричні; has_filter_status функціональна (з нотаток LLM)", "rejected", "V2", "у файлі ці характеристики записано як значення rdfs:label, а не як типи; rdflib/HermiT бачать 0 транзитивних і симетричних властивостей"),
 ("Чернетка LLM: усі об'єктні властивості типізовані за каталогом", "rejected", "V2", "0 з 32 мають domain; 1 із 32 має range"),
 ("Чернетка LLM: BRCA1/BRCA2 — класи", "rejected", "V3", "гени — індивіди; змішування класу та індивіда (OntoClean); оцінка автора, не експерта-людини"),
 ("Чернетка LLM: pathogenic variant — первинний підклас genetic variant", "rejected", "V3", "анти-жорсткий клас; потрібен означений клас (оцінка автора)"),
 ("Чернетка LLM: panelSize — xsd:string", "rejected", "V2", "розмір — число"),
 ("Чернетка LLM: threshold ⊑ Measure of quality; gene panel ⊑ Genomic element", "rejected", "V3", "хибні is-a (OntoClean; оцінка автора)"),
 ("Чернетка LLM: статуси FILTERED призначено явно (VAR-002, VAR-004)", "rejected", "V4", "відповіді правильні, але дублюють пороги; в моїй онтології виводяться"),
 ("Чернетка LLM: пара germline/somatic із диз'юнктністю", "verified", "V2", "взято: SomaticVariant у моїй онтології, HermiT узгоджена"),
 ("Чернетка LLM: CascadeTesting має рівно 1 пробанда", "verified", "V2", "взято: hasProband = 1; HermiT узгоджена"),
 ("Чернетка LLM: мінімальний вік тестування як data-значення", "verified", "V2", "взято: hasMinTestingAge = 18"),
]
for c, st, lvl, com in CL: add(c, "гіпотеза" if st == "rejected" else "правило", "llm_log/raw/step_llm_draft_raw_output.ttl", lvl, st, com)
add("Мої визначення класів «рід + відмінність» складено з участю LLM", "гіпотеза", "models/class_table.csv", "V1", "pending", "автоперевірка (самопосилання, цикли) пройдена; змістову точність має підтвердити експерт (V3)")
add("Повторне використання: skos:closeMatch/exactMatch до MeSH і таксономії ЛР5 доречні", "гіпотеза", "ЛР5 external_links.csv (URI перевірено MeSH Lookup API)", "V1", "pending", "існування URI й мітка перевірені в ЛР5; смислову еквівалентність оцінила LLM")
with open(ROOT / "claims/claims.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f); w.writerow(["id", "claim", "type", "source", "verification_level", "status", "comment"])
    for i, r in enumerate(rows, 1): w.writerow([f"C{i:03d}", *r])
n = len(rows); ver = sum(r[4] == "verified" for r in rows); rej = sum(r[4] == "rejected" for r in rows); pen = n - ver - rej
(ROOT / "claims/README.md").write_text(f"""# claims.csv — реєстр тверджень, отриманих від LLM (ЛР7)
Рівні перевірки (за завданням ЛР7): **V1** — джерело/цитата; **V2** — парсер rdflib + reasoner HermiT; **V3** — оцінка експерта-людини; **V4** — CQ-тест (SPARQL).
Рівень — найвищий пройдений; **V3 не досягнуто жодним твердженням** (експерта-людини не залучено; позначки «оцінка автора» — це LLM-асистент).
Статуси: verified / rejected / pending. Типи: факт / правило / гіпотеза.

Підсумок: усього {n}; verified {ver} ({ver/n:.0%}); rejected {rej}; pending {pen}. Відхилені твердження пояснено в колонці `comment`.
""", encoding="utf-8")
LOG = [("l7-draft", "Чернетка OWL-онтології за таксономією, картою, CQ і сценарієм (наосліп)", "llm_log/prompts/step_llm_draft_prompt_v1.md", "llm_log/raw/step_llm_draft_raw_output.ttl; step_llm_draft_notes.md", "використано як порівняння; 3 ідеї взято, 5+ відхилено (docs/onto_eval.md)"),
       ("l7-model", "Чернетки класів, аксіом, властивостей, ситуацій і скриптів (мій асистент у цій сесії)", "—  (інтерактивний діалог; скрипти scripts/onto_model.py, build_onto.py, build_data.py)", "scripts/*.py (сирі відповіді окремо не збережено)", "перевірено автоматично; змістовна перевірка — за студентом")]
with open(ROOT / "llm_log/log.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f); w.writerow(["step", "task", "date", "model", "temperature_seed", "prompt_version", "raw_output", "human_decision"])
    for s, t, p, raw, dec in LOG:
        w.writerow([s, t, "2026-10-25/26", "claude-sonnet-5-5 (фактична модель підагента могла відрізнятися)", "не доступні в цьому середовищі", p, raw, dec + "; очікує перегляду студентом"])
(ROOT / "llm_log/README.md").write_text("# Журнал використання LLM (ЛР7)\n`log.csv` — крок, завдання, дата, модель, параметри, підказка, сирий вихід, рішення людини. `raw/` — дослівні виходи чернетки; `prompts/` — підказка й вхідні файли. Перевірка тверджень — `../claims/claims.csv`.\n", encoding="utf-8")
print(n, ver, rej, pen)
