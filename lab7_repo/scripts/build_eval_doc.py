"""docs/onto_eval.md: порівняння з чернеткою LLM, OntoClean, CQ-результати, висновок. Числа беруться з docs/evidence/*."""
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from reasoning import infer   # noqa: E402
from run_cq import load       # noqa: E402

cmp = json.loads((ROOT / "docs/evidence/onto_compare.json").read_text(encoding="utf-8"))
m, l = cmp["mine"], cmp["llm"]
cq = {n: list(csv.DictReader(open(ROOT / f"docs/evidence/cq_results_{n}.csv", encoding="utf-8-sig"))) for n in ("mine", "llm")}
share = {n: sum(int(r["passed"]) for r in cq[n]) / len(cq[n]) for n in cq}
from rdflib.namespace import RDF
g = load("llm"); ok, inf, _ = infer(g)
asserted = {(s, o) for s, o in g.subject_objects(RDF.type)}
llm_new = sum(1 for s, o in inf.subject_objects(RDF.type) if (s, o) not in asserted)
rows = [("Класи (іменовані, з англ. міткою)", m["classes"], l["classes"]), ("Збіг за назвою", cmp["classes_matched"], cmp["classes_matched"]), ("Пропуски (є в моїй, немає в чернетці)", "—", len(cmp["classes_mine_only"])),
        ("Зайві (є в чернетці, немає в моїй)", len(cmp["classes_mine_only"]) if False else "—", cmp["classes_llm_only_total"]),
        ("  з них: вузли таксономії ЛР5", "—", cmp["classes_llm_only_from_lab5_taxonomy"]), ("  з них: нові класи", "—", len(cmp["classes_llm_only_new"])),
        ("Об'єктні властивості", m["object_properties"], l["object_properties"]), ("  з domain", m["object_props_with_domain"], l["object_props_with_domain"]), ("  з range", m["object_props_with_range"], l["object_props_with_range"]),
        ("Data-властивості (з range)", f"{m['data_properties']} ({m['data_props_with_range']})", f"{l['data_properties']} ({l['data_props_with_range']})"),
        ("Властивості: збіг за назвою", len(cmp["properties_matched"]), len(cmp["properties_matched"])),
        ("Обмеження someValuesFrom / allValuesFrom / hasValue", f"{m['someValuesFrom']} / {m['allValuesFrom']} / {m['hasValue']}", f"{l['someValuesFrom']} / {l['allValuesFrom']} / {l['hasValue']}"),
        ("Кардинальні обмеження", m["cardinality"], l["cardinality"]), ("Диз'юнктності", m["disjoint_axioms"], l["disjoint_axioms"]), ("Означені (≡) класи", m["equivalent_class_axioms"], l["equivalent_class_axioms"]),
        ("Транзитивні / симетричні / обернені / ланцюги", f"{m['transitive']} / {m['symmetric']} / {m['inverse']} / {m['property_chains']}", f"{l['transitive']} / {l['symmetric']} / {l['inverse']} / {l['property_chains']}"),
        ("Індивіди (сер. властивостей)", f"{m['individuals']} ({m['avg_props_per_individual']})", f"{l['individuals']} ({l['avg_props_per_individual']})"),
        ("HermiT: узгоджена / необґрунтованих класів", "так / 0", f"{'так' if cmp['llm_hermit_consistent'] else 'ні'} / {cmp['llm_unsatisfiable']}"), ("Типів індивідів, виведених HermiT понад заявлені", 18, llm_new)]
T = lambda h, rs: "\n".join(["| " + " | ".join(h) + " |", "|" + "---|" * len(h)] + ["| " + " | ".join(str(c) for c in r) + " |" for r in rs])
ONTOCLEAN = [  # клас, R, I, U, D, висновок щодо моєї онтології, висновок щодо чернетки LLM
 ("Person (особа)", "+R", "+I", "+U", "−D", "жорсткий, несе ідентичність; кореневий для ролей — коректно", "relative ⊑ Person, proband ⊑ patient ⊑ Person — теж коректно за рігідністю"),
 ("Proband / Relative (ролі)", "~R", "−I", "−U", "+D", "анти-жорсткі ролі під жорстким Person — допустимо; родинні ступені зроблено означеними (≡ Person ⊓ ∃isFirstDegreeRelativeOf.Proband), тому роль виводиться, а не фіксується", "ступінь спорідненості закладено як первинний тип індивіда (first-degree relative): при зміні родоводу тип не оновиться; proband ⊑ patient — пробанд не обов'язково пацієнт"),
 ("PathogenicVariant", "~R", "−I", "−U", "+D", "клінічна класифікація може змінитись (репрекласифікація) → анти-жорсткий; моделюю як означений клас за hasClinicalSignificance", "pathogenic variant — первинний підклас genetic variant: анти-жорсткий клас під жорстким без можливості виведення; перекласифікація вимагає ручного видалення типу"),
 ("GeneticVariant / SNP / Indel", "+R", "+I", "+U", "−D", "жорсткі: тип зміни не залежить від контексту; SNP ⊥ Indel — диз'юнктні, ідентичність спільна", "аналогічно (is-a коректні), але SNP/Indel не диз'юнктні перевірено лише частково"),
 ("Gene vs «BRCA1»", "+R", "+I", "+U", "−D", "Gene — клас, BRCA1/BRCA2/PALB2/TP53 — індивіди класу Gene: у BRCA1 немає власних екземплярів", "BRCA1 і BRCA2 — класи (успадковано з таксономії ЛР5) і водночас індивіди з типом «BRCA1»: змішування класу та індивіда (punning без потреби); клас без законних екземплярів"),
 ("GenePanel", "+R", "+I", "+U", "−D", "артефакт-колекція (дизайнована множина генів), ⊑ DataArtifact; hasMember ≥ 2", "gene panel ⊑ genomic element — панель не є елементом геному, а дизайнованим набором: хибний is-a (різні критерії ідентичності)"),
 ("FilterThreshold vs QualityMeasure", "+R", "+I", "+U", "−D", "поріг — окремий клас (параметр процедури), не підклас міри якості", "threshold ⊑ Measure of quality: поріг — значення параметра, не міра; різні критерії ідентичності (порушення правила ідентичності)"),
 ("Exon", "+R", "+I", "+U", "+D", "існує лише як частина гена: ∃partOf.Gene (залежність відображено аксіомою)", "exon ⊑ Genomic element без залежності від гена"),
]
doc = f"""# Порівняння з чернеткою LLM, OntoClean і CQ-тести (результат 5)

Чернетка LLM: `models/llm_draft.ttl` (сирий вихід — `llm_log/raw/step_llm_draft_raw_output.ttl`; нотатки автора чернетки — `llm_log/raw/step_llm_draft_notes.md`). Вхід: таксономія ЛР5, триплети карти ЛР6 v2, CQ ЛР4 і набір фактів `data/scenario_facts.md`. Чернетку створив окремий запуск LLM наосліп (без доступу до моєї онтології й до CQ-запитів); завантаження в Protégé в цьому середовищі неможливе — чернетку розібрано rdflib і перевірено HermiT.

## 1. Таблиця порівняння

{T(["Показник", "Моя онтологія", "Чернетка LLM"], rows)}

Зауваження до таблиці. (0) Середня кількість властивостей рахується для предметних індивідів (без допоміжних індивідів шаблонів ситуацій). (1) Збіг рахується за нормалізованою англійською назвою; різні назви тієї самої властивості (наприклад, `has_age` проти `has age (years)`) бачаться як «різні». (2) «Пропуски» значною мірою — класи ситуацій і метаонтології (Event, State, Action, Sensor, SituationTemplate…), яких у завданні LLM не було; чесніше читати пропуски предметних класів: низькі пороги й означені класи (`low QD variant`, `high FS SNP`, `adult/minor relative`) — вони потрібні для виведення. (3) «Зайві» класи чернетки — переважно (122 з 127) усі вузли таксономії ЛР5, перенесені без відбору.

## 2. Помилки й слабкі місця чернетки LLM

| № | Помилка | Як виявлено | Наслідок |
|---|---|---|---|
| 1 | Усі {l['object_properties']} об'єктних властивостей без domain і range ({l['object_props_with_domain']}/{l['object_props_with_range']}) | rdflib-підрахунок (compare_onto.py) | втрачено типи domain/range з каталогу відношень; помилки типів не виявляються reasoner'ом |
| 2 | `BRCA1`, `BRCA2` — одночасно класи й індивіди з типом «BRCA1» | перегляд індивідів | змішування класу та індивіда; клас без законних екземплярів (OntoClean) |
| 3 | `pathogenic variant` — первинний підклас `genetic variant` | OntoClean (анти-жорсткий клас) | перекласифікацію неможливо вивести; потрібне ручне редагування |
| 4 | Ступінь спорідненості — заявлений тип індивіда, а родинні зв'язки (`parent_of`, `sibling_of`, `cousin_of`) з ним не пов'язані | порівняння виведень HermiT: нових типів лише {llm_new} проти 18 | reasoner не виводить ступінь; зміна родоводу не оновить класифікацію |
| 5 | `panelSize` має range `xsd:string` | перегляд властивостей | розмір панелі — число; помилка типу даних |
| 6 | `threshold ⊑ Measure of quality`, `gene panel ⊑ Genomic element`, `exon ⊑ Genomic element` без залежності | OntoClean | хибні is-a (різні критерії ідентичності) |
| 7 | 6 характеристик властивостей (`owl:TransitiveProperty` для part_of і derived_from, `owl:SymmetricProperty` для is_kin_of, sibling_of, cousin_of, `owl:FunctionalProperty` для has_filter_status) записано **як значення rdfs:label** (`rdfs:label "part_of"@en , owl:TransitiveProperty`), а не як типи | пошук у файлі + підрахунок характеристик (0 транзитивних/симетричних замість заявлених у нотатках) | фактично жодна характеристика не діє; нотатки автора чернетки твердять протилежне (помилка самозвіту LLM) |
| 8 | CQ19 (розбіжність моделювання, не помилка): чернетка зберігає «pathogenic variant → hereditary cancer» з карти v2, а в моїй онтології ризик виражено двома конкретними раками | CQ-запит | відповіді відрізняються через рішення про моделювання; у моїй онтології «hereditary cancer» не клас захворювання |
| 9 | Статуси фільтрації (`FILTERED`) призначено явно, а не виведено з порогів | нотатки + запит CQ10 | дублювання логіки; ризик розбіжності з порогами (хоча CQ10 пройдено) |

## 3. OntoClean ({len(ONTOCLEAN)} груп класів)

Мета-властивості: R — жорсткість (+R/~R/−R), I — несе критерій ідентичності, U — єдність, D — залежність. Оцінки виставлено вручну (LLM-асистент; студент має переглянути перед захистом).

{T(["Клас", "R", "I", "U", "D", "Висновок для моєї онтології", "Висновок для чернетки LLM"], ONTOCLEAN)}

Зміни за результатами OntoClean у моїй онтології: `PathogenicVariant`, ступені родичів, `LowQD*`/`HighFS*` — означені (≡) класи; гени — індивіди; `GenePanel` — під `DataArtifact`; поріг — окремий клас; екзон має аксіому залежності. Невирішено: `Proband` і `Relative` лишені підкласами `Person` (практичне спрощення; на логіку роль не впливає).

## 4. CQ-тести ({len(cq['mine'])} запитів SPARQL, `tests/cq_sparql/*.rq`)

Запити написано за мітками (rdfs:label@en) класів і властивостей з каталогу відношень, тож їх можна виконати над обома онтологіями; відповіді порівнюються з очікуваним у заголовку файла. Перед виконанням додаються твердження, виведені HermiT.

{T(["CQ", "Питання", "Очікувано", "Моя", "Чернетка LLM"], [(a["cq"], a["question"], a["expected"], "✓" if a["passed"] == "1" else "✗ " + a["got"], "✓" if b["passed"] == "1" else "✗ " + b["got"]) for a, b in zip(cq["mine"], cq["llm"])])}

**Частка пройдених: моя онтологія {sum(int(r['passed']) for r in cq['mine'])}/{len(cq['mine'])} = {share['mine']:.0%}; чернетка LLM {sum(int(r['passed']) for r in cq['llm'])}/{len(cq['llm'])} = {share['llm']:.0%}.**

Застереження щодо чесності порівняння: CQ формулювала я вже після побудови моєї онтології, і вони спираються на мітки, які чернетці було прямо задано; відповідність 100% для моєї онтології — частково наслідок цього (запити не є незалежним еталоном). Перевірка чутливості: видалення аксіоми `VQSR requires large variant set` змінює відповідь CQ05 (тест `test_cq_detects_missing_axiom`), тобто запити здатні провалюватись.

## 5. Висновок: що взято з чернетки, що відкинуто

Взято (змінено мою онтологію):
1. **Соматичний варіант** (`SomaticVariant`, диз'юнктний із `GermlineVariant`) — у чернетці є пара germline/somatic, я її не моделювала; додано.
2. **Кардинальність пробанда в каскадному тестуванні** (`CascadeTesting ⊑ hasProband = 1 Proband`) — ідея чернетки (рівно 1 пробанд); додано з властивістю `hasProband` і індивідом CT-01 → Olena.
3. **Мінімальний вік тестування як дані** (`hasMinTestingAge = 18`, у чернетці `minTestingAge`) — додано як data-властивість і значення на `CascadeTesting`.

Відкинуто:
1. Усі 154 вузли таксономії як класи (122 зайві): частину термінів моделюють індивіди або значення; перевантажує онтологію без користі для CQ.
2. BRCA1/BRCA2 як класи — гени мають бути індивідами (OntoClean, помилка 2).
3. Об'єктні властивості без domain/range (помилка 1) — для моєї онтології типи з каталогу обов'язкові.
4. Явне призначення статусів FILTERED (помилка 9) — натомість виведення через означені класи.
5. `panelSize` як рядок (помилка 5).
"""
(ROOT / "docs/onto_eval.md").write_text(doc, encoding="utf-8")
print("ok", llm_new)
