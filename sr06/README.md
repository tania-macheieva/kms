# Самостійна робота 6 — Оцінювання концептуальних карт

## Завдання

Оцінити три карти за рубрикою Новака, порівняти оцінки з незалежним оцінювачем, виправити не менше п'яти помилок у карті LLM і класифікувати типові помилки.

## Файли та результати

- `models/` — карти для оцінювання.
- `scores_all.json`, `agreement_all.json`, `metrics.json` — оцінки й узгодженість.
- `cmap_llm_fixed.json` та `cmap_llm_fixed.dot` — виправлена карта LLM.
- `SR6_concept_maps_assessment.xlsx` — таблиці оцінювання.
- `chart_scores.png`, `cmap_llm_fixed.png` — діаграми.
- `build6.py`, `draw.py` — побудова таблиць і графіки.

Наявні оцінки R1/R2 створені LLM; незалежної оцінки колеги серед збережених матеріалів немає.

## Перебудова артефактів

Із PowerShell у цій папці:

```powershell
python -X utf8 build6.py
python -X utf8 draw.py
```

Потрібні `openpyxl`, `matplotlib`, `networkx`; для рендерингу карти бажаний Graphviz (`dot`), інакше скрипт використовує fallback.
