"""llm_log/log.csv (protocol of LLM-expert use): one row per batch / assistant action. Regenerate: python scripts/make_llm_log.py"""
import json, csv, pathlib, re
ROOT = pathlib.Path(__file__).resolve().parent.parent
HAIKU = "claude-haiku-4-5-20251001 (налаштований ідентифікатор субагента; фактична модель могла відрізнятися)"; SONNET = "claude-sonnet-5-5 (налаштований ідентифікатор субагента; фактична модель могла відрізнятися)"
PAR = "не керується (немає параметра temperature/seed у субагента); сліпий прогін: бачить лише system+user"
PV = {"plan_v1": ("plan_v1", "планувальник агента (вибір інструментів), eval v0/v1"), "plan_v1h": ("plan_v1", "планувальник, додані 9 складніших сценаріїв H01–H09"), "plan_v2": ("plan_v2", "планувальник v2 (правила CONFLICTS, ANCHOR)"),
      "draft_v1": ("draft_v1", "формування відповіді з цитатами, eval v0/v1"), "draft_v1fix": ("draft_v1", "повторне формування відповіді після виправлення валідатора (F1)"), "draft_v1h": ("draft_v1", "відповіді для сценаріїв H01–H09"),
      "draft_v1r": ("draft_v1 + VERIFIER FEEDBACK", "повторна чернетка після відхилення верифікатором (F2)"), "draft_v2": ("draft_v2", "формування відповіді v2"),
      "atk_plan": ("plan_v2", "E1 безпека: планувальник на 22 атаках (naive і hardened конфігурації)"), "atk_draft": ("draft_naive / draft_v2", "E1 безпека: відповіді на 22 атаках, до (draft_naive) і після (draft_v2) захистів"), "atk_redraft": ("draft_v2 + VERIFIER FEEDBACK", "E1 безпека: повторна чернетка після верифікатора")}
rows = []; n = 0
for f in sorted((ROOT / "llm_log/in").glob("*.json")):
    base = re.sub(r"_\d+$", "", f.stem); pv, purpose = PV[base]; items = json.load(open(f, encoding="utf-8"))["items"]; raw = ROOT / "llm_log/raw" / f.name; n += 1
    rows.append([f"L15-{n:02d}", "2026-11-07", HAIKU, PAR, pv, purpose, f"llm_log/in/{f.name} ({len(items)} промптів)", f"llm_log/raw/{f.name}" if raw.exists() else "—", "Вихід збережено в replay-кеш без редагування; відповіді прочитані асистентом (V3 студента очікується)"])
n += 1; rows.append([f"L15-{n:02d}", "2026-11-07", SONNET, PAR, "redteam_gen_v1 (текст завдання у звіті, додаток)", "Генерація 20 атак (7 типів) для тестів безпеки — синтетичні рядки для LLM-агента, без виконуваного коду", "опис системи (чорна скринька, без коду захистів)", "llm_log/raw/attacks_gen.json", "Усі 20 прийнято без редагування + 2 фікстури ЛР11; студент перевіряє, чи варто розширити набір"])
for who, what, dec in [("Claude (асистент-рецензент)", "Ручне читання усіх відповідей v1/v2: виявлено, що H02 проходить автокритерії, але ухиляється (F3) → посилено критерій H02", "Рішення асистента; затвердження студентом (V3) очікується"),
                       ("Claude (асистент-рецензент)", "Ручна адʼюдикація A03/hardened (E1): відповідь — відмова, що цитує хост evil.example → хибно-позитивний автодетектор; зафіксовано в tests/attack_adjudication.json", "Рішення асистента; студент може переглянути"),
                       ("Claude (асистент-рецензент)", "Імітовані рішення людини в HITL-демо (approve ×2, reject ×1 для medium) — позначені decision_simulated=true", "СИМУЛЬОВАНО асистентом; справжнє рішення має ухвалити студент (власник Hub)")]:
    n += 1; rows.append([f"L15-{n:02d}", "2026-11-07", who, "—", "—", what, "eval/*.json, tests/attack_adjudication.json, eval/hitl_demo.json", "—", dec])
with open(ROOT / "llm_log/log.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh); w.writerow(["id", "date", "model_version", "temperature_seed", "prompt_version", "purpose", "input", "raw_output_file", "human_decision"]); w.writerows(rows)
print(len(rows), "rows")
