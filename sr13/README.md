# Самостійна робота 13 — Порівняння методів витягу відношень

## Набір та методи

`gold.json` містить 50 речень: 60 золотих трійок `(subject, predicate, object)` і 11 речень без відношень. На тому самому наборі збережено результати трьох методів: правила (`rules_out.json`), spaCy (`spacy_out.json`) і LLM (`llm_out.json`).

## Результати

| Метод | P strict | R strict | F1 strict | P lenient | R lenient | F1 lenient |
|---|---:|---:|---:|---:|---:|---:|
| Правила | 0.500 | 0.133 | 0.211 | 0.750 | 0.200 | 0.316 |
| spaCy | 0.385 | 0.167 | 0.233 | 0.615 | 0.267 | 0.372 |
| LLM | 0.556 | 0.583 | 0.569 | 0.635 | 0.667 | 0.650 |

`metrics.json` містить strict, lenient та subject/object-only метрики; `errors.json` — помилки FP/FN за реченнями. За збереженим прогоном правила витратили ≈1.1 мс, витяг spaCy — ≈200 мс (завантаження моделі ≈278 мс). У `llm_out.json` немає часу, токенів або вартості API, тому вартість LLM-прогону не зафіксована.

За strict оцінкою правила дали 8 TP, 8 FP і 52 FN; spaCy — 10 TP, 16 FP і 50 FN; LLM — 35 TP, 28 FP і 25 FN. Отже, правила в цьому наборі мають найнижче охоплення, spaCy часто помиляється в суб'єкті/об'єкті, а LLM має найвищий F1, але й найбільше хибних позитивних спрацьовувань. LLM також повернула два відношення для речень без золотих фактів.

## Файли та повторний запуск

- `sentences_only.json`, `gold.json` — тестові речення й ручна золота розмітка.
- `m_rules.py`, `m_spacy.py` — реалізації методів.
- `evaluate.py`, `common.py`, `errors.py` — метрики й аналіз помилок.

Потрібні `spaCy`, пакет моделі `en_core_web_sm` і `numpy`. Із PowerShell у цій папці:

```powershell
python -X utf8 m_rules.py
python -X utf8 m_spacy.py
python -X utf8 evaluate.py
python -X utf8 errors.py rules spacy llm
```
