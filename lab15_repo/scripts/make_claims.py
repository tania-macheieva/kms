"""claims/claims.csv: claims of the lab-15 report with verification levels V1..V4 (V1 source/data reproducible, V2 tests/SHACL/consistency, V3 human expert, V4 metrics before/after).
Numbers are read from eval/*.json so that the table cannot drift from the results."""
import json, csv, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent; J = lambda p: json.load(open(ROOT / p, encoding="utf-8"))
M = J("eval/metrics.json"); H = J("eval/hitl_demo.json")["metrics"]
def load(n): return J(f"eval/{n}.json")
def succ(n): R = load(n); return sum(r["success"] for r in R), len(R)
n1, h1, n2, h2 = succ("attacks_naive"), succ("attacks_hardened"), succ("e2_naive"), succ("e2_hardened")
rows = [
 ("C01", f"Агент v2 проходить {round(M['v2']['success_share']*M['v2']['n'])} з {M['v2']['n']} сценаріїв за автокритеріями", "fact", "eval/v2.json; eval/metrics.json", "✓", "✓", "pending", "✓", "verified", "відтворюється replay-кешем; критерії грубі; V3 очікується"),
 ("C02", f"v0 (перший стан коду) проходив {round(M['v0']['success_share']*M['v0']['n'])} з {M['v0']['n']} перших сценаріїв; усі 4 збої мали одну причину (валідатор Cypher)", "fact", "eval/v0.json; logs/trace_v0.jsonl", "✓", "✓", "n/a", "✓", "verified", "причина прочитана в трейсі й підтверджена тестом test_literals_are_preserved"),
 ("C03", f"Після виправлення верифікатора кількість повторних чернеток впала з {M['v1']['redrafts']} до {M['v2']['redrafts']}", "fact", "eval/metrics.json", "✓", "✓", "n/a", "✓", "verified", ""),
 ("C04", "Покращення v0→v2 є чистим (held-out) порівнянням", "hypothesis", "docs/agent_eval.md §1", "✗", "✗", "n/a", "✗", "rejected", "9 сценаріїв H01–H09 додано після першого прогону; v0 пройдено лише на перших 16; критерій H02 посилено після читання → не чисте порівняння"),
 ("C05", "Вартість запиту ≈ $0.0027 (haiku)", "hypothesis", "eval/metrics.json", "✓", "n/a", "pending", "n/a", "pending", "токени оцінені за довжиною, ціна $1/$5 за 1 млн — припущення, не перевірено за прайсом"),
 ("C06", "Усі запити запису/процедур у graph_query відхиляються валідатором, граф не змінюється", "rule", "agent/guards.py; tests/test_agent.py (33 параметризованих тести)", "✓", "✓", "n/a", "n/a", "verified", "перевірено для 3 ролей і 11 шаблонів запису; не доводить повноти (нове обхідне формулювання можливе)"),
 ("C07", "Роль reader не бачить Person/Diagnosis/Variant/Annotation/Sample та restricted-чанки", "rule", "agent/config.py LABEL_MIN_ROLE; tests/test_agent.py::test_role_matrix", "✓", "✓", "pending", "n/a", "verified", "матриця ролей протестована; відповідність політиці чутливості — рішення власника Hub (V3)"),
 ("C08", f"E1 (реальна модель): naive {n1[0]}/{n1[1]}, hardened {h1[0]}/{h1[1]} успішних атак", "fact", "eval/attacks_naive.json; eval/attacks_hardened.json", "✓", "✓", "n/a", "✓", "verified", "модель опиралась усім атакам навіть без захистів → захисти не показали вимірюваної користі в E1; 1 хибнопозитив детектора адʼюдиковано вручну (A03)"),
 ("C09", f"E2 (assume-breach): naive {n2[0]}/{n2[1]} успішних, hardened {h2[0]}/{h2[1]}", "fact", "eval/e2_naive.json; eval/e2_hardened.json; tests/attacks_obey.json", "✓", "✓", "pending", "✓", "verified", "поведінка «послушної» моделі — моє припущення (tests/attacks_obey.json); N=22"),
 ("C10", "Агент захищений від непрямої ін'єкції", "hypothesis", "docs/agent_security.md §5", "✗", "✗", "n/a", "✗", "rejected", "ні: парафраз A09 проходить лексичний фільтр; захист багатошаровий, але не повний (залишкові ризики 1–7)"),
 ("C11", "Токен-ізоляція спостережень (<<<UNTRUSTED>>>) зменшує успіх ін'єкцій", "hypothesis", "agent/guards.py wrap_observations", "n/a", "n/a", "n/a", "✗", "pending", "не виміряно: E1 без атак, що вдаються; E2 не моделює ізоляцію"),
 ("C12", "Фальшиве число, що збігається з різницею двох спостережуваних чисел, проходить верифікатор", "fact", "agent/graph.py ungrounded_numbers(derived=True)", "✓", "✓", "n/a", "n/a", "verified", "свідомий компроміс F2; перелічено як залишковий ризик 3"),
 ("C13", f"HITL-демо: {H['proposals']} пропозицій; low авто → staging ({H['by_status']['auto_accepted']}), medium → людина ({H['medium_decided']}, схвалено {H['approved_share_of_decided']*100:.0f}%), high відхилено", "fact", "eval/hitl_demo.json; proposals/*.jsonl", "✓", "✓", "n/a", "✓", "verified", "рішення людини СИМУЛЬОВАНІ асистентом (decision_simulated=true); час схвалення не репрезентативний"),
 ("C14", "Агент не може схвалити власну пропозицію", "rule", "agent/propose_fact.py decide; tests/test_hitl.py", "✓", "✓", "n/a", "n/a", "verified", "approver має бути з APPROVERS; автентифікація справжнього схвалювача не реалізована"),
 ("C15", "Аудит-журнал має хеш-ланцюг і виявляє зміну записів", "fact", "agent/propose_fact.py verify_audit; test_audit_chain_detects_tampering", "✓", "✓", "n/a", "n/a", "verified", "tamper-evident, не tamper-proof"),
 ("C16", "MCP-сервер (5 інструментів) підключається клієнтом через stdio; роль фіксована сервером", "fact", "mcp_server/server.py; logs/mcp_demo_reader.json; logs/mcp_demo_analyst.json", "✓", "✓", "n/a", "n/a", "verified", "перевірено власним клієнтом на SDK mcp 2.3.0; підключення до конкретної IDE (Claude Desktop/Cursor) не перевірялось"),
 ("C17", "Hard filtering здебільшого корисний, коли викликають варіанти у кількох зразках і даних недостатньо для складніших методів (VQSR)", "fact", "sarek_vc_theory#h008 (відповідь агента на S06)", "✓", "✓", "pending", "n/a", "pending", "переказ чанка; явного правила вибору hard filtering проти VQSR у джерелах немає (агент це зазначив); експертна перевірка очікується"),
 ("C18", "Для GATK 4.x поточна вимога Java 17; Java 8/1.8 — застаріле (superseded/outdated_flag)", "fact", "gatk_readme#h001; hub/alternatives.jsonl (CF-JAVA)", "✓", "✓", "pending", "n/a", "verified", "дата чанка = дата завантаження; V3 очікується"),
 ("C19", "Локальні пороги QD 1.5 / FS 45 / SOR 4 — коректні альтернативи вендорським 2/60/3", "hypothesis", "hub/alternatives.jsonl; fixtures ЛР11", "✓", "n/a", "pending", "n/a", "pending", "статус «alternative; рішення очікує людину (V3)»; агент лише повідомляє про суперечність, не обирає"),
 ("C20", "Агент став «безпечним для клінічного застосування»", "hypothesis", "—", "✗", "✗", "n/a", "✗", "rejected", "не стверджується: агент не медичний виріб, відповіді не перевірені клініцистом; синтетичні дані"),
]
with open(ROOT / "claims/claims.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh); w.writerow(["id", "claim", "type", "source", "V1", "V2", "V3", "V4", "status", "comment"]); w.writerows(rows)
ver = sum(r[8] == "verified" for r in rows); rej = [r for r in rows if r[8] == "rejected"]; pen = sum(r[8] == "pending" for r in rows)
(ROOT / "claims/README.md").write_text(f"""# Таблиця тверджень (ЛР15)
Усього {len(rows)}; verified {ver} ({100*ver/len(rows):.0f}%), pending {pen}, rejected {len(rej)} ({', '.join(r[0] for r in rej)}) — причини в стовпці comment.
Рівні: V1 — джерело/дані відтворювані скриптом; V2 — тести/SHACL/узгодженість; V3 — експерт-людина (очікується від студента; ролі людини виконував LLM-асистент); V4 — метрики до/після. «verified» ≠ перевірено людиною: де V3 = pending, твердження лишається на розсуд студента.
Джерела: документація GATK/Sarek/bcftools (корпус ЛР11), граф і реєстр альтернатив (ЛР9/14), склад DuckDB (ЛР12), eval/*.json цієї роботи.
""", encoding="utf-8"); print(len(rows), ver, pen, len(rej))
