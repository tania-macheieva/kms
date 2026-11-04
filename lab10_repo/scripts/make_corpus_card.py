"""R1: docs/corpus_card.md from data/docs_manifest.json + corpus.jsonl (statistics are computed, not typed)."""
import json, collections, statistics as st
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
M = json.load(open(ROOT / "data/docs_manifest.json", encoding="utf-8")); C = [json.loads(l) for l in open(ROOT / "data/corpus.jsonl", encoding="utf-8")]
cd = collections.Counter(c["doc_id"] for c in C); nw = [c["n_words"] for c in C]
repos = collections.OrderedDict()
for d in M:
    u = d["source_url"]; key = "/".join(u.split("/")[3:5]) if u.startswith("https://github.com") else "own project (ЛР4–ЛР9)"
    repos.setdefault(key, []).append(d)
LIC = {"nf-core/sarek": "MIT", "nf-core/raredisease": "MIT", "samtools/bcftools": "MIT/Expat (dual with GPL)", "broadinstitute/gatk": "Apache-2.0"}
sha = {k: next(d["source_url"].split("/blob/")[1].split("/")[0] for d in v)[:10] for k, v in repos.items() if k in LIC}
L = ["# Картка корпусу (Domain Knowledge Hub, ЛР10)", "",
     f"Корпус: **{len(M)} документів → {len(C)} фрагментів** (стратегія за заголовками, ≤250 слів; медіана {st.median(nw):.0f} слів, мін {min(nw)}, макс {max(nw)}). Файл: `data/corpus.jsonl` (метадані: chunk_id, doc_id, title, section, type, date, sensitivity, source_url, lang, start, end, n_words, text).", "",
     "## 1. Джерела та ліцензії", "", "| Джерело | Версія (commit) | Ліцензія | Документів | Фрагментів | Мова |", "|---|---|---|---|---|---|"]
for k, v in repos.items():
    L.append(f"| {k} | {sha.get(k, 'локальні файли')} | {LIC.get(k, 'власна робота автора (включено до репозиторію; дані синтетичні)')} | {len(v)} | {sum(cd[d['doc_id']] for d in v)} | {v[0]['lang']} |")
L += ["", "Документи — відкрита документація (README, посібники, довідники) інструментів аналізу геномних варіантів, тобто тієї ж предметної області, що й проєкт (біомедичні дані: VCF, анотація, фільтрація). Сирі копії файлів лежать у `data/raw/` (для зовнішніх джерел — з їхньою ліцензією MIT/Apache-2.0, яка дозволяє копіювання з збереженням повідомлення про авторські права), очищені — у `data/docs_clean/`.",
      "Свідомо **не** включено: специфікації GA4GH hts-specs (у репозиторії немає файла ліцензії), Wikipedia, NCBI/PubMed та HuggingFace (недоступні з середовища виконання), CHANGELOG-файли (шум, низька інформативність).", "",
      "## 2. Правила очищення (шум, навігація, колонтитули)", "", "Реалізація — `scripts/build_corpus.py` (`md_clean`, `adoc_clean`); правила застосовуються в такому порядку:", "",
      "| № | Правило | Навіщо |", "|---|---|---|",
      "| R1 | Видалення YAML front matter | службові метадані |", "| R2 | Видалення HTML-коментарів | службові нотатки |", "| R3 | Видалення блоків ```mermaid | діаграми без тексту |",
      "| R4 | Видалення бейджів `[![…](…)](…)` | навігація/статус CI |", "| R5 | Видалення зображень `![…](…)` | немає тексту |", "| R6 | Видалення HTML-тегів (img, p, picture, details…) із збереженням тексту | розмітка |",
      "| R7 | Посилання `[текст](url)` → `текст` | URL не несуть змісту для пошуку |", "| R8 | Callout-блоки `> [!NOTE]` → `NOTE:` | зберегти попередження |", "| R9 | Видалення розділювачів таблиць `|---|` | розмітка |",
      "| R10 | Видалення розділів «Table of contents» | навігація |", "| R11 | Видалення пунктів списку, що є лише якорями `[…](#…)` | навігація |",
      "| R12 | AsciiDoc (bcftools): видалення `//` коментарів | службові |", "| R13 | AsciiDoc: підкреслені заголовки та `=== X` → Markdown `#`; прибрати `+`/`--` | зберегти структуру |",
      "| R14 | AsciiDoc: прибрати `*…*`, `'…'` маркери, `{date}`/`{version}`, екранування `\\<` | розмітка |", "| R15 | Нормалізація пробілів, ≤1 порожній рядок підряд | чистота |", "| R16 | Видалення порожніх заголовків | порожні розділи |", "",
      "Обсяг: сирі файли містили " + f"{sum(d['raw_chars'] for d in M):,}".replace(",", " ") + " символів, після очищення — " + f"{sum(len((ROOT / 'data/docs_clean' / (d['doc_id'] + '.md')).read_text(encoding='utf-8')) for d in M):,}".replace(",", " ") + ". Колонтитулів у Markdown-документації немає; їхній аналог (CI-бейджі, меню, TOC) знято правилами R4, R10, R11.", "",
      "## 3. Чутливість (sensitivity) і доступ", "", "Кожен фрагмент має поле `sensitivity`: **public** — відкрита документація; **internal** — внутрішні звіти проєкту без персональних записів; **restricted** — внутрішні звіти, що містять записи родоводу (імена вигаданих/синтетичних осіб: Olena, Iryna, …) — вони позначені обмеженими, бо за призначенням проєкту такі дані мають потрапляти лише до уповноважених користувачів. Правило призначення: `restricted`, якщо в сирому документі є ім'я з родоводу ЛР7–ЛР9; інакше `internal`; усе з зовнішніх репозиторіїв — `public`.", "",
      "| sensitivity | Документів | Фрагментів |", "|---|---|---|"]
for s in ("public", "internal", "restricted"):
    L.append(f"| {s} | {sum(d['sensitivity'] == s for d in M)} | {sum(c['sensitivity'] == s for c in C)} |")
L += ["", "Pre-filter за `sensitivity` перевірено в `docs/hybrid_report.md`; жодні дані не передавалися зовнішнім сервісам (усі моделі працюють локально).", "",
      "## 4. Типи документів", "", "| type | Документів | Фрагментів |", "|---|---|---|"]
tc = collections.Counter(d["type"] for d in M); tf = collections.Counter(c["type"] for c in C)
for t, n in tc.most_common(): L.append(f"| {t} | {n} | {tf[t]} |")
L += ["", "## 5. Документи", "", "| doc_id | Назва | type | date | sensitivity | Фрагментів |", "|---|---|---|---|---|---|"]
for d in M: L.append(f"| {d['doc_id']} | {d['title'][:60]} | {d['type']} | {d['date']} | {d['sensitivity']} | {cd[d['doc_id']]} |")
L += ["", "`date` — дата останнього коміту файла в репозиторії-джерелі (для власних документів — дата зміни файла).", "",
      "## 6. Відомі прогалини та ризики", "",
      "- **Мова.** 24 з 33 документів англійською, 9 — українською (власні звіти). Доступні в середовищі моделі embeddings — англомовні (multilingual-e5 недоступна, HuggingFace заблоковано), тому для українських запитів якість очікувано нижча; це виміряно окремо в `docs/embeddings_cmp.md`.",
      "- **Дублювання.** Документація sarek і raredisease частково повторює одні й ті самі настанови (nf-core boilerplate) — схожі фрагменти ускладнюють розмітку релевантності.",
      "- **Охоплення.** Немає клінічних настанов (ACMG, ClinVar), немає статей; корпус — технічна документація, а не біомедична література. Запити без відповіді (no_answer) використовують цю прогалину.",
      "- **Таблиці й код.** Таблиці та командні рядки перетворено на текст; частина таблиць після очищення втрачає структуру стовпців.",
      "- **Версії.** Знімки репозиторіїв зафіксовано commit-ами (див. source_url); пізніші зміни документації не відображені.",
      "- **Власні документи** — українською, написані в межах ЛР, містять синтетичні дані; не є джерелом істини щодо медицини.", ""]
(ROOT / "docs/corpus_card.md").write_text("\n".join(L), encoding="utf-8"); print("ok", len(L))
