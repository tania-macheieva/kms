# Лабораторна робота 7. Онтологія предметної області та її формалізація
Область: Медицина / аналіз біомедичних даних (контроль якості геномних варіантів; каскадне тестування родичів пробанда з BRCA1/BRCA2). Вхід: таксономія ЛР5, карта й триплети ЛР6, CQ ЛР4.

| Результат | Артефакти |
|---|---|
| 1. Формалізація | `models/class_table.csv` (78 класів), `models/property_dictionary.csv` (35 object + 16 data), `docs/evidence/definition_check.txt`, `scripts/check_definitions.py` |
| 2. OWL-онтологія (Turtle) | `models/onto.owl`, `scripts/onto_model.py` + `scripts/build_onto.py`, `docs/evidence/axioms.txt`, `docs/evidence/rdflib_parse.txt` |
| 3. Індивіди та reasoner | `models/onto_data.ttl`, `models/onto_inferred.ttl`, `docs/reasoner_log.md`, `docs/evidence/hermit_*.txt`, `scripts/build_data.py`, `scripts/reasoner_run.py` |
| 4. Ситуації та метаонтологія | `models/situations.csv`, `models/model_meta.csv`, `tests/sparql_situations/*.rq`, `docs/evidence/situations_queries.txt` |
| 5. Порівняння з LLM, CQ | `docs/onto_eval.md`, `tests/cq_sparql/*.rq` (17), `models/llm_draft.ttl`, `docs/evidence/cq_results_*.csv`, `docs/evidence/onto_compare.*` |
| LLM-експерт | `llm_log/` (`log.csv`, `raw/`, `prompts/`), `claims/claims.csv` + `claims/README.md` |
| Тести | `tests/test_onto.py` (14), `docs/evidence/pytest_all.txt` |

## Запуск з нуля
```
python -m venv .venv && source .venv/bin/activate     # Python 3.13 (перевірено), >= 3.10
pip install -r requirements.txt                        # rdflib 7.6.0, owlready2 0.51 (містить HermiT.jar), networkx, openpyxl, pytest
# потрібні: Java (перевірено OpenJDK 21) і Graphviz `dot` (лише для діаграми)
# Windows: після встановлення JDK додайте його `bin` до PATH або задайте JAVA_HOME; перевірте командою `java -version`.
python scripts/build_onto.py          # models/class_table.csv, property_dictionary.csv, onto.owl, docs/evidence/axioms.txt
python scripts/build_data.py          # models/onto_data.ttl, situations.csv, model_meta.csv
python scripts/check_definitions.py   # перевірка визначень (самопосилання, цикли)
python scripts/check_parse.py         # парсинг rdflib
python scripts/reasoner_run.py        # HermiT: docs/reasoner_log.md, models/onto_inferred.ttl
python scripts/verify_situations.py   # SPARQL-перевірка ситуацій
python scripts/run_cq.py mine llm     # CQ над двома онтологіями
python scripts/compare_onto.py && python scripts/build_eval_doc.py   # docs/onto_eval.md
python scripts/build_claims_lab7.py   # claims/, llm_log/log.csv
python scripts/draw_hierarchy.py      # docs/class_hierarchy.png (потрібен dot)
python -m pytest -v                   # 14 passed
```
Скрипти детерміновані (seed не потрібен). Чернетка онтології `models/llm_draft.ttl` — дослівний вихід LLM (не перегенеровується).
**Protégé:** `File → Open…` `models/onto.owl` (формат Turtle). Індивіди — у `models/onto_data.ttl` (імпортує IRI онтології; при відкритті вкажіть локальний файл `onto.owl` для `http://example.org/dkh/onto`). Для rdflib: `Graph().parse("models/onto.owl", format="turtle")` (розширення `.owl` без `format=` rdflib читає як RDF/XML — помилка).
