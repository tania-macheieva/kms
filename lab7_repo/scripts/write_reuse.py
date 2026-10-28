"""docs/reuse.md: розділ «повторне використання» (результат 1, крок 3) — генерується з class_table.csv."""
import csv
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
rows = list(csv.DictReader(open(ROOT / "models/class_table.csv", encoding="utf-8-sig")))
mesh = [r for r in rows if "MeSH" in r["reuse_mapping"]]; ex5 = [r for r in rows if "ex5:" in r["reuse_mapping"]]
L = ["# Повторне використання зовнішніх онтологій і словників", "",
     "| Ресурс | Як використано | Обґрунтування | Охоплення |", "|---|---|---|---|",
     "| SKOS (W3C) | `skos:definition`, `skos:closeMatch`, `skos:exactMatch`, `skos:note` для визначень і зіставлень | стандартний словник для визначень і зіставлення понять; уже використано в ЛР5; не змінює OWL-семантику | усі класи (визначення), 36 зіставлень |",
     f"| Таксономія ЛР5 (`models/taxonomy.ttl`) | `skos:closeMatch` до `ex5:Cxxx` | зберігає простежуваність від таксономії до онтології; термін може мати кілька класів онтології | {len(ex5)} класів із {len(rows)} |",
     f"| MeSH (NLM) | `skos:exactMatch` / `skos:closeMatch` до дескрипторів | загальноприйнятий біомедичний словник; URI й мітки підтверджено запитом MeSH Lookup API у ЛР5 | {len(mesh)} класів: " + ", ".join(f"{r['label_en']} ({r['reuse_mapping'].split()[-1]})" for r in mesh) + " |", "",
     "Не використано (причини): Sequence Ontology, EDAM, OBI — кандидати для gene/exon/variant і форматів VCF/BAM, але перевірити їхні URI в цьому середовищі не вдалося (ресурси недоступні), тому зіставлень не вписано (план: перевірити через OLS і додати як `skos:closeMatch`). `owl:imports` зовнішніх онтологій не застосовано, щоб модель відкривалась офлайн і HermiT не завантажував мережеві ресурси.", "",
     "Зіставлення залишаються на рівні анотацій (не змінюють логіку); смислову еквівалентність exactMatch/closeMatch оцінила LLM — її має підтвердити студент (див. claims/claims.csv)."]
(ROOT / "docs/reuse.md").write_text("\n".join(L) + "\n", encoding="utf-8")
