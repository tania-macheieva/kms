"""claims/claims.csv, llm_log/log.csv та docs/cmap_changes_v1_v2.md."""
import csv
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_triples import TEXT, norm   # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
tr = [json.loads(l) for l in (ROOT / "models/triples_llm.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
man = {x["id"]: x for x in json.loads((ROOT / "data/triples_manual_review.json").read_text(encoding="utf-8"))["reviewed"]}
final = {(r["s"], r["p"], r["o"]) for r in csv.DictReader(open(ROOT / "models/triples_final.csv", encoding="utf-8-sig"))}
exp = json.loads((ROOT / "models/cmap_expert.json").read_text(encoding="utf-8"))
lab = {c["id"]: c["label"] for c in exp["concepts"]}
exp_set = {(lab[p["s"]].lower(), p["p"], lab[p["o"]].lower()) for p in exp["propositions"]}
SRC = {"gatk": "sources/gatk_hard_filtering.txt", "cdc": "sources/cdc_cascade_testing.txt"}
rows = []
for t in tr:
    errs = [c if isinstance(c, str) else c["class"] for c in t["checks"]]
    q = norm(t["evidence"]) in TEXT[t["source"]]
    level = "V1" if q else "V0"
    if q and not errs:
        level = "V2"
        if (t["s"].lower(), t["p"], t["o"].lower()) in exp_set:
            level = "V3"
    if errs or t["id"] in man:
        status = "rejected"
        comment = "; ".join(filter(None, [("автоперевірка: " + ",".join(errs)) if errs else "", man.get(t["id"], {}).get("issue", "")]))
    else:
        status = "verified"
        comment = "цитата знайдена; типи коректні" + ("; збігається з експертною картою" if level == "V3" else "; відсутня в експертній карті v1, але підтримана текстом")
    rows.append({"claim": f"{t['s']} —{t['p']}→ {t['o']}", "type": "relation", "source": SRC[t["source"]], "level": level, "status": status, "comment": f"[{t['id']}] " + comment})
EXTRA = [
    ("Тестування родичів: 50% для родичів першого ступеня", "number", "cdc", "1 in 2 (50%) chance"),
    ("25% для родичів другого ступеня", "number", "cdc", "1 in 4 (25%) chance"),
    ("12,5% для родичів третього ступеня", "number", "cdc", "1 in 8 (12.5%) chance"),
    ("Поріг ReadPosRankSum < −8", "number", "gatk", "ReadPosRankSum value less than -8.0"),
    ("Поріг MQRankSum < −12,5", "number", "gatk", "MQRankSum < -12.5"),
    ("VQSR потребує великої кількості варіантів і відомих ресурсів", "relation", "gatk", "requires a large number of variants and well-curated known variant"),
    ("SOR створено, бо FS штрафує варіанти в кінці екзонів", "relation", "gatk", "SOR was created because FS tends to penalize variants that occur at the ends of exons"),
    ("Правило: будь-яке значення поза порогом → варіант відкидається", "rule", "gatk", "throwing out any variants that have annotation values above or below the set thresholds"),
    ("Тестування лише дорослих (≥ 18 років)", "rule", "cdc", "should only be done on adults (18 years of age and older)"),
    ("Тестування починають із найближчих родичів", "rule", "cdc", "genetic testing should start with family members who are most closely related"),
]
for c, ty, s, q in EXTRA:
    ok = norm(q) in TEXT[s]
    rows.append({"claim": c, "type": ty, "source": SRC[s], "level": "V1" if ok else "V0", "status": "verified" if ok else "pending", "comment": "цитата знайдена в тексті: «" + q + "»" if ok else "цитату не знайдено"})
rows.append({"claim": "FS > 200 для INDEL", "type": "number", "source": "коментар читача до статті GATK (не основний текст)", "level": "V0", "status": "pending", "comment": "значення з коментаря; перевірити за офіційною документацією GATK (потрібен V4)"})
rows.append({"claim": "Карта «колеги» (запуск LLM) точніша за LLM-триплети за рубрикою", "type": "evaluation", "source": "llm_log/raw/step5_rubric_R*_raw_output.json", "level": "V3", "status": "pending", "comment": "два незалежні запуски дали однаковий порядок; це не людська оцінка"})
rows.append({"claim": "Визначення 121 терміна таксономії (ЛР5) коректні", "type": "definition", "source": "ЛР5", "level": "V0", "status": "pending", "comment": "визначення згенеровано/відредаговано з участю LLM; потрібна перевірка студентом за MeSH/EDAM"})
with open(ROOT / "claims/claims.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["id", "claim", "type", "source", "verification_level", "status", "comment"])
    for i, r in enumerate(rows, 1):
        w.writerow([f"C{i:03d}", r["claim"], r["type"], r["source"], r["level"], r["status"], r["comment"]])
n = len(rows); ver = sum(r["status"] == "verified" for r in rows); rej = sum(r["status"] == "rejected" for r in rows); pen = n - ver - rej
(ROOT / "claims/README.md").write_text(f"""# claims.csv — реєстр тверджень, отриманих від LLM

Рівні перевірки: **V0** — не перевірено; **V1** — дослівна цитата знайдена в тексті джерела (скрипт `scripts/check_triples.py`);
**V2** — додатково пройдено перевірку типів domain/range за каталогом; **V3** — збігається з незалежним джерелом (експертна карта);
**V4** — підтверджено людиною за первинним джерелом (**жодного V4 ще немає** — це крок студента).

Статуси: verified / rejected / pending.

Підсумок: усього {n}; verified {ver} ({ver/n:.0%}); rejected {rej}; pending {pen}.
Відхилені твердження пояснено в колонці `comment`.
""", encoding="utf-8")
print(n, ver, rej, pen)
# журнал запусків LLM
LOG = [
    ("step3", "Витяг триплетів із 2 текстів із закритим каталогом відношень", "prompt_v1 (llm_log/prompts/step3_prompt_v1.md)", "llm_log/raw/step3_triples_llm_raw_output.jsonl", "41 триплет; автоперевірка + ручний перегляд; 12 відхилено"),
    ("step3b", "Список неперенесених (unmapped) тверджень", "prompt_v1", "llm_log/raw/step3_unmapped_raw_output.json", "17 записів; використано як перелік прогалин каталогу"),
    ("step4", "Карта «колеги» наосліп (без доступу до експертної)", "prompt_v1", "llm_log/raw/step4_peer_map_raw_output.json", "Використано як третю карту для оцінювання; не є колегою-людиною"),
    ("step5-R1", "Оцінювач 1 за рубрикою Новака", "rubric_v1", "llm_log/raw/step5_rubric_R1_raw_output.json", "Зауваження враховано у v2"),
    ("step5-R2", "Оцінювач 2 за рубрикою Новака (незалежно)", "rubric_v1", "llm_log/raw/step5_rubric_R2_raw_output.json", "Перезапуск після помилки 429; зауваження враховано у v2"),
]
with open(ROOT / "llm_log/log.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f); w.writerow(["step", "task", "date", "model", "temperature_seed", "prompt_version", "raw_output", "human_decision"])
    for s, t, p, raw, dec in LOG:
        w.writerow([s, t, "2026-10-24/25", "claude-sonnet-5-5 (subagent)", "не доступні (задати неможливо в цьому середовищі)", p, raw, dec + "; очікує перегляду студентом"])
# журнал змін
CH = json.load(open(ROOT / "data/changes_v1_v2.json", encoding="utf-8"))
md = ["# Зміни v1 → v2", "", "| № | Що змінено | Причина | Джерело зауваження |", "|---|---|---|---|"] + ["| " + " | ".join(x) + " |" for x in CH]
(ROOT / "docs/cmap_changes_v1_v2.md").write_text("\n".join(md) + "\n", encoding="utf-8")
