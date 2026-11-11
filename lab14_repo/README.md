# Domain Knowledge Hub — ЛР14: якість, очищення та оцінювання сховища знань
Домен: Медицина / «Аналіз біомедичних даних». Сховище під тестом — гібридне сховище ЛР11 (688 чанків, граф 370 вузлів / 757 зв'язків, 34 тести RAG).

## Що тут
| Результат | Де |
|---|---|
| R1 профіль якості (14 метрик, пороги, baseline, пріоритети) | `quality/profile.py`, `quality/thresholds.json`, `quality/metrics.json` (= baseline, з версією і датою), `quality/profile_baseline.md` |
| R2 дедуплікація (золотий набір пар, блокінг, поріг, суддя, merge/unmerge) | `quality/dedup.py`, `quality/pairs_gold.csv`, `scripts/{make_pairs,build_pairs_gold,eval_dedup,make_judge_pairs,run_dedup}.py`, `docs/dedup_card.md` |
| R3 суперечності (8, 4 типи), реєстр альтернатив, журнал рішень | `quality/conflicts.py`, `quality/decisions.csv`, `store_clean/alternatives.jsonl`, `quality/alternatives.cypher`, `quality/conflicts.md` |
| R4 CI: SHACL + SPARQL + JSON Schema + SQL + pytest, гейт, історія, workflow, 3 дефекти | `quality/shapes.ttl`, `quality/tests/`, `quality/gate.py`, `.github/workflows/quality.yml`, `quality/history.jsonl`, `quality/trend.png`, `eval/defect_injection.json` |
| R5 до/після (34 тести RAG), аналіз, процес супроводу | `scripts/run_rag_after.py`, `eval/rag_comparison.json`, `quality/after_report.md` |
| Протокол LLM | `llm_log/` (підказки, вхід, сирий вихід, `log.csv`), `claims/claims.csv` |

`store/` — базовий знімок (ЛР11); `store_clean/` — покращений знімок (дедуплікація, виправлені заголовки/секції, граф без ребра, що порушує правило, реєстр альтернатив, словник аліасів).

## Запуск з нуля (без ключів API)
Потрібні Python 3.12+ і Linux x86_64 або WSL2 (перевірено в Linux; native Windows не підтримується через залежності графового/RAG середовища). Усі команди нижче запускайте з Bash у каталозі `lab14_repo`.
```bash
pip install -r requirements.txt
# 1) ЛР11 потрібна лише для повторного прогону RAG (R5): розпакувати поруч як ../lab11_repo
(cd ../lab11_repo && bash scripts/fetch_models.sh && (cd graph_kb/scripts && python3 import_graph.py))
export LAB11_REPO=$(realpath ../lab11_repo) PYTHONHASHSEED=0
# 2) все разом
bash scripts/run_all.sh
# або лише перевірка якості (без ЛР11):
python3 -m pytest tests -q
python3 quality/gate.py --store store_clean --label ci     # exit 1 при блокуючих помилках
QUALITY_STORE=store python3 -m pytest quality/tests -q     # baseline: очікувано багато збоїв
```
Відповіді LLM відтворюються з `llm_cache/` (sha256(модель|system|user)); нові виклики потребують ANTHROPIC_API_KEY (у коді ключів немає). Особисті/конфіденційні дані зовнішнім сервісам не передавались: всі тексти — публічна документація, синтетичні нотатки та синтетичні персони.

## Чесні обмеження
* Усі анотатори, суддя й «експерт» — LLM однієї родини; золотий набір має лише 17 пар-дублікатів (8 у test) → довірчі інтервали широкі.
* Комбінована оцінка схожості не краща за один TF-IDF на test.
* Базова лінія RAG уже на стелі → вимірюваного приросту на 34 тестах немає (див. `quality/after_report.md`).
* M06 (точність вибірки експертом) і M14 лишаються нижче порогу (попередження).
* Рішення щодо суперечностей — «запропоновано асистентом, очікує схвалення власника (студента)». Доменні твердження про hg19/b37 та Java — з пам'яті моделі, V3 не пройдено.
* Гілка `lab14`.
