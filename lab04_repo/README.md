# Лабораторна робота 4. Правила IF–THEN і фрейми з перевіркою на тестових випадках

Предметна область: Медицина / аналіз біомедичних даних (QC геномних варіантів за GATK; каскадне тестування родичів BRCA1/BRCA2).

## Структура

| Шлях                                                 | Зміст                                               | Результат |
| ---------------------------------------------------- | --------------------------------------------------- | --------- |
| `docs/scope_cq.md`                                   | межі, користувачі, 18 CQ                            | Р1        |
| `models/rules.json` (+ `models/history/`)            | 35 правил v1.1 (32 verified, 3 draft), історія v1.0 | Р2        |
| `models/frames.py`, `models/instances.py`            | 12 фреймів, 15 екземплярів                          | Р3        |
| `engine/engine.py`                                   | пряме ланцюжкування, конфлікти, explain             | Р4        |
| `tests/`                                             | золотий набір (40), пастки, фрейми, якість правил   | Р4, Р5    |
| `docs/rules_analysis.md`, `scripts/analyze_rules.py` | аналіз, пастки, виправлення, процес оновлення       | Р5        |
| `docs/evidence/`, `docs/explanations.txt`            | протоколи запусків                                  | усі       |
| `claims/claims.csv`, `llm_log/`                      | протокол LLM-експерта                               | —         |
| `sources/`                                           | два PDF-джерела та їх OCR-тексти                    | —         |

## Запуск (Python ≥ 3.10, pytest)

```
pip install pytest
python -m pytest -v                                        # v1.1: 67 passed, 1 xfailed
python -m pytest -v --rules models/history/rules_v1.0.json tests/test_gold.py   # v1.0: 35/40
python scripts/verify_quotes.py                            # перевірка цитат
python scripts/validate_rules.py                           # схема + перелік винятків
python scripts/analyze_rules.py [файл правил]              # надлишкові / суперечливі / недосяжні
python engine/engine.py                                    # три приклади з поясненням
scripts/make_evidence.sh                                   # перегенерація docs/evidence
```
