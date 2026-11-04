"""Нормалізація корпусу термінів: сирі кандидати → models/terms.csv.

Правила (також у README):
 R1 обрізати пробіли, звести тире/нерозривні пробіли до звичайних;
 R2 ключ порівняння — casefold, дефіс → пробіл, без кінцевої пунктуації;
 R3 однина: кінцеве -ies→-y, -es (після s,x,ch,sh)→-, -s→- (крім слів-виключень, напр. analysis);
 R4 мова: кирилічні форми зіставляються з label_uk, канонічна мова — англійська;
 R5 синоніми й абревіатури зливаються в канонічний термін (alt_labels), довідник — data/curation.py;
 R6 шум (список NOISE) видаляється; нерозпізнані форми потрапляють у звіт, а не в корпус;
 R7 freq — кількість вживань канонічного терміну та його alt_labels у текстах джерел (word boundary, без урахування регістру).
Запуск: python scripts/normalize_terms.py
"""
import csv
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "data"))
from curation import NOISE, T                                    # noqa: E402

SOURCES = {"gatk": ROOT / "sources/gatk_hard_filtering.txt", "cdc": ROOT / "sources/cdc_cascade_testing.txt"}
KEEP_S = {"analysis", "diagnosis", "genomics", "proteomics", "epigenetics", "mass spectrometry", "bias", "chorus"}


def key(s: str) -> str:                                          # R1, R2
    s = s.replace(" ", " ").replace("–", "-").replace("—", "-").strip()
    s = re.sub(r"\s+", " ", s).casefold().replace("-", " ")
    return s.strip(" .,;:")


def singular(k: str) -> str:                                     # R3
    if k in KEEP_S or len(k) < 4:
        return k
    if k.endswith("ies"):
        return k[:-3] + "y"
    if re.search(r"(ss|us|is)$", k):
        return k
    if re.search(r"(sses|xes|ches|shes)$", k):
        return k[:-2]
    return k[:-1] if k.endswith("s") else k


def build_lookup():
    lk = {}
    for canon, uk, alts, _ in T:
        for form in [canon, uk, *[a for a in alts.split(";") if a]]:
            lk[key(form)] = canon
    return lk


def plural(w):
    if w.endswith("s"):
        return w
    return w[:-1] + "ies" if w.endswith("y") and not w.endswith("ay") else w + "s"


def raw_candidates():
    """Сирий список кандидатів: усі форми з джерел кураторської таблиці у різному регістрі/числі + шум."""
    out = []
    for canon, uk, alts, _ in T:
        out += [canon, canon.title(), canon.upper() if len(canon) < 8 else canon, plural(canon), uk]
        out += [a for a in alts.split(";") if a]
    out += NOISE + [n.upper() for n in NOISE[:4]]
    return out


def normalize(raw):
    lk = build_lookup()
    noise = {key(n) for n in NOISE}
    mapped, removed, unmapped = defaultdict(list), [], []
    for r in raw:
        k = key(r)
        if k in noise:
            removed.append(r); continue
        canon = lk.get(k) or lk.get(singular(k))
        if canon:
            mapped[canon].append(r)
        else:
            unmapped.append(r)
    return mapped, removed, unmapped


def count_freq(forms):
    freqs = {}
    for name, path in SOURCES.items():
        text = path.read_text(encoding="utf-8")
        total = 0
        for f in forms:
            f = f.strip()
            if len(f) <= 3 and f.isupper():                      # короткі абревіатури — з урахуванням регістру
                total += len(re.findall(rf"(?<![\w]){re.escape(f)}(?![\w])", text))
            else:
                total += len(re.findall(rf"(?<![\w]){re.escape(f)}(?![\w])", text, flags=re.I))
        freqs[name] = total
    return freqs


def main():
    raw = raw_candidates()
    mapped, removed, unmapped = normalize(raw)
    rows = []
    for i, (canon, uk, alts, definition) in enumerate(sorted(T, key=lambda t: t[0].casefold()), 1):
        forms = [canon] + [a for a in alts.split(";") if a]
        fr = count_freq(forms)
        srcs = [n for n, v in fr.items() if v] or ["llm_domain"]
        rows.append({"id": f"T{i:03d}", "term": canon, "label_uk": uk, "alt_labels": ";".join(a for a in alts.split(";") if a),
                     "definition": definition, "def_status": "llm_draft", "source": ";".join(srcs),
                     "freq": sum(fr.values()), "raw_forms": len(set(mapped[canon]))})
    (ROOT / "models").mkdir(exist_ok=True)
    with open(ROOT / "models/terms.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, list(rows[0])); w.writeheader(); w.writerows(rows)
    c = Counter(r["source"] for r in rows)
    print(f"сирих кандидатів: {len(raw)}; унікальних сирих форм: {len(set(raw))}")
    print(f"видалено шуму: {len(removed)} ({', '.join(sorted(set(x.lower() for x in removed)))})")
    print(f"нерозпізнано: {len(unmapped)} {unmapped[:5]}")
    print(f"канонічних термінів: {len(rows)}; з alt_labels: {sum(1 for r in rows if r['alt_labels'])}; з визначенням: {sum(1 for r in rows if r['definition'])}")
    print(f"злито форм: {sum(len(set(v)) for v in mapped.values())} унікальних форм → {len(rows)} термінів")
    print("джерела:", dict(c))


if __name__ == "__main__":
    main()
