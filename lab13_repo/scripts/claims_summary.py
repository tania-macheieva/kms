import csv, collections, pathlib
r = list(csv.DictReader(open(pathlib.Path(__file__).resolve().parent.parent / "claims/claims.csv", encoding="utf-8")))
c = collections.Counter(x["status"] for x in r); print(dict(c), "verified share", round(c["verified"] / len(r), 2))
