"""Нормалізація корпусу термінів → models/terms.csv (+ data/terms_raw.csv з усіма сирими варіантами).

Вхід: data/corpus_spec.py (ручна добірка термінів, синонімів і чернеток визначень),
      sources/*.txt (два тексти-джерела для підрахунку freq).
Правила нормалізації (повний опис — docs/normalization.md):
  N1 регістр: канонічний термін — нижній регістр; скорочення та символи генів (BRCA1, FHIR, SKOS, VCF, GATK) лишаються як є;
  N2 форма: називний відмінок, однина (множинні/відмінкові форми зливаються з канонічним — позначка «~»);
  N3 мова: канонічний термін — українською; англомовні назви, скорочення та синоніми — в alt_labels;
  N4 синоніми зливаються в один канонічний термін (alt_labels через «;»);
  N5 шум (службові слова, «рисунок», «https»…) видаляється; помилки OCR (BRCAZ, VQOSR) відносяться до «~»-варіантів;
  N6 унікальність: канонічні терміни порівнюються без урахування регістру; дублікат = помилка збірки.
"""
import csv
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "data"))
from corpus_spec import NOISE, T                                    # noqa: E402

TEXTS = {k: (ROOT / "sources" / f"{n}.txt").read_text(encoding="utf-8")
         for k, n in (("gatk", "gatk_hard_filtering"), ("cdc", "cdc_cascade_testing"))}
ALL_TEXT = "\n".join(TEXTS.values())


def count(label: str, text: str = None) -> int:
    """Входження ярлика в текст (за замовчуванням — в обидва джерела): короткі скорочення — з урахуванням регістру, решта — без."""
    text = ALL_TEXT if text is None else text
    if not label.isascii():
        return 0
    flags = 0 if (len(label) <= 4 and label.upper() == label) else re.I
    return len(re.findall(r"(?<![A-Za-z0-9])" + re.escape(label) + r"(?![A-Za-z0-9])", text, flags))


def norm_canonical(s: str) -> str:
    s = re.sub(r"\s+", " ", s).strip()
    return s if (s.isupper() or re.search(r"[A-Z]{2,}|[a-z][A-Z]", s) or re.search(r"\d", s)) else s.lower()


def build():
    terms, raw_rows, seen = [], [], set()
    for i, (canon, variants, src, definition) in enumerate(T, 1):
        canon = norm_canonical(canon)
        key = canon.casefold()
        if key in seen:
            raise ValueError(f"дублікат канонічного терміна: {canon}")
        seen.add(key)
        alts = []
        raw_rows.append([canon, f"T{i:03d}", "canonical", src])
        for v in variants:
            if v.startswith("~"):
                raw_rows.append([v[1:], f"T{i:03d}", "inflection/typo", src])
            else:
                alts.append(v)
                raw_rows.append([v, f"T{i:03d}", "synonym", src])
        labels = [canon] + alts
        per = {k: sum(count(x, t) for x in labels) for k, t in TEXTS.items()}
        freq = sum(per.values())
        src = ";".join(k for k, v in per.items() if v) or "domain"      # джерело визначає присутність у текстах
        terms.append({"term_id": f"T{i:03d}", "term": canon, "alt_labels": ";".join(alts), "definition": definition,
                      "def_status": "draft_llm", "source": src, "freq": freq})
    for n in NOISE:
        raw_rows.append([n, "", "noise (видалено)", ""])
    return terms, raw_rows


def main():
    terms, raw_rows = build()
    (ROOT / "models").mkdir(exist_ok=True)
    with open(ROOT / "models" / "terms.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, ["term_id", "term", "alt_labels", "definition", "def_status", "source", "freq"])
        w.writeheader(); w.writerows(terms)
    with open(ROOT / "data" / "terms_raw.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f); w.writerow(["raw", "term_id", "kind", "source"]); w.writerows(raw_rows)
    print(f"сирих рядків: {len(raw_rows)}; канонічних термінів: {len(terms)}; із визначенням: "
          f"{sum(1 for t in terms if t['definition'])}; synonyms→alt_labels: {sum(1 for r in raw_rows if r[2] == 'synonym')}; "
          f"шум видалено: {sum(1 for r in raw_rows if r[2].startswith('noise'))}")


if __name__ == "__main__":
    main()
