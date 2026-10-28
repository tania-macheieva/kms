"""Генерує docs/onto_eval.md із docs/evidence/onto_compare.json і CQ-результатів; OntoClean та висновки — ручні (у цьому файлі)."""
import csv
import json
from pathlib import Path

from rdflib import BNode
from rdflib.namespace import OWL, RDF, RDFS
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from run_cq import load   # noqa: E402

R = json.loads((ROOT / "docs/evidence/onto_compare.json").read_text(encoding="utf-8"))


def axioms(g):
    some = len(list(g.subject_objects(OWL.someValuesFrom))); only = len(list(g.subject_objects(OWL.allValuesFrom)))
    card = sum(len(list(g.subject_objects(p))) for p in (OWL.minQualifiedCardinality, OWL.maxQualifiedCardinality, OWL.qualifiedCardinality, OWL.minCardinality, OWL.maxCardinality, OWL.cardinality))
    hv = len(list(g.subject_objects(OWL.hasValue)))
    eq = len(list(g.subject_objects(OWL.equivalentClass)))
    dis = len(list(g.subjects(RDF.type, OWL.AllDisjointClasses))) + len(list(g.subject_objects(OWL.disjointWith)))
    prop_dr = sum(1 for p in g.subjects(RDF.type, OWL.ObjectProperty) if list(g.objects(p, RDFS.domain)) and list(g.objects(p, RDFS.range)))
    chars = sum(len(list(g.subjects(RDF.type, t))) for t in (OWL.TransitiveProperty, OWL.SymmetricProperty)) + len(list(g.subject_objects(OWL.inverseOf)))
    chain = len(list(g.subject_objects(OWL.propertyChainAxiom)))
    return [some, only, card, hv, eq, dis, prop_dr, chars, chain]


am, al = axioms(load("mine")), axioms(load("llm"))
c, p, d = R["classes"], R["properties"], R["draft_defects"]
M = ["# Порівняння моєї онтології з чернеткою LLM (результат 5)", "",
     "Артефакти: `models/onto.owl` + `models/onto_data.ttl` (моя), `models/llm_draft.ttl` (чернетка LLM), `tests/cq_sparql/*.rq`, `scripts/eval_onto.py`, `scripts/run_cq.py`. Усі числа відтворюються командами з README.", "",
     "## 1. Як отримано чернетку LLM",
     "Окремий запуск моделі (claude-sonnet-5-5, наосліп: без моєї онтології, без CQ-запитів, без правил перевірки) отримав таксономію ЛР5, триплети карти v2, текст CQ ЛР4 і файл сценарію-даних; завдання — Turtle з ≥ 30 класами, обмеженнями, властивостями й індивідами. Дослівний вихід: `llm_log/raw/step_llm_draft_raw_output.ttl`, нотатки моделі — `llm_log/raw/step_llm_draft_notes_raw.md`. Чернетку завантажено rdflib і HermiT (у Protégé в цьому середовищі її відкрити неможливо; формат OWL/Turtle для Protégé коректний).", "",
     "## 2. Таблиця порівняння (збіг / пропуски / зайві)", "",
     "| Показник | Моя онтологія | Чернетка LLM |", "|---|---|---|",
     f"| Класів | {c['mine']} | {c['llm']} |",
     f"| Збіг за міткою (з них псевдоніми: {len(c['matched_alias'])}) | {c['matched_by_label']} | {c['matched_by_label']} |",
     f"| Пропуски відносно моєї (є в моїй, немає в чернетці) | — | {c['mine_only']} |",
     f"| Зайві відносно моєї (є в чернетці, немає в моїй) | {c['llm_only']} | — |",
     f"| Об'єктних властивостей | {p['mine_object']} | {p['llm_object']} (збіг за міткою: {p['object_matched']}) |",
     f"| Data-властивостей | {p['mine_data']} | {p['llm_data']} (збіг за міткою: {p['data_matched']}) |",
     f"| Аксіом ∃ (someValuesFrom) | {am[0]} | {al[0]} |", f"| Аксіом ∀ (allValuesFrom) | {am[1]} | {al[1]} |", f"| Кардинальних обмежень | {am[2]} | {al[2]} |",
     f"| hasValue-обмежень | {am[3]} | {al[3]} |", f"| Означених класів (≡) | {am[4]} | {al[4]} |", f"| Груп диз'юнктності | {am[5]} | {al[5]} |",
     f"| Object-властивостей з domain і range | {am[6]} з {p['mine_object']} | {al[6]} з {p['llm_object']} |", f"| Характеристик (транзитивна/симетрична/обернена) | {am[7]} | {al[7]} |", f"| Ланцюгів властивостей | {am[8]} | {al[8]} |",
     f"| Нових типів, виведених HermiT для індивідів | {R['mine']['new_inferred_types_on_individuals']} | {d['draft_new_inferred_types_on_individuals']} |", "",
     "Розшифровка: «пропуски» — переважно мета-онтологія (State/Event/Action/Sensor, потрібна для результату 4), допоміжні означені класи (LowQDVariant, AdultRelative…) і Disease/Cancer; «зайві» — 120+ класів, що просто перенесли всю таксономію ЛР5 (proteomics, data privacy, clinical trial тощо) і не потрібні для CQ. Збіг за міткою занижує подібність (назви різні: Data artifact / Data and artifact).", "",
     "Чернетка узгоджена (HermiT), необґрунтованих класів немає.", "",
     "## 3. Помилки й слабкі місця чернетки (перевірено скриптом і вручну)", "",
     "| № | Помилка | Доказ | Тип |", "|---|---|---|---|",
     f"| 1 | Характеристика властивості записана як **друге значення rdfs:label** (`rdfs:label \"part_of\"@en , owl:TransitiveProperty`), тому транзитивність/симетричність не оголошено | у {len(d['E_label_is_IRI'])} властивостях ({', '.join(d['E_label_is_IRI'])}); фактично транзитивних 0, симетричних 0, хоча нотатки моделі стверджують протилежне | синтаксично-семантична |",
     f"| 2 | Об'єктні властивості без domain/range | {d['object_props_without_domain_or_range']} з {d['object_props_total']} без domain або range (обидва відсутні у {d['object_props_without_domain_and_range_both']}) | неповнота |",
     f"| 3 | Класи замість індивідів: конкретні гени BRCA1/BRCA2 — класи (підкласи gene) з єдиним індивідом BRCA1_gene | classes: {', '.join(d['classes_with_single_individual_that_are_individuals_in_reality'])} | OntoClean (ідентичність) |",
     f"| 4 | Висновки записано вручну замість виведення: ступінь спорідненості й ймовірність задано кожному індивіду ({d['degree_class_asserted_not_inferred']} тверджень), статус PASS/FILTERED — {d['asserted_filter_status_instead_of_inferred']} тверджень; reasoner майже нічого не додає ({d['draft_new_inferred_types_on_individuals']} нових типів) | результат HermiT | спосіб моделювання |",
     "| 5 | Семантична помилка: `BRCA1_gene increases_risk_of Olena_breast_cancer` — ген (клас-тип) підвищує ризик конкретного випадку раку; коректно — патогенний варіант (змішування гена й варіанта, E7) | індивід BRCA1_gene | семантична |",
     "| 6 | Генна панель — підклас «Genomic element» (біологічної сутності), хоча панель — спроєктований набір (артефакт) | ланцюг gene_panel → Genomic_element → Biological_entity | OntoClean (єдність/тип) |",
     "| 7 | Немає класів для віку/неповнолітніх; відкладене тестування Sofiia закодовано окремою властивістю testing_deferred_for | у чернетці немає minor/adult | неповнота |",
     f"| 8 | Мінімальні метадані: skos:definition не використано ({d['skos_definition_used']}), у заголовку {d['ontology_metadata_triples']} трипл­ети (немає версії/власника) | аналіз файла | якість |", "",
     "## 4. Перевірка класів за OntoClean (метавластивості: R — жорсткість, I — ідентичність, U — єдність, D — залежність)", "",
     "| Клас | R | I | U | D | Висновок для моєї онтології | Висновок для чернетки |", "|---|---|---|---|---|---|---|",
     "| Gene | +R | +I (локус/послідовність) | +U | незалежний | клас; конкретні гени (BRCA1) — індивіди ✓ | BRCA1/BRCA2 — класи з одним індивідом: порушено розмежування «тип/екземпляр» ✗ |",
     "| Proband | −R (роль) | успадковує від Person | — | +D (залежить від аналізу родини) | підклас Person, диз'юнктний із Relative ✓ (роль не підпорядковує жорсткий клас) | підклас patient ⊑ Person ✓ |",
     "| Relative / FirstDegreeRelative | −R (роль щодо пробанда) | від Person | — | +D (від пробанда) | означений клас ≡ Person ⊓ ∃isFirstDegreeRelativeOf.Proband: членство **виводиться** і змінюється разом із зв'язками ✓ | тип призначено індивіду вручну: при зміні пробанда доведеться переписувати ✗ |",
     "| PathogenicVariant | −R (статус надає курація) | від GeneticVariant | — | +D (від висновку) | означений клас через hasClinicalSignificance ✓ | постійний підклас, призначений вручну ⚠ |",
     "| GenePanel | +R | +I (перелік членів) | −U (єдність надана проєктуванням) | +D (від членів) | артефакт даних із hasMember ≥ 2 ✓ | під «Genomic element» ✗ |",
     "| FlaggedVariant | −R (залежить від порогів) | від GeneticVariant | — | +D | означений клас — об'єднання порогів ✓ | еквівалентність є, але статус ще й заданий явно ⚠ |",
     "| MinorRelative | −R (вік змінюється) | від Relative | — | +D | означений клас через hasAgeYears < 18 → особа «дорослішає» автоматично ✓ | відсутній ✗ |",
     "| VCFFile | +R | +I (вміст/контрольна сума) | +U | незалежний | ✓ | ✓ |", "",
     "Позначення: ✓ — відповідає OntoClean; ⚠ — припустимо, але краще інакше; ✗ — порушення. Оцінки метавластивостей — експертне судження моє (та LLM); вони потребують перевірки викладачем.", "",
     "## 5. CQ-запити та частка пройдених", "",
     "Запити `tests/cq_sparql/*.rq` написано за мітками (rdfs:label @en) спільного словника й виконано на обох онтологіях разом із виведеннями HermiT. Очікуваний результат — у заголовку кожного файла (`# expect:`).", ""]
cqm = {r["cq"]: r for r in csv.DictReader(open(ROOT / "docs/evidence/cq_results_mine.csv", encoding="utf-8-sig"))}
cql = {r["cq"]: r for r in csv.DictReader(open(ROOT / "docs/evidence/cq_results_llm.csv", encoding="utf-8-sig"))}
M += ["| CQ | Запитання | Очікуваний результат | Моя | Чернетка LLM |", "|---|---|---|---|---|"]
for k in cqm:
    M.append(f"| {k} | {cqm[k]['question']} | {cqm[k]['expected']} | {'✓' if cqm[k]['passed']=='1' else '✗ ' + cqm[k]['got']} | {'✓' if cql[k]['passed']=='1' else '✗ ' + cql[k]['got']} |")
tm = sum(int(r["passed"]) for r in cqm.values()); tl = sum(int(r["passed"]) for r in cql.values())
M += ["", f"**Частка пройдених:** моя онтологія — {tm}/{len(cqm)} = {tm/len(cqm):.0%}; чернетка LLM — {tl}/{len(cql)} = {tl/len(cql):.0%}.", "",
      "Застереження до цього показника: (1) CQ-запити писала я після побудови своєї онтології, тому 100% не є незалежним доказом; (2) чернетка отримала сценарій-даних і CQ-список, тому більшість відповідей змодельовано явно (асертовані статуси); (3) CQ перевіряють відповіді, а не якість моделювання — помилки з розділів 3–4 CQ не бачать. Для чесного порівняння потрібні CQ, написані третьою особою. Негативний контроль (видалення означення FlaggedVariant ламає CQ10) виконано в `tests/test_onto.py`.", "",
      "## 6. Висновок: що взято з чернетки, що відкинуто", "",
      "**Взято:** (1) властивість `isDeceased` (Maria померла) — додано до моєї онтології (`isDeceased`, `Maria`); (2) ідею тримати в індивідів ідентифікатори й окремі індивіди-анотації для кожного показника — у моїй вона вже була, чернетка її підтвердила; (3) нотатки про відсутність в еталонній таксономії класів для родичів і пороги стали перевіркою моєї повноти (додано HighFS/INDEL, MQRankSum, ReadPosRankSum).", "",
      "**Відкинуто, з прикладами:**",
      "1. Перенесення всіх 154 вузлів таксономії як класів (≈ 120 зайвих: proteomics, data privacy, clinical trial) — вони не потрібні для CQ, збільшують шум і ризик помилок (приклад: gene panel під Genomic element).",
      "2. Ручне призначення ступеня спорідненості й ймовірності кожному індивіду (Marta, Sofiia…) замість виведення з родинних зв'язків — HermiT у моїй онтології виводить ті самі типи з hasParent/hasSibling/ланцюгів (18 нових типів, 44 зв'язки), а в чернетці лише 2.",
      "3. BRCA1/BRCA2 як класи й твердження «ген підвищує ризик раку» — замінено індивідами гена та патогенним варіантом як носієм ризику.",
      "4. «Транзитивність», записана як мітка (`rdfs:label \"part_of\"@en , owl:TransitiveProperty`) — виправлено оголошенням `a owl:TransitiveProperty` у моїй онтології; у чернетці вона не діє.", ""]
(ROOT / "docs/onto_eval.md").write_text("\n".join(M), encoding="utf-8")
print("ok", tm, tl)
