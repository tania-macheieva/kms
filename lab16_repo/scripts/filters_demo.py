"""Demonstrates the quality & access filters of the recommender (R1 C2). python scripts/filters_demo.py > docs/filters_demo.txt"""
import sys, pathlib, collections; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from app.core import Hub
from reco.models import recommend
from reco.data import AS_OF, age_days
h = Hub(); it = h.items; H = [(h.idx["sarek_vc_sarek#h007"], 84)]; seen = {i for i, _ in H}
print("items by sensitivity:", dict(collections.Counter(i["sensitivity"] for i in it)), "| unverified:", [i["id"] for i in it if not i["verified"]])
print("history: sarek_vc_sarek#h007 (mentions QD, FS, SOR, SNP); candidates exclude already-read items; ranking = hybrid\n")
def show(title, **kw):
    r = recommend(h.hyb, it, kw.pop("role"), H, 84, seen, k=680, **kw); sens = collections.Counter(it[i]["sensitivity"] for i in r); unv = [it[i]["id"] for i in r if not it[i]["verified"]]; ages = [age_days(it[i], AS_OF) for i in r]
    print(f"{title}: {len(r)} candidates; by sensitivity {dict(sens)}; unverified {unv}; max age {max(ages) if ages else '-'} d")
show("A reader,    verified_only=True ", role="reader")
show("B reader,    verified_only=False", role="reader", verified_only=False)
show("C analyst,   verified_only=True ", role="analyst")
show("D analyst,   verified_only=False", role="analyst", verified_only=False)
show("E clinician, verified_only=False", role="clinician", verified_only=False)
show("F analyst,   verified_only=False, max_age_days=30 (freshness)", role="analyst", verified_only=False, max_age_days=30)
show("G reader,    verified_only=True,  max_age_days=10", role="reader", max_age_days=10)
r = recommend(h.hyb, it, "reader", H, 84, seen, k=5); print("\nTop-5 for reader:", [it[i]["id"] for i in r])
r = recommend(h.hyb, it, "analyst", H, 84, seen, k=5, verified_only=False); print("Top-5 for analyst without verification filter:", [(it[i]["id"], it[i]["verified"]) for i in r])
r = recommend(h.hyb, it, "clinician", H, 84, seen, k=680, verified_only=False); print("Rank of unverified items WITHOUT the verification filter (clinician, 679 candidates):", {it[i]["id"]: n + 1 for n, i in enumerate(r) if not it[i]["verified"]})
