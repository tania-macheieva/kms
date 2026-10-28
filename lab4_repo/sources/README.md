# Джерела (тексти для витягання правил)

| Ключ | Файл-текст | Оригінал (PDF) | Походження |
|------|------------|----------------|------------|
| `gatk` | `gatk_hard_filtering.txt` | `pdf/gatk_hard_filtering.pdf` | «Hard-filtering germline short variants», GATK Team, Broad Institute (https://gatk.broadinstitute.org/hc/en-us/articles/360035890471-Hard-filtering-germline-short-variants), стаття оновлена 06.11.2024; PDF збережено 14.10.2026 |
| `cdc` | `cdc_cascade_testing.txt` | `pdf/cdc_cascade_testing.pdf` | «About Cascade Testing for Hereditary Breast and Ovarian Cancers», CDC Archive, 14.05.2024 (https://archive.cdc.gov/www_cdc_gov/cascade-testing/about/about-cascade-testing-for-hereditary-breast-and-ovarian-cancer.html); PDF збережено 14.10.2026 |

## Як отримано текстові файли

PDF були створені друком із браузера («Microsoft: Print To PDF») і містять лише зображення без текстового шару.
Текст розпізнано OCR (Tesseract 5, мова `eng`, 200 dpi, `--psm 6`), після чого видалено колонтитули
(дата друку, URL внизу сторінок) і службові рядки замість зображень. Текст більше нічим не редагувався.

Через OCR у файлах є дрібні помилки розпізнавання (наприклад, `BRCAZ` замість `BRCA2`, `VQOSR` замість `VQSR`).
Цитати в `models/rules.json` обрано лише з фрагментів без таких помилок; скрипт `scripts/verify_quotes.py`
звіряє їх із цими файлами. Остаточно цитати слід звірити з PDF-оригіналами в `sources/pdf/`.
