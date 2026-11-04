# Лабораторна робота 6. Семантична мережа та концептуальна карта
Область: Медицина / аналіз біомедичних даних. Вхід: таксономія ЛР5, CQ ЛР4, два тексти (GATK hard filtering; CDC cascade testing).

| Результат | Артефакти |
|---|---|
| 1. Фокусне питання, parking lot, каталог | `docs/cmap_focus.md`, `data/relations.json`, `data/concept_types.json` |
| 2. Експертна карта v1 | `models/cmap_expert.json/.png/.drawio`, `scripts/build_expert_map.py`, `scripts/map_tools.py` |
| 3. Триплети LLM | `models/triples_llm.jsonl`, `models/cmap_llm.png`, `scripts/check_triples.py`, `docs/evidence/triples_check.txt` |
| 4. Рубрика Новака | `docs/cmap_rubric.xlsx`, `scripts/eval_maps.py`, `scripts/build_rubric_xlsx.py`, `docs/evidence/map_eval.*`, карта «колеги» `models/cmap_peer.*` |
| 5. Карта v2 | `models/cmap_v2.json/.png/.drawio`, `models/triples_final.csv`, `docs/cmap_changes_v1_v2.md`, `scripts/build_v2.py`, `scripts/validate_v2.py` |
| LLM-експерт | `llm_log/` (`log.csv`, `raw/`, `prompts/`), `claims/claims.csv` + `claims/README.md` |
| Тести | `tests/test_cmap.py`, `docs/evidence/pytest_all.txt` |

## Запуск з нуля
```
python -m venv .venv && source .venv/bin/activate     # Python 3.13 (перевірено), >= 3.10
pip install -r requirements.txt                       # networkx, openpyxl, scipy, scikit-learn, numpy, pytest
# потрібен Graphviz `dot` (apt install graphviz; перевірено 2.43.0); python-docx лише для звіту
# Windows: встановіть Graphviz, додайте його `bin` (зазвичай `C:\Program Files\Graphviz\bin`) до PATH і перезапустіть термінал; перевірте командою `dot -V`
python scripts/build_expert_map.py     # models/cmap_expert.* (v1)
python scripts/check_triples.py --write     # models/triples_llm.jsonl + docs/evidence/triples_check.txt
python scripts/draw_triples_graph.py   # models/cmap_llm.png
python scripts/eval_maps.py            # метрики рубрики, узгодженість, P/R
python scripts/build_v2.py             # models/cmap_v2.*, models/triples_final.csv
python scripts/build_rubric_xlsx.py    # docs/cmap_rubric.xlsx
python scripts/build_claims.py         # claims/claims.csv, llm_log/log.csv, docs/cmap_changes_v1_v2.md
python -m pytest -v                    # 8 passed
```
Скрипти детерміновані (рандомізації немає, seed не потрібен). Витяг триплетів, карта «колеги» й оцінки рубрики — **дослівні виходи LLM** (`llm_log/raw/`), вони не перегенеровуються скриптами. Ключів API у репозиторії немає.
`scripts/import_peer_map.py` перетворює сирий вихід карти «колеги» у `models/cmap_peer.json`; `scripts/build_focus_doc.py` будує `docs/cmap_focus.md`.

## Формат карти
JSON: `concepts` (id, label, kind concept|instance, cluster, type — тип ЛР5 рівня 1, definition), `propositions` (id, s, p, o, cross, explanation). Відношення — лише з `data/relations.json` (12 типів). draw.io: відкрийте `.drawio` у diagrams.net (координати з Graphviz).
