"""Write claims/claims.csv + claims/README.md (claims made in the report, their sources, verification level and status)."""
import csv, collections, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
C = [
("fact","GATK README (gatk_readme#h001) requires Java 17 to run/build GATK","gatk_readme#h001","V1","verified","текст чанка перевірено вручну"),
("fact","Funcotator tutorial (gatk_funco_tutorial#h035) states Java 1.8","gatk_funco_tutorial#h035","V1","verified","текст чанка перевірено"),
("hypothesis","Java 1.8 у tutorial застаріле порівняно з README (старіша сторінка)","gatk_funco_tutorial#h035; gatk_readme#h001","V3","pending","дата чанка = дата завантаження, не публікації; потрібна перевірка людиною"),
("fact","hg19, b37, GRCh37 НЕ взаємозамінні (різні референси)","gatk_funco_refdiff#h000","V1","verified","прямо сказано в документі сховища"),
("rule","hg19/b37/GRCh37 пов'язуються як skos:closeMatch, не exactMatch","gatk_funco_refdiff#h002,#h003","V3","pending","рішення запропоновано асистентом; схвалення власника очікується"),
("hypothesis","GRCh38.GATK — інший запис того самого ключа sarek, що й GATK.GRCh38","sarek_usage#h001; sarek_usage#h059","V3","pending","з пам'яті моделі + тексту двох чанків; V3 не пройдено"),
("rule","CT-01 (minTestingAge=18) застосовано до Sofiia (17 р.) — порушення правила","graph CSV; shapes.ttl S14","V2","verified","SHACL S14: 1 порушення на baseline, 0 після виправлення"),
("rule","Вендорські пороги QD<2.0, FS>60, SOR>3 лишаються типовими; локальні 1.5/45/4 — альтернативи зі scope","store/graph Threshold; fixtures","V3","pending","рішення власника очікується (decisions.csv)"),
("fact","Фікстури fx_* — синтетичні нотатки ЛР11, а не реальні джерела","store/fixtures.json","V1","verified","задокументовано в ЛР11 і conflicts.md"),
("fact","Золотий набір: 150 пар + 10 проб; бінарна kappa=0.968, 3-класова kappa=0.905","eval/pairs_agreement.json","V4","verified","обчислено build_pairs_gold.py"),
("fact","17 пар-дублікатів у золотому наборі (9 dev / 8 test)","quality/pairs_gold.csv","V4","verified","підраховано"),
("hypothesis","PR102 (sarek_usage#h017 vs rare_usage#h029) — не дублікат, а RELATED","llm_log/raw/pairs_adjudication.json","V3","pending","L1=RELATED, L2=DUP; арбітраж асистента, не студента"),
("fact","Поріг 0.975 підібрано на dev; test P=1.0, R=0.75 (8 дублікатів)","eval/dedup_eval.json","V4","verified","95% ДІ для R [0.38; 1.0] — широкий"),
("fact","Повний конвеєр (правило+суддя) на gold: P=R=1.0 на dev і test","eval/dedup_eval_judge.json","V4","verified","суддя сліпий до gold, але та сама родина моделей; не незалежна оцінка"),
("fact","Злито 14 чанків у 11 кластерах (688→674); unmerge відновлює оригінал","eval/dedup_apply.json; тест Q12","V2","verified","перевірено на всіх кластерах"),
("hypothesis","Пояснення судді для 5 DUP-пар (JP003/4/6/7/8) правильні","llm_log/raw/pairs_judge.json","V3","pending","12 точних збігів тексту підтверджено правилом; 5 суддівських — LLM"),
("fact","M08 0.0203→0; M03 8→0; M04 1→0; M14 0.9404→0.957","quality/metrics_*.json","V4","verified","profile.py"),
("fact","Експертна вибірка 36 записів: 23/36 повністю коректні (0.639) до і після ремонту","llm_log/raw/accuracy_expert*.json","V3","pending","експерт — LLM; потрібна вибіркова перевірка людиною"),
("fact","Гейт: baseline 9 блокуючих збоїв, після 0; 2 попередження (M06, M14)","quality/gate_report_*.json","V2","verified","запуск gate.py"),
("fact","Три внесені дефекти (дубль чанка, порушення віку, ребро без provenance) виявлено","eval/defect_injection.json","V2","verified","кожен ловиться щонайменше однією перевіркою"),
("fact","RAG до/після: faithfulness 0.9889→0.9885, context recall 0.98→0.98, conflict_detected 1.0→1.0","eval/rag_comparison.json","V4","verified","5 змінених відповідей — новий суддя; 29 — вердикти ЛР11"),
("hypothesis","Реєстр альтернатив покращує поведінку RAG на конфліктах","eval/results_after.json","V4","rejected","не підтверджено: відповідь і до, і після — CONFLICT; один прогін не відокремлює ефект від шуму"),
("fact","Ретрівальний пробник: зайвих слотів top-5 17/55 → 0/55","eval/probe_dups.json","V4","verified","запити — уривки самих чанків (зміщення на користь знаходження)"),
("fact","Експертні вердикти meta_ok=false для 2 поглинутих записів (id не збігається з вмістом)","llm_log/raw/accuracy_expert_after.json","V3","rejected","артефакт моєї побудови входу (id оригіналу + вміст канонічного чанка); вхід виправлено, огляд повторено"),
("hypothesis","Мітка DUP для PR102 від анотатора L2","llm_log/raw/pairs_L2_b3.json","V3","rejected","в A є додатковий абзац (MultiQC-звіти), якого немає в B — інформація різна"),
]
rows = [(f"CL{i:02d}", c[1], c[0], c[2], c[3], c[4], c[5]) for i, c in enumerate(C, 1)]
w = csv.writer(open(ROOT / "claims/claims.csv", "w", newline="", encoding="utf-8")); w.writerow(["id", "claim", "type", "source", "verification_level", "status", "comment"]); w.writerows(rows)
n = len(rows); c = collections.Counter(r[5] for r in rows)
open(ROOT / "claims/README.md", "w", encoding="utf-8").write(f"""# Таблиця тверджень (ЛР14)
Усього {n}; verified {c['verified']} ({c['verified']/n:.0%}), pending {c['pending']}, rejected {c['rejected']} (пояснення — у стовпці comment).
Рівні: V1 — джерело (текст у сховищі), V2 — SHACL/тести, V3 — експерт/суддя (LLM; схвалення людини очікується), V4 — метрики до/після.
Частка «verified» не означає перевірку людиною: V3-твердження лишаються pending до схвалення студентом.
Джерела: документація GATK, bcftools, nf-core/sarek, nf-core/raredisease (`store/docs_clean/`); синтетичні фікстури ЛР11; граф ЛР9.
""")
print(n, dict(c), round(c["verified"] / n, 2))
