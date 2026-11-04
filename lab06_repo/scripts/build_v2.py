"""Об'єднана карта v2 + triples_final.csv.

Вхід: експертна карта v1, підтверджені триплети LLM (models/triples_llm.jsonl), зауваження оцінювачів (docs/cmap_rubric.xlsx / llm_log).
Правки v1 → v2 перелічено в CHANGES (вони ж потрапляють у docs/cmap_changes_v1_v2.md).
Статуси триплетів: verified — є дослівна цитата, знайдена в тексті, і пройдено перевірку типів; expert_asserted — твердження експерта без цитати
(потребує підтвердження); pending — джерело другорядне (коментар читача) або цитата неточна.
"""
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_triples import TEXT, norm                                    # noqa: E402
from map_tools import REL, ROOT, load_map, render_png, stats, taxonomy_info, to_drawio   # noqa: E402

TAX = taxonomy_info()
exp = load_map(ROOT / "models/cmap_expert.json")
tr = {t["id"]: t for t in (json.loads(l) for l in (ROOT / "models/triples_llm.jsonl").read_text(encoding="utf-8").splitlines() if l.strip())}
by_label = {c["label"]: dict(c) for c in exp["concepts"]}
by_id = {c["id"]: c["label"] for c in exp["concepts"]}
props = {}        # (s_label, p, o_label) → dict
for p in exp["propositions"]:
    props[(by_id[p["s"]], p["p"], by_id[p["o"]])] = {"cross": p["cross"], "explanation": p["explanation"], "source": "expert", "status": "expert_asserted", "evidence": "", "src_text": ""}

CHANGES = []   # (id, що змінено, причина/зауваження, джерело зауваження)


def drop(s, p, o):
    props.pop((s, p, o), None)


def add(s, p, o, source="expert_v2", cross=False, explanation="", evidence="", src_text=""):
    props[(s, p, o)] = {"cross": cross, "explanation": explanation, "source": source, "status": "expert_asserted", "evidence": evidence, "src_text": src_text}


def concept(label, kind, cluster, typ, definition):
    by_label[label] = {"id": "", "label": label, "kind": kind, "cluster": cluster, "type": typ, "definition": definition, "in_vocabulary": label in TAX}


# --- 1. хибна класифікація раків як спадкових
drop("breast cancer", "is_a", "hereditary cancer"); drop("ovarian cancer", "is_a", "hereditary cancer")
add("pathogenic variant", "increases_risk_of", "breast cancer"); add("pathogenic variant", "increases_risk_of", "ovarian cancer")
CHANGES.append(("V2-01", "Видалено is_a «breast cancer/ovarian cancer → hereditary cancer»; зв'язок через підвищення ризику патогенним варіантом", "не кожен рак спадковий; is_a перебільшував (зауваження R1 і R2 до експертної карти)", "R1, R2"))
# --- 2. симетрія BRCA1/BRCA2 ↔ рак
add("BRCA1", "increases_risk_of", "ovarian cancer", source="expert_v2+llm:cdc"); add("BRCA2", "increases_risk_of", "breast cancer", source="expert_v2+llm:cdc")
CHANGES.append(("V2-02", "BRCA1 і BRCA2 пов'язано з обома раками (раніше BRCA1 — лише з молочною залозою, BRCA2 — лише з яєчниками)", "джерело CDC називає обидва гени для обох раків; неповнота v1", "R1, R2; триплети LLM L025–L028"))
# --- 3. ієрархія родичів і приклади
for lab, d, ex, exd in (("first-degree relative", "Родич першого ступеня: батьки, діти, рідні брати й сестри пробанда.", "рідні брати/сестри, батьки, діти: 50%", "Батьки, діти й рідні брати/сестри пробанда з BRCA1/BRCA2 мають шанс 1 з 2 (50%) мати ту саму зміну."),
                        ("second-degree relative", "Родич другого ступеня: зведені брати/сестри, тітки/дядьки, бабусі/дідусі.", "зведені брати/сестри, тітки/дядьки, бабусі/дідусі: 25%", "Зведені брати/сестри, тітки/дядьки, бабусі/дідусі мають шанс 1 з 4 (25%)."),
                        ("third-degree relative", "Родич третього ступеня та далі: двоюрідні й інші віддалені родичі.", "двоюрідні та віддалені родичі: до 12,5%", "Двоюрідні й віддалені родичі можуть мати до 1 з 8 (12,5%) шанс — верхня межа.")):
    concept(lab, "concept", "C", "Clinical concept", d); add(lab, "is_a", "relative")
    concept(ex, "instance", "C", "Clinical concept", exd); add(lab, "has_example", ex)
drop("relative", "has_example", "рідний брат/сестра: 50%"); drop("relative", "has_example", "двоюрідний родич: до 12,5%")
by_label.pop("рідний брат/сестра: 50%", None); by_label.pop("двоюрідний родич: до 12,5%", None)
add("cascade testing", "recommended_for", "first-degree relative", cross=False)
CHANGES.append(("V2-03", "Додано ієрархію родичів (першого/другого/третього ступеня) з прикладами 50% / 25% / до 12,5%; каскадне тестування рекомендоване насамперед родичам першого ступеня", "приклад «рідний брат/сестра: 50%» змішував клас і ймовірність; CQ12, CQ14 були непокриті", "R1, R2"))
# --- 4. VQSR: нетривіальні передумови
drop("variant quality score recalibration", "requires", "genetic variant")
concept("large variant set", "concept", "Q", "Data and artifact", "Великий набір варіантів — передумова для навчання моделі VQSR.")
concept("curated known variants", "concept", "Q", "Data and artifact", "Добре підготовлені ресурси відомих варіантів, на яких навчається VQSR.")
add("variant quality score recalibration", "requires", "large variant set", evidence="Unfortunately this method requires a large number of variants and well-curated known variant", src_text="gatk")
add("variant quality score recalibration", "requires", "curated known variants", evidence="Unfortunately this method requires a large number of variants and well-curated known variant", src_text="gatk")
CHANGES.append(("V2-04", "Тривіальне «VQSR потребує genetic variant» замінено на «потребує великого набору варіантів» і «потребує відомих ресурсів варіантів»", "тривіальна пропозиція, яка не пояснює вибір hard filtering для малих панелей (зауваження R2)", "R1, R2; триплет L015"))
# --- 5. правило екзонного кінця
drop("strand odds ratio", "recommended_for", "exon")
concept("variant at exon end", "concept", "Q", "Genetic variation", "Варіант у кінці екзона, для якого FS може занижувати якість через однобічне покриття.")
add("Fisher strand bias", "applies_to", "variant at exon end", evidence="SOR was created because FS tends to penalize variants that occur at the ends of exons.", src_text="gatk")
add("strand odds ratio", "recommended_for", "variant at exon end", evidence="SOR was created because FS tends to penalize variants that occur at the ends of exons.", src_text="gatk")
by_label.pop("exon", None) if all(k[0] != "exon" and k[2] != "exon" for k in props) else None
CHANGES.append(("V2-05", "Нечітке «SOR рекомендований для exon» замінено на правило екзонного кінця: FS штрафує такі варіанти, тому застосовують SOR", "зауваження: зв'язок не пояснював причину (REVIEW у ЛР4)", "R1, R2"))
# --- 6. пороги INDEL/MQRankSum/прапорець
INST = [
    ("Fisher strand bias", "FS > 200 (INDEL)", "Q", "Measure of quality", "Поріг для INDEL з коментаря читача до статті GATK (не з основного тексту; потребує перевірки).", "", "", "pending"),
    ("rank sum test", "MQRankSum < −12,5", "Q", "Measure of quality", "Рекомендований поріг GATK для MQRankSum.", "none of your variants have MQRankSum less than -12.5", "gatk", "verified"),
    ("rank sum test", "ReadPosRankSum < −8", "Q", "Measure of quality", "Рекомендований поріг GATK для ReadPosRankSum.", "ReadPosRankSum value less than -8.0", "gatk", "verified"),
    ("variant filtering", "будь-який прапорець → відкинути варіант", "Q", "Method and procedure", "Правило жорсткої фільтрації: варіант із значенням анотації поза порогом відкидається.", "throwing out any variants that have annotation values above or below the set thresholds", "gatk", "verified"),
    ("genetic testing", "тестування лише дорослих (≥ 18 років)", "C", "Clinical concept", "Чинні настанови: тестування лише дорослих, виняток — зміни з ризиком раку в дитинстві.", "should only be done on adults (18 years of age and older)", "cdc", "verified"),
]
for cls, lab, cl, typ, d, ev, st, status in INST:
    concept(lab, "instance", cl, typ, d); add(cls, "has_example", lab, evidence=ev, src_text=st)
    props[(cls, "has_example", lab)]["_status_hint"] = status
CHANGES.append(("V2-06", "Додано приклади: FS > 200 (INDEL), MQRankSum < −12,5, ReadPosRankSum < −8, правило «будь-який прапорець → відкинути», вік ≥ 18 років", "CQ03–CQ05, CQ15 були непокриті (зауваження R1, R2 до експертної й LLM-карт)", "R1, R2"))
# --- 7. злиття підтверджених триплетів LLM
MERGE = ["L009", "L010", "L013", "L014", "L021", "L032", "L036", "L037", "L040"]
for i in MERGE:
    t = tr[i]
    for lab in (t["s"], t["o"]):
        if lab not in by_label:
            by_label[lab] = {"id": "", "label": lab, "kind": "concept", "cluster": "G", "type": TAX[lab]["type"], "definition": TAX[lab]["definition"], "in_vocabulary": True}
    k = (t["s"], t["p"], t["o"])
    if k in props:
        props[k].update({"source": "expert+llm:" + t["source"], "evidence": t["evidence"], "src_text": t["source"]})
    else:
        props[k] = {"cross": False, "explanation": "", "source": "llm:" + t["source"], "status": "expert_asserted", "evidence": t["evidence"], "src_text": t["source"]}
# підтвердження експертних тверджень, що збіглися з триплетами LLM
for t in tr.values():
    k = (t["s"], t["p"], t["o"])
    if k in props and not t["checks"] and t["id"] not in {"L020", "L012", "L011"} and not props[k]["evidence"]:
        props[k].update({"source": "expert+llm:" + t["source"], "evidence": t["evidence"], "src_text": t["source"]})
CHANGES.append(("V2-07", f"До карти додано {len(MERGE)} підтверджених триплетів LLM (цитата знайдена, типи коректні, ручний перегляд пройдено)", "карта колеги й LLM показали пропущені в v1 зв'язки (mapping quality → sequencing read, VQSR → VCF file, genetic testing → рак тощо)", "R1, R2; триплети L009–L040"))
CHANGES.append(("V2-08", "Відхилено хибні триплети LLM: детекція генів замість варіантів (L033, L034, L038, L039), rank sum test → allele (L011), genetic counseling → risk assessment (L041), слабкі підстави (L020, L012)", "помилки типів і семантики, виявлені перевіркою (див. docs/evidence/triples_check.txt і data/triples_manual_review.json)", "перевірка триплетів"))

# --- id, визначення, валідація
for n, (lab, c) in enumerate(by_label.items(), 1):
    c["id"] = f"I{n:02d}" if c["kind"] == "instance" else f"M{n:02d}"
    c.setdefault("in_vocabulary", lab in TAX)
used = {x for k in props for x in (k[0], k[2])}
concepts = [c for c in by_label.values() if c["label"] in used]
ids = {c["label"]: c["id"] for c in concepts}
out_props, rows = [], []
for i, (k, v) in enumerate(sorted(props.items(), key=lambda kv: (by_label[kv[0][0]]["cluster"], kv[0])), 1):
    s, p, o = k
    assert p in REL, p
    status = v.get("_status_hint") or v["status"]
    ev = v["evidence"]
    if ev:
        ok = norm(ev) in TEXT.get(v["src_text"], "")
        status = ("verified" if ok else "pending") if status != "pending" else "pending"
        if not ok:
            ev = ev + " (цитату не підтверджено)"
    elif status != "pending":
        status = "expert_asserted"
    out_props.append({"id": f"P{i:02d}", "s": ids[s], "p": p, "o": ids[o], "cross": v["cross"], "explanation": v["explanation"]})
    rows.append({"s": s, "p": p, "o": o, "source": v["source"], "status": status, "evidence": ev or "—", "s_type": by_label[s]["type"], "o_type": by_label[o]["type"]})
m = {"title": "Об'єднана концептуальна карта v2", "concepts": concepts, "propositions": out_props}
(ROOT / "models/cmap_v2.json").write_text(json.dumps(m, ensure_ascii=False, indent=1), encoding="utf-8")
render_png(m, ROOT / "models/cmap_v2.png", "Об'єднана концептуальна карта v2")
to_drawio(m, ROOT / "models/cmap_v2.drawio", "Об'єднана концептуальна карта v2")
with open(ROOT / "models/triples_final.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, ["s", "p", "o", "source", "status", "evidence", "s_type", "o_type"]); w.writeheader(); w.writerows(rows)
json.dump(CHANGES, open(ROOT / "data/changes_v1_v2.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(json.dumps(stats(m), ensure_ascii=False)); print(len(rows), "рядків; статуси:", {s: sum(1 for r in rows if r["status"] == s) for s in {r["status"] for r in rows}})
