"""Apply the decision rule to eval/patterns.json and write docs/patterns.md + eval/patterns_rules.csv."""
import json, csv, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
d = json.load(open(ROOT / "eval/patterns.json")); R = d["rules_top40"]
def decide(r):
    why = []
    if r["perm_p_within_docs"] >= 0.01: why.append(f"chance not excluded (p={r['perm_p_within_docs']})")
    if r["boot_stable_share"] < 0.8: why.append(f"unstable (bootstrap share {r['boot_stable_share']:.2f})")
    if r["n_docs"] < 3: why.append(f"only {r['n_docs']} document(s)")
    if min(r["half_lift"]) <= 1.0: why.append("lift <= 1 in one document half")
    return ("accept", "passes chance, stability and breadth checks") if not why else ("reject", "; ".join(why))
MECH = {
 ("vep|Tool", "annotation|Procedure"): "VEP is by definition a variant-annotation tool; the documents describe it in annotation context (mechanism: the tool's function).",
 ("snpeff|Tool", "annotation|Procedure"): "Same mechanism as VEP: SnpEff is an annotation tool; confirms that the rule reflects function, not text layout.",
 ("vcfanno|Tool", "annotation|Procedure"): "vcfanno annotates VCFs with other files; mechanism = function. Caveat: the three annotation rules share one consequent and one mechanism, they are not independent evidence.",
 ("singularity|Tool", "docker|Tool"): "Both are container engines that the Nextflow-based pipelines document side by side (profiles -profile docker / singularity); mechanism = documentation boilerplate, true but low informational value (lift 12.7 is inflated by rarity).",
 ("ac|Metric", "an|Metric"): "AC (allele count) and AN (allele number) are standard INFO fields always listed together in annotation tables; mechanism = co-documentation of a field set. Only 3 documents, all GATK/Funcotator-family.",
 ("an|Metric", "ac|Metric"): "Converse of the previous rule (confidence 1.0).",
 ("raredisease|Tool", "nextflow|Tool"): "Nextflow boilerplate (run commands) in every usage chunk of the pipeline; not excluded as chance (p=0.06) and driven by 3 documents.",
 ("mutect2 multi|Tool", "funcotator|Tool"): "Artefact of one WDL document that lists both workflows in the same input table (1 document).",
 ("bcftools|Tool", "vcf|FileFormat"): "Plausible mechanism (bcftools works on VCF/BCF), but lift is only 1.7 and the rule is not stable under document resampling.",
 ("bcf|FileFormat", "vcf|FileFormat"): "One document (bcftools manual) discusses BCF and VCF together; a single-document pattern.",
 ("tabix|Tool", "vcf|FileFormat"): "Mechanism is real (tabix indexes bgzipped VCF) and p<0.001, but only 70% of bootstrap resamples keep the rule: borderline, rejected by the pre-set threshold (0.8).",
 ("deepvariant|Tool", "variant calling|Procedure"): "Mechanism real (DeepVariant is a variant caller); bootstrap share 0.71 < 0.8 -> rejected by threshold although plausible; decision may change with more documents.",
 ("filtering|Procedure", "vcf|FileFormat"): "Plausible (filters act on VCF records) but unstable under resampling and weak lift (2.0).",
}
rows = []
for r in R:
    dec, why = decide(r); r["decision"], r["why"] = dec, why; rows.append(r)
with open(ROOT / "eval/patterns_rules.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["antecedent", "consequent", "support", "n_chunks", "confidence", "lift", "n_docs", "perm_p_within_docs", "boot_stable_share", "boot_lift_p5", "boot_lift_p95", "half_lift_0", "half_lift_1", "decision", "why"])
    for r in rows: w.writerow([r["antecedent"], r["consequent"], r["support"], r["n_chunks"], r["confidence"], r["lift"], r["n_docs"], r["perm_p_within_docs"], r["boot_stable_share"], round(r["boot_lift_p5"], 2), round(r["boot_lift_p95"], 2), *r["half_lift"], r["decision"], r["why"]])
acc = [r for r in rows if r["decision"] == "accept"]; rej = [r for r in rows if r["decision"] == "reject"]
show = acc + [r for r in rej if (r["antecedent"], r["consequent"]) in MECH][:8]
L = [f"# Закономірності в графі знань (ЛР13, результат R5)\n",
     f"Дані: {d['chunks']} фрагментів (heading-chunks ЛР10, лише зовнішня документація, {d['docs']} документів), елементи — сутності методу A (Tool, FileFormat, Metric, Resource, Procedure), "
     f"ключ — нормалізована назва + тип. Алгоритм: правила з одним антецедентом, мінімум {d['min_support_chunks']} фрагментів (support ≥ {d['min_support_chunks']/d['chunks']:.3f}), confidence ≥ {d['min_conf']}, lift ≥ {d['min_lift']}; "
     f"кандидатів: **{d['n_candidate_rules']}** (таблиця — `eval/patterns_rules.csv`, топ-40 за lift·support).\n",
     "## Перевірки (як відрізнити закономірність від збігу)\n",
     "1. **Випадковість**: перестановковий тест — стовпець наслідку перемішується *всередині кожного документа* (зберігає базову частоту в документі, тож усуває ефект «документ про X»), 2000 перестановок, p = частка null-lift ≥ спостереженого.",
     "2. **Стабільність**: бутстреп за *документами* (300 повторів, документи — кластер залежності фрагментів) → частка повторів, де confidence ≥ 0,6 і lift ≥ 1,5; плюс lift у двох половинах (парні/непарні документи).",
     "3. **Широта/механізм**: правило має спиратися на ≥ 3 документи; для кожного — доменне пояснення механізму.",
     "**Правило рішення (задано до перегляду таблиці):** accept, якщо p < 0,01 І bootstrap-частка ≥ 0,8 І ≥ 3 документи І lift > 1 в обох половинах; інакше reject.\n",
     f"Підсумок: {len(acc)} прийнято, {len(rej)} відхилено з {len(rows)} перевірених.\n",
     "## Правила: метрики, перевірки, рішення\n",
     "| Правило A → B | support (фрагм.) | conf | lift | док. | p (перест.) | bootstrap | lift 2 половин | Рішення |", "|---|---|---|---|---|---|---|---|---|"]
for r in show:
    L.append(f"| {r['antecedent'].split('|')[0]} → {r['consequent'].split('|')[0]} | {r['support']:.3f} ({r['n_chunks']}) | {r['confidence']:.2f} | {r['lift']:.1f} | {r['n_docs']} | {r['perm_p_within_docs']} | {r['boot_stable_share']:.2f} | {r['half_lift'][0]:.1f} / {r['half_lift'][1]:.1f} | **{r['decision']}** |")
L += ["", "## Механізм і обґрунтування рішень\n"]
for r in show:
    m = MECH.get((r["antecedent"], r["consequent"]), "—")
    L.append(f"- **{r['antecedent'].split('|')[0]} → {r['consequent'].split('|')[0]}** — {r['decision']} ({r['why']}). {m}")
L += ["", "## Обмеження\n",
      "- Сутності цього аналізу — з методу A (правила + словник, зібраний на dev), тому словник визначає, які патерни взагалі можливі; точність A на тесті (F1 сутностей 0,59) означає шум в елементах.",
      "- Лише правила з одним антецедентом; 24 документи, деякі (sarek, bcftools) домінують; accepted-правила про анотацію мають спільний наслідок і спільний механізм — це один висновок, а не три.",
      "- «Прийнято» означає «пройшло задані перевірки на цьому корпусі», а не «закон предметної області»; AC→AN та singularity→docker істинні, але тривіальні (документаційна спільність)."]
(ROOT / "docs/patterns.md").write_text("\n".join(L) + "\n", encoding="utf-8")
print(len(acc), len(rej)); [print(r["antecedent"], r["consequent"]) for r in acc]
