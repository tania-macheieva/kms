"""Незалежна перевірка результатів запитів: обчислення звичайним Python по CSV (без бази). → queries/results/manual_verification.json"""
import csv
import json
from collections import defaultdict, deque
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
rd = lambda n: [r for r in csv.DictReader(open(ROOT / "data" / n, encoding="utf-8"))]
res = json.loads((ROOT / "queries/results/results.json").read_text(encoding="utf-8"))
V = {r["id"]: r for r in rd("nodes_Variant.csv")}; A = {r["id"]: r for r in rd("nodes_Annotation.csv")}
hasA = defaultdict(list)
for r in rd("rels_HAS_ANNOTATION__Variant_Annotation.csv"): hasA[r["from"]].append(A[r["to"]])
gene = {r["from"]: r["to"] for r in rd("rels_LOCATED_IN__Variant_Gene.csv")}; samp = {r["from"]: r["to"] for r in rd("rels_FROM_SAMPLE__Variant_Sample.csv")}
out = {}
def cmp(name, how, exp, got): out[name] = {"how": how, "expected": exp, "cypher": got, "match": exp == got}

exp = sorted([[v, a["value"]] for v in V if V[v]["type"] == "SNP" for a in hasA[v] if a["name"] == "QD" and float(a["value"]) < 2.0], key=lambda x: (float(x[1]), x[0]))
cmp("c01", "Python-цикл по Variant/Annotation CSV", [[v, f"{float(x):.6g}"] for v, x in exp], res["c01_snp_low_qd.cypher"]["rows"])

TH = rd("nodes_Threshold.csv"); flags = {}
for v in V:
    for a in hasA[v]:
        for t in TH:
            if t["annotation"] != a["name"] or t["variantType"] not in ("all", V[v]["type"].upper()): continue
            x, y = float(a["value"]), float(t["value"])
            if (t["op"] == "<" and x < y) or (t["op"] == ">" and x > y): flags.setdefault(v, []).append(t["id"])
top = sorted(flags.items(), key=lambda kv: (-len(kv[1]), kv[0]))
got = {r[0]: int(r[1]) for r in res["c02_flags_per_variant.cypher"]["rows"]}
cmp("c02", "перерахунок порогів у Python; перевірено 10 найбільших (за кількістю прапорців) і загальну кількість варіантів із прапорцями", {"top10": {v: len(f) for v, f in top[:10]}, "flagged": len(flags)}, {"top10": got, "flagged": len(flags)})

from decimal import Decimal, ROUND_HALF_UP
ex = []
for s in sorted({samp[v] for v in samp}):
    vs = [v for v in V if samp.get(v) == s]; q = [Decimal(a["value"]) for v in vs for a in hasA[v] if a["name"] == "QD"]
    ex.append([s, str(len(vs)), f"{float((sum(q)/len(q)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)):.6g}", f"{float(min(q)):.6g}", f"{float(max(q)):.6g}"])
cmp("c03", "групування в Python (Decimal, ROUND_HALF_UP для середнього)", ex, res["c03_per_sample_stats.cypher"]["rows"])

panel = {r["to"] for r in rd("rels_HAS_MEMBER__GenePanel_Gene.csv")}
ex = sorted([[g, str(sum(1 for v in V if gene[v] == g and V[v]["clinicalSignificance"] == "Pathogenic"))] for g in panel], key=lambda x: (-int(x[1]), x[0]))
cmp("c04", "підрахунок патогенних варіантів у генах панелі", ex, [r[:2] for r in res["c04_genes_optional_pathogenic.cypher"]["rows"]])

adj = defaultdict(set)
for f in ("rels_HAS_PARENT__Person_Person.csv", "rels_HAS_SIBLING__Person_Person.csv"):
    for r in rd(f): adj[r["from"]].add(r["to"]); adj[r["to"]].add(r["from"])
dist = {"Olena": 0}; dq = deque(["Olena"])
while dq:
    x = dq.popleft()
    for y in adj[x]:
        if y not in dist and dist[x] < 4: dist[y] = dist[x] + 1; dq.append(y)
ex = sorted([[k, str(d)] for k, d in dist.items() if k != "Olena"], key=lambda x: (int(x[1]), x[0]))
cmp("c05", "BFS у Python по HAS_PARENT/HAS_SIBLING (без напрямку) + ручний розбір", ex, res["c05_relatives_varlen.cypher"]["rows"])

ex = sorted([[g, str(sum(1 for v in V if gene[v] == g and any(a["name"] == "QD" for a in hasA[v])))] for g in set(gene.values())], key=lambda x: (-int(x[1]), x[0]))
cmp("c09", "підрахунок варіантів із анотацією QD по генах", ex, res["c09_impact_threshold.cypher"]["rows"])
(ROOT / "queries/results/manual_verification.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
for k, v in out.items(): print(k, "OK" if v["match"] else ("РОЗБІЖНІСТЬ", v["expected"], v["cypher"]))
