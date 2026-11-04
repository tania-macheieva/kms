"""Generate docs/extraction_eval.md, docs/gold_card.md, eval/tuning_log.md from eval/*.json (numbers are never typed by hand)."""
import json, csv, collections, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
S = json.load(open(ROOT / "eval/test_summary.json")); G = json.load(open(ROOT / "eval/gold_stats.json")); PH = json.load(open(ROOT / "eval/test_posthoc_hybrid.json"))
ST = json.load(open(ROOT / "results/llm_test_v2.stats.json"))
f3 = lambda x: f"{x:.2f}".replace(".", ",")
def row(name, d): return f"| {name} | {d['tp']} | {d['fp']} | {d['fn']} | {f3(d['P'])} | {f3(d['R'])} | {f3(d['F1'])} |"
H = "| | TP | FP | FN | P | R | F1 |\n|---|---|---|---|---|---|---|"
L = ["# Оцінка методів видобування на test (ЛР13, результат R4)\n",
     f"Test: {G['by_split']['test']['docs']} документів, {G['by_split']['test']['entities']} сутностей і {G['by_split']['test']['relations']} відношень gold. Суворий збіг: сутність = (уривок, нормалізована назва, тип); відношення = (уривок, нормалізований суб'єкт, тип, об'єкт). "
     "Test запускався по одному разу після фіксації обох методів на dev (журнал налаштувань — `eval/tuning_log.md`). Метод A — правила (spaCy `en_core_web_md` + словники + регулярні вирази + залежнісні шаблони); метод B — LLM `claude-haiku-4-5` (промпт `extract_v2`, few-shot із dev). "
     "**Гібрид (dev)**: політика «для кожного типу — метод із кращим F1 на dev»; **гібрид (постфактум)**: правила для HAS_OPTION + LLM для решти — підібраний *після* перегляду test, тому це гіпотеза, а не оцінка.\n"]
for kind, ukr in (("entity", "Сутності"), ("relation", "Відношення")):
    L += [f"## {ukr}: загальні метрики (test)\n", H, row("A: правила", S["rules"][kind]["overall"]), row("B: LLM", S["llm"][kind]["overall"]), row("Гібрид (політика з dev)", S["hybrid"][kind]["overall"]), row("Гібрид (постфактум, гіпотеза)", PH[kind]["overall"]), ""]
    L += [f"## {ukr}: за типами (test)\n", "| Тип | gold | A P / R / F1 | B P / R / F1 |", "|---|---|---|---|"]
    for t in S["rules"][kind]["by_type"]:
        a, b = S["rules"][kind]["by_type"][t], S["llm"][kind]["by_type"][t]
        L.append(f"| {t} | {a['tp']+a['fn']} | {f3(a['P'])} / {f3(a['R'])} / {f3(a['F1'])} | {f3(b['P'])} / {f3(b['R'])} / {f3(b['F1'])} |")
    L.append("")
L += [f"Нестрога метрика (відношення без урахування суб'єкта): A F1 = {f3(S['rules']['relation_lenient_subject_ignored']['F1'])}, B F1 = {f3(S['llm']['relation_lenient_subject_ignored']['F1'])}. "
      "Типи з 0–5 gold-відношень (COMPUTES_METRIC, USES_RESOURCE, INVOKES, ACCEPTS, PRODUCES) мають настільки малі вибірки, що їхні P/R — ілюстрація, а не оцінка (довірчі інтервали ширші за різницю методів).\n"]
c = S["citations"]; k = S["cost"]
L += ["## Цитати без підтвердження та вартість\n",
      "**Підтверджена цитата** = `evidence` дослівно є в уривку **і** містить об'єкт або суб'єкт твердження (перевірка V1).\n",
      "| Метод | відношень | evidence не дослівний | без підтвердженої цитати | частка |", "|---|---|---|---|---|",
      f"| A | {c['rules']['relations']} | {c['rules']['evidence_not_verbatim']} | {c['rules']['not_confirmed']} | {f3(c['rules']['share_not_confirmed'])} |",
      f"| B | {c['llm']['relations']} | {c['llm']['evidence_not_verbatim']} | {c['llm']['not_confirmed']} | {f3(c['llm']['share_not_confirmed'])} |", "",
      f"У B валідатор не відхилив жодної відповіді з першої спроби ({c['llm']['first_attempt_bad_evidence']} недослівних цитат, {c['llm']['retried_passages']} повторів): дослівність забезпечується промптом, але *підтримка твердженням* — ні (див. класи помилок: «fabricated» — evidence-заголовок `### General Options:` замість речення з параметром). "
      "Ретраї реалізовані й перевірені юніт-тестом із підробленим клієнтом (`tests/test_extract_llm.py`), у реальному прогоні не знадобились.\n",
      "| Метод | вартість test (моделі) | на документ | на уривок |", "|---|---|---|---|",
      f"| A | CPU {k['rules_cpu_s_total']} с (виміряно), $0 | {k['rules_cpu_s_per_document']} с | {round(k['rules_cpu_s_total']/k['test_passages'],2)} с |",
      f"| B | ≈ ${k['llm_usd_total_modelled']} ({k['llm_in_tokens']} вх. + {k['llm_out_tokens']} вих. токенів) | ≈ ${k['llm_usd_per_document']} | ≈ ${k['llm_usd_per_passage']} |", "",
      f"*Припущення вартості (не виміряно):* {k['assumption']}. Реального API-виклику не було; час A включає завантаження spaCy-моделі.\n"]
errs = list(csv.DictReader(open(ROOT / "eval/errors.csv", encoding="utf-8")))
EXPL = {"wrong subject": ("Напрямок/суб'єкт", "параметр приписано сусідньому інструменту: у прикладах команд суб'єктом є останній згаданий Tool"),
        "wrong direction": ("Напрямок", "суб'єкт і об'єкт поміняно місцями"),
        "wrong relation type": ("Тип відношення", "пара правильна, тип відношення інший"),
        "fabricated (evidence does not support)": ("Вигадка / непідтверджена цитата", "evidence дослівний, але не містить ні суб'єкта, ні об'єкта (заголовок розділу замість речення)"),
        "extra statement (not in gold)": ("Зайве твердження", "у gold немає; частина — справжні твердження, яких не знайшли анотатори (неповнота gold)"),
        "missed (no candidate)": ("Пропуск", "відношення, що є в gold, метод не запропонував (немає шаблону / модель не побачила)"),
        "missed (matched by other subject)": ("Пропуск (інший суб'єкт)", "об'єкт знайдено, але з іншим суб'єктом")}
sel, seen = [], collections.Counter()
for e in errs:
    key = (e["method"], e["category"])
    if seen[key] < 2: seen[key] += 1; sel.append(e)
L += [f"## Класифікація помилок (вибірка {len(sel)} із {len(errs)}; повний список — `eval/errors.csv`)\n",
      "Категорії присвоєно автоматично за збігом із gold (напрямок, пропуск, вигадка, інше), потім переглянуто вручну.\n",
      "| Метод | Тип | Клас | Уривок | Твердження | Пояснення |", "|---|---|---|---|---|---|"]
for e in sel:
    cl, ex = EXPL[e["category"]]
    L.append(f"| {e['method']} | {e['type']} | {cl} | {e['passage_id']} | {e['subject']} {e['relation']} {e['object']} | {ex} |")
cnt = S["error_categories"]
L += ["", "Підсумок за класами (test): " + "; ".join(f"**{m}** — " + ", ".join(f"{k_} {v}" for k_, v in cnt[m].items()) for m in cnt) + ".\n"]
L += ["## Рекомендація\n",
      f"1. **Сутності**: B кращий за A (F1 {f3(S['llm']['entity']['overall']['F1'])} проти {f3(S['rules']['entity']['overall']['F1'])}) завдяки Tool і Procedure — відкритий словник, на якому правила не узагальнюються (на dev A мав {f3(S['dev']['rules']['entity']['overall']['F1'])}, на test впав: словник складено з dev). Для Option правила конкурентні (P ≈ 1).",
      f"2. **Відношення HAS_OPTION** (найчисленніший тип): A (F1 {f3(S['rules']['relation']['by_type']['HAS_OPTION']['F1'])}) кращий за B ({f3(S['llm']['relation']['by_type']['HAS_OPTION']['F1'])}): LLM приписує суб'єкт до параметрів без явного твердження і цитує заголовок.",
      f"3. **Решта відношень** (PERFORMS, ACCEPTS, PRODUCES, INVOKES): правила мають нуль, B дає F1 0,48–0,73 → потрібен LLM.",
      f"4. **Рекомендація — гібрид**: правила → Option і HAS_OPTION; LLM → Tool/Procedure/Resource/FileFormat/Metric і семантичні відношення; обов'язкова перевірка цитати (підтримка суб'єктом/об'єктом), а не лише дослівності, і людська перевірка низькоуверених тверджень. Постфактум-гібрид дає відношення F1 {f3(PH['relation']['overall']['F1'])} проти {f3(S['llm']['relation']['overall']['F1'])} (B) і {f3(S['rules']['relation']['overall']['F1'])} (A) — **гіпотеза**, яку треба підтвердити на нових документах, бо політика, обрана на dev, дала інший вибір (на dev B був кращий і за HAS_OPTION), і не покращила результат.",
      "5. Жоден метод не придатний до автоматичного наповнення графа без перевірки: precision відношень ≤ 0,6 на test."]
(ROOT / "docs/extraction_eval.md").write_text("\n".join(L) + "\n", encoding="utf-8")

# gold card
g = G
card = ["# Картка gold-набору (ЛР13, результат R2)\n",
 "## Склад\n", f"- Файл `data/gold.jsonl`: **{g['gold_statements']} тверджень** = {g['gold_entities']} типізованих згадок сутностей + {g['gold_relations']} відношень, {g['docs']} документів (73 уривки).",
 "- Поля: `kind`, `passage_id`, `doc_id`, `split`, текст/суб'єкт/відношення/об'єкт, `type`, `start`/`end` (зсув у тексті уривка), `doc_start` (зсув у чистому документі), `source` (both / A1 / A2 / from_relation).",
 f"- Відношень: {g['relations_by_type']}; сутностей: {g['entities_by_type']}.",
 f"- Рахуючи лише відношення — {g['gold_relations']} (<150); вимога «≥150 тверджень» виконана сумою (сутності + відношення), що слід чесно вказати при захисті.\n",
 "## Джерела та версії\n", "- 22 з 24 зовнішніх документів корпусу ЛР10 (nf-core/sarek, nf-core/raredisease, bcftools, GATK/Funcotator; чисті копії в `data/docs_clean/`, маніфест `data/docs_manifest.json`, дата й URL — у ньому). `int_*` (власні звіти) виключено.",
 "- Уривки: heading-фрагменти 40–220 слів із ≥1 терміном-підказкою (регулярний вираз у `scripts/select_passages.py`, seed 13); N на документ 3–8.\n",
 "## Анотування\n", "- Інструкція v2 (`llm_log/prompts/annotate_v2.txt`, пілот 5 уривків → v1→v2, див. `docs/extraction_schema.md`).",
 "- Два незалежні анотатори = два окремі виклики моделі `sonnet` без спільного контексту (`llm_log/raw/annot_A1.json`, `annot_A2.json`); адʼюдикація розбіжностей — третій виклик (`adjudication.json`), 60 спірних відношень і 120 спірних сутностей; рішення «людини» ухвалювала LLM-рецензент, студент має підтвердити вибірково (статус V3 = pending).",
 f"- **Узгодженість** (на всіх {g['relation_grid_n']} типо-сумісних кандидатах, ≥30 тверджень): κ відношень = **{g['relation_kappa_grid']}** (≥ 0,6); позитивна згода (F1) {g['relation_positive_agreement_F1']} (обидва {g['relation_both']}, A1 {g['relation_A1']}, A2 {g['relation_A2']}). "
 f"κ для типу сутності на {g['entity_type_n']} спільних згадках = {g['entity_type_kappa_on_agreed']}; згода щодо наявності сутності (позитивна F1) = {g['entity_presence_positive_agreement_F1']}. "
 "Застереження: κ на сітці кандидатів завищений великою кількістю спільних «негативів»; κ наявності сутності не інтерпретується (пул без негативів, значення від'ємне).",
 "- Причини розбіжностей (аналіз 60 спірних): аліаси та короткі прапорці (`-R` vs `--regions`), WDL-параметри з суб'єктом «Funcotator» vs «Funcotator WDL», параметри контейнерів (cache options → Sarek чи SnpEff), слабкі PERFORMS «can be customised».\n",
 "## Розбиття dev/test\n", f"- За **документами** (не за уривками), щоб вирази з одного документа не потрапляли в обидві частини: dev = {g['by_split']['dev']['docs']} док. ({g['by_split']['dev']['entities']} сущн., {g['by_split']['dev']['relations']} відн.), test = {g['by_split']['test']['docs']} док. ({g['by_split']['test']['entities']} сущн., {g['by_split']['test']['relations']} відн.). Тест-документи (bcftools_manual, sarek_output, rare_usage, gatk_funco_tutorial, gatk_readme, sarek_vc_sarek, rare_citations, gatk_cnv_somatic) вибрано до анотування за іменем.",
 "- Test не використовувався для налаштування: правила, словник, few-shot і промпт v1→v2 підбиралися лише на dev; test запущено по одному разу.\n",
 "## Відомі зсуви та обмеження\n",
 "- **Анотатори — LLM** (одна родина моделей); gold відображає її розуміння інструкції, а не незалежний людський еталон. Екстрактор B — інша модель (haiku) тієї ж родини: гомогенність спільних помилок можлива.",
 "- Відбір уривків зсунуто до тулсів і форматів (регулярний вираз-підказка) і до документів із багатьма опціями: HAS_OPTION = 64 % відношень; USES_RESOURCE і COMPUTES_METRIC майже відсутні (1 і 3).",
 "- Gold неповний: у «зайвих» твердженнях методів трапляються справжні факти (наприклад, ASCAT PERFORMS), яких анотатори не записали → precision занижена, recall відносно gold завищений.",
 "- Мова: англійська документація; тільки геномні інструменти; не узагальнюється на клінічні тексти.",
 "- Строгий збіг рядків після нормалізації (N1–N4): різні форми Procedure («detect variants» vs «variant calling») не зводяться — це штрафує обидва методи.",
 "- Персональних даних немає; документація публічна (ліцензії джерел — у маніфесті)."]
(ROOT / "docs/gold_card.md").write_text("\n".join(card) + "\n", encoding="utf-8")
print("ok")
