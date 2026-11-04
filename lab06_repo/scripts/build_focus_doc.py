"""Генерує docs/cmap_focus.md із data/relations.json та models/cmap_expert.json (щоб числа й посилання збігалися з картою)."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from map_tools import REL, ROOT, load_map            # noqa: E402

m = load_map(ROOT / "models/cmap_expert.json")
by = {c["id"]: c for c in m["concepts"]}
LEVEL = {  # рівень загальності: 1 — найзагальніші … 4 — екземпляри
    "genetic variant": 1, "gene": 1, "hereditary cancer": 1, "variant filtering": 1, "genetic testing": 1, "risk assessment": 1,
    "pathogenic variant": 2, "germline variant": 2, "hard filtering": 2, "variant quality score recalibration": 2, "cascade testing": 2,
    "genetic counseling": 2, "breast cancer": 2, "ovarian cancer": 2, "proband": 2, "relative": 2, "gene panel": 2, "family history": 2,
    "variant calling": 2, "sequence alignment": 2, "VCF file": 2, "BAM file": 2,
    "single nucleotide polymorphism": 3, "insertion-deletion": 3, "BRCA1": 3, "BRCA2": 3, "quality by depth": 3, "Fisher strand bias": 3,
    "strand odds ratio": 3, "mapping quality": 3, "rank sum test": 3, "read depth": 3, "exon": 3,
}
ORDER = sorted(LEVEL, key=lambda k: (LEVEL[k], k))
inst = [c["label"] for c in m["concepts"] if c["kind"] == "instance"]
# покриття CQ ЛР4: (CQ, запитання, покриття, пропозиції-доказ у картi)
def pid(s, p, o):
    sid = next(c["id"] for c in m["concepts"] if c["label"] == s); oid = next(c["id"] for c in m["concepts"] if c["label"] == o)
    return next(x["id"] for x in m["propositions"] if x["s"] == sid and x["p"] == p and x["o"] == oid)
CQ = [
    ("CQ01", "За якого QD SNP-варіант отримує прапорець LowQD?", "повністю", [pid("quality by depth", "has_example", "QD < 2")]),
    ("CQ02", "За якого FS SNP відкидають?", "повністю", [pid("Fisher strand bias", "has_example", "FS > 60 (SNP)")]),
    ("CQ04", "Які значення SOR, MQ, MQRankSum призводять до прапорців?", "частково (SOR, MQ; без MQRankSum)", [pid("strand odds ratio", "has_example", "SOR > 3"), pid("mapping quality", "has_example", "MQ < 40")]),
    ("CQ07", "Чому варіант на кінці екзона з лише LowFS не слід просто відкидати?", "частково (зв'язок SOR—екзон)", [pid("strand odds ratio", "recommended_for", "exon")]),
    ("CQ08", "Який метод фільтрації обрати для малої панелі?", "повністю", [pid("hard filtering", "recommended_for", "gene panel"), pid("hard filtering", "is_a", "variant filtering")]),
    ("CQ11", "Який шанс успадкування для рідного брата/сестри?", "повністю", [pid("relative", "has_example", "рідний брат/сестра: 50%")]),
    ("CQ13", "Який шанс для двоюрідних і далі?", "повністю", [pid("relative", "has_example", "двоюрідний родич: до 12,5%")]),
    ("CQ14", "З кого починати тестування і чому?", "частково (каскад застосовується до родичів)", [pid("cascade testing", "applies_to", "relative")]),
    ("CQ17", "Чи буде користь від універсальної панелі без «родинного» варіанта?", "ні (поза картою)", []),
    ("CQ15", "Чи можна тестувати 17-річного родича?", "ні (вік поза картою)", []),
]
L = []
L.append("# Результат 1. Фокусне питання, parking lot і каталог відношень\n")
L.append("## 1. Фокусне питання\n")
L.append("> **Як якість анотацій варіантів і родинний генетичний ризик перетворюються на рішення — які варіанти відкинути під час жорсткої фільтрації "
         "і яких родичів пробанда з BRCA1/BRCA2 тестувати в першу чергу?**\n")
L.append("Питання відкрите (починається з «як», не має відповіді «так/ні»), змістовне й пов'язане з нашою проблемою — підтримкою рішень щодо якості геномних варіантів "
         "та каскадного тестування. Воно задає межі карти: два кластери (контроль якості варіантів, клінічне тестування) і зв'язки між ними через геномні поняття.\n")
L.append("## 2. Parking lot (33 поняття + 6 екземплярів), від загальних до часткових\n")
L.append("Усі поняття взято зі словника ЛР5 (таксономія). Рівень загальності: 1 — найзагальніші, 3 — конкретні, 4 — екземпляри (порогові значення, випадки). Порядок у межах рівня — алфавітний.\n")
L.append("| № | Поняття | Рівень | Тип (ЛР5, рівень 1) | Кластер |")
L.append("|---|---|---|---|---|")
cl = {"G": "Геноміка й дані", "Q": "Контроль якості", "C": "Клінічне тестування"}
n = 0
for k in ORDER:
    n += 1; c = next(x for x in m["concepts"] if x["label"] == k)
    L.append(f"| {n} | {k} | {LEVEL[k]} | {c['type']} | {cl[c['cluster']]} |")
for k in inst:
    n += 1; c = next(x for x in m["concepts"] if x["label"] == k)
    L.append(f"| {n} | {k} | 4 | {c['type']} | {cl[c['cluster']]} |")
L.append("\nВідкладено (не потрапило до карти, але лишається у ЛР5): `genome`, `exome`, `RNA sequencing`, `ontology` тощо — поза фокусним питанням.\n")
L.append("## 3. Каталог відношень (12 типів)\n")
L.append("| № | Відношення | У карті | Визначення | Domain → range (типи ЛР5) | Приклад |")
L.append("|---|---|---|---|---|---|")
for i, (rid, r) in enumerate(REL.items(), 1):
    if r.get("same_type"):
        dr = "той самий тип"
    else:
        dom = "будь-який" if r["domain"] == ["*"] else ", ".join(r["domain"]); rng = "будь-який" if r["range"] == ["*"] else ", ".join(r["range"])
        dr = f"{dom} → {rng}"
    L.append(f"| {i} | `{rid}` | {r['label_uk']} | {r['definition']} | {dr} | {r['example']} |")
L.append("\nВідношення «related-to» навмисно відсутнє: кожен зв'язок має бути одним із 12 типів із визначенням. Типи domain/range використовуються для автоматичної перевірки триплетів (результат 3).\n")
L.append("## 4. Компетентнісні запитання ЛР4, які покриває карта\n")
L.append("Запитання взято з `docs/cq_lab4.md` (18 CQ). Карта v1 повністю покриває 5, частково — 3.\n")
L.append("| CQ | Запитання | Покриття | Пропозиції в карті |")
L.append("|---|---|---|---|")
for q, t, cov, ps in CQ:
    L.append(f"| {q} | {t} | {cov} | {', '.join(ps) or '—'} |")
L.append("\nCQ17 і CQ15 лишаються поза картою свідомо (вік, склад панелі — деталі правил, а не понять); їх закриватимуть правила ЛР4.\n")
(ROOT / "docs/cmap_focus.md").write_text("\n".join(L), encoding="utf-8")
print("ok", n)
