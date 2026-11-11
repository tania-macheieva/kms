#!/usr/bin/env python3
"""СР4: продукційні правила триажу варіантів (QC + ACMG-подібна класифікація).
Створює rules_draft.json, rules_fixed.json, analysis.json.
Запуск: python3 sr4.py   (без зовнішніх залежностей, без ключів/мережі)."""
import json, random, itertools, operator

SIB = "SIB training: GATK hard filters (sib-swiss.github.io/NGS-variants-training)"
ACMG = "Richards et al. 2015 (ACMG/AMP), PMID 25741868"
LOC = "лабораторна політика / припущення автора (потребує підтвердження)"

def R(i, conds, then, source, note="", default=False):
    return dict(id=i, **{"if": conds}, then=then, source=source, note=note,
                priority=None, default=default)

# ---------- ЧЕРНЕТКА (27 правил) ----------
draft = [
 R("R01", [["type","==","SNP"],["QD","<",2]], {"qc":"FAIL"}, SIB),
 R("R02", [["type","==","SNP"],["QUAL","<",30]], {"qc":"FAIL"}, SIB),
 R("R03", [["type","==","SNP"],["SOR",">",3]], {"qc":"FAIL"}, SIB),
 R("R04", [["type","==","SNP"],["FS",">",60]], {"qc":"FAIL"}, SIB),
 R("R05", [["type","==","SNP"],["MQ","<",40]], {"qc":"FAIL"}, SIB),
 R("R06", [["type","==","SNP"],["MQRankSum","<",-12.5]], {"qc":"FAIL"}, SIB),
 R("R07", [["type","==","SNP"],["ReadPosRankSum","<",-8]], {"qc":"FAIL"}, SIB),
 R("R08", [["type","==","INDEL"],["QD","<",2]], {"qc":"FAIL"}, SIB),
 R("R09", [["type","==","INDEL"],["QUAL","<",30]], {"qc":"FAIL"}, SIB),
 R("R10", [["type","==","INDEL"],["FS",">",200]], {"qc":"FAIL"}, SIB),
 R("R11", [["type","==","INDEL"],["ReadPosRankSum","<",-20]], {"qc":"FAIL"}, SIB),
 R("R12", [["QD","<",2]], {"qc":"FAIL"}, SIB, "узагальнене правило для будь-якого типу"),
 R("R13", [["DP","<",10]], {"qc":"FAIL"}, LOC, "мінімальна глибина покриття"),
 R("R14", [["qc","==","PASS"],["af",">=",0.05]], {"class":"Benign"}, ACMG, "BA1: AF>5% (stand-alone)"),
 R("R15", [["qc","==","PASS"],["lof","==",True],["lof_mech","==",True],["in_gnomad","==",False]],
        {"class":"Likely pathogenic"}, ACMG, "PVS1 + PM2"),
 R("R16", [["qc","==","PASS"],["clinvar","==","pathogenic"]], {"class":"Pathogenic"},
        "ClinVar (експертно перевірені записи) + ACMG/AMP 2015", "потрібен рівень рев'ю у реальній системі"),
 R("R17", [["qc","==","PASS"],["clinvar","==","benign"]], {"class":"Benign"}, "ClinVar + ACMG/AMP 2015"),
 R("R18", [["qc","==","PASS"],["in_gnomad","==",False],["insilico","==","damaging"]],
        {"class":"VUS"}, ACMG + "; ClinGen SVI (PM2_Supporting)", "PM2+PP3 → VUS"),
 R("R19", [["qc","==","PASS"],["af",">=",0.01],["insilico","==","benign"]],
        {"class":"Likely benign"}, ACMG, "BS1 + BP4 (спрощено)"),
 R("R20", [["qc","==","PASS"]], {"class":"VUS"}, ACMG, "типовий результат за відсутності доказів", default=True),
 R("R21", [["qc","==","PASS"],["in_gnomad","==",False]], {"action":"discard"}, LOC,
        "евристика «новий варіант = артефакт»"),
 R("R22", [["qc","==","FAIL"]], {"action":"do_not_report_confirm"}, SIB + "; практика ортогонального підтвердження"),
 R("R23", [["class","==","Pathogenic"]], {"action":"report"}, ACMG),
 R("R24", [["class","==","Likely pathogenic"]], {"action":"report"}, ACMG),
 R("R25", [["class","in",["Benign","Likely benign"]]], {"action":"no_report"}, ACMG),
 R("R26", [["qc","==","PASS"],["DP","<",10]], {"class":"VUS"}, LOC, "низька глибина → VUS"),
 R("R27", [["qc","==","PASS"],["clinvar","==","pathogenic"]], {"class":"Pathogenic"},
        "ClinVar + ACMG/AMP 2015", "копія з іншого переліку SOP"),
 R("R28", [["class","==","VUS"]], {"action":"list_in_VUS_section"}, ACMG),
]

# ---------- ВИПРАВЛЕНА ВЕРСІЯ ----------
def make_fixed(d):
    drop = {"R01","R08","R27","R21","R26"}
    prio = {"R16":90,"R17":90,"R14":80,"R19":60,"R15":70,"R18":50,"R20":0,
            "R22":100,"R23":50,"R24":50,"R25":50,"R28":50}
    out = []
    for r in d:
        if r["id"] in drop: continue
        r = json.loads(json.dumps(r))
        if r["id"] in prio: r["priority"] = prio[r["id"]]
        if r["id"] == "R14":
            r["if"].append(["clinvar","!=","pathogenic"])
            r["note"] += "; виняток: курований ClinVar «pathogenic» (напр. відомі винятки BA1 за ClinGen SVI)"
        out.append(r)
    return out
fixed = make_fixed(draft)

# ---------- РУШІЙ ----------
OPS = {"<":operator.lt,"<=":operator.le,">":operator.gt,">=":operator.ge,
       "==":operator.eq,"!=":operator.ne}
def cond_ok(c, facts):
    f, op, v = c
    x = facts.get(f)
    if x is None: return False          # відсутня анотація → умова хибна
    if op == "in": return x in v
    return OPS[op](x, v)
def matches(r, facts): return all(cond_ok(c, facts) for c in r["if"])
def attr_of(r): return next(iter(r["then"]))

def run(rules, facts, strategy):
    """qc → class → action. strategy: 'first' (порядок файлу) | 'resolved' (priority>specificity>мета-правило)."""
    st = dict(facts)
    fired = {"qc":[], "class":[], "action":[]}
    qc_rules = [r for r in rules if attr_of(r)=="qc"]
    f = [r for r in qc_rules if matches(r, st)]
    st["qc"] = "FAIL" if f else "PASS"; fired["qc"] = f
    for attr in ("class","action"):
        cands = [r for r in rules if attr_of(r)==attr and matches(r, st)]
        fired[attr] = cands
        if not cands: continue
        if strategy == "first":
            pick = cands[0]; val = pick["then"][attr]
        else:
            cands2 = sorted(cands, key=lambda r: (-(r["priority"] or 0), -len(r["if"])))
            top = cands2[0]
            ties = [r for r in cands2 if (r["priority"] or 0)==(top["priority"] or 0)
                    and len(r["if"])==len(top["if"]) and r["then"][attr]!=top["then"][attr]]
            if ties:   # мета-правило: нерозв'язний конфлікт → консервативно
                val = "VUS" if attr=="class" else "manual_review"
            else: val = top["then"][attr]
        st[attr] = val
    return st, fired

# ---------- ФАЗЗ-ГЕНЕРАТОР ----------
GRID = dict(QD=[0.5,1.9,2,5,20], QUAL=[10,29,30,200], SOR=[1,3,3.1,5], FS=[1,60,61,100,200,201],
            MQ=[30,39,40,60], MQRankSum=[-15,-12.5,-5,0], ReadPosRankSum=[-25,-20,-8.5,-8,0],
            DP=[5,9,10,30,100])
CLEAN = dict(QD=[5,20], QUAL=[200], SOR=[1], FS=[1], MQ=[60], MQRankSum=[0,-5], ReadPosRankSum=[0,-5], DP=[30,100])
def gen(rng):
    clean = rng.random() < 0.6
    g = CLEAN if clean else GRID
    f = {"type": rng.choice(["SNP","INDEL"])}
    for k, vals in g.items():
        if k in ("MQRankSum","ReadPosRankSum") and rng.random()<0.1: continue
        f[k] = rng.choice(vals)
    if rng.random() < 0.15: f["DP"] = rng.choice([5,9])      # бувають низькі DP при чистих інших метриках
    f["in_gnomad"] = rng.random() < 0.6
    if f["in_gnomad"]: f["af"] = rng.choice([1e-5,5e-4,0.005,0.01,0.02,0.05,0.07,0.12])
    f["insilico"] = rng.choice(["damaging","benign","uncertain"])
    f["clinvar"] = rng.choice(["none","none","pathogenic","benign"])
    f["lof"] = rng.random() < 0.3
    f["lof_mech"] = f["lof"] and rng.random() < 0.7
    return f

# ---------- АНАЛІЗ ----------
def analyze(rules, N=100000, seed=7):
    rng = random.Random(seed)
    fires = {r["id"]: set() for r in rules}
    pair = {}   # (a,b,attr) -> кількість
    for n in range(N):
        facts = gen(rng)
        st, fired = run(rules, facts, "first")
        for attr in ("qc","class","action"):
            for r in fired[attr]: fires[r["id"]].add(n)
        for attr in ("class","action"):
            c = [r for r in fired[attr] if not r["default"]]
            for a, b in itertools.combinations(c, 2):
                if a["then"][attr] != b["then"][attr]:
                    key = (a["id"], b["id"], attr)
                    pair[key] = pair.get(key, 0) + 1
    by = {r["id"]: r for r in rules}
    # дублікати (статично)
    dups = []
    for a, b in itertools.combinations(rules, 2):
        if sorted(map(json.dumps,a["if"]))==sorted(map(json.dumps,b["if"])) and a["then"]==b["then"]:
            dups.append([a["id"], b["id"]])
    # надлишковість (динамічно: A спрацьовує ⇒ B спрацьовує з тим самим висновком)
    redund = []
    for a, b in itertools.permutations(rules, 2):
        if a["then"]==b["then"] and not b["default"] and fires[a["id"]] and fires[a["id"]] <= fires[b["id"]] \
           and [a["id"], b["id"]] not in dups and [b["id"], a["id"]] not in dups:
            redund.append([a["id"], b["id"]])
    # конфлікти
    conflicts = [dict(a=a, b=b, attr=at, n=n, then_a=by[a]["then"][at], then_b=by[b]["then"][at])
                 for (a,b,at), n in sorted(pair.items())]
    # недосяжні: ніколи не спрацьовують
    never = [r["id"] for r in rules if not fires[r["id"]]]
    # статичне пояснення: qc==PASS + умова, що вже є умовою QC-FAIL правила
    def implied(cond, conds):
        f, op, v = cond
        for g, op2, v2 in conds:
            if g != f: continue
            if (g,op2,v2)==(f,op,v): return True
            if op in ("<","<=") and op2 in ("<","<=") and v2 <= v: return True
            if op in (">",">=") and op2 in (">",">=") and v2 >= v: return True
        return False
    why = {}
    for rid in never:
        r = by[rid]
        if ["qc","==","PASS"] in r["if"]:
            own = [c for c in r["if"] if c[0] != "qc"]
            for q in rules:
                if attr_of(q)=="qc" and all(implied(c, own) for c in q["if"]):
                    why[rid] = f"умова еквівалентна/сильніша за QC-FAIL правило {q['id']} → qc завжди FAIL"
                    break
    return dict(N=N, dups=dups, redundant=redund, conflicts=conflicts, unreachable=never, unreachable_why=why,
                fired_counts={k: len(v) for k, v in fires.items()})

def ties(rules, N=100000, seed=7):
    rng = random.Random(seed); t = 0; changed = 0
    for _ in range(N):
        f = gen(rng)
        a, _x = run(rules, f, "first"); b, _y = run(rules, f, "resolved")
        if (a.get("class"), a.get("action")) != (b.get("class"), b.get("action")): changed += 1
        if b.get("class")=="VUS" or b.get("action")=="manual_review":
            pass
        if b.get("action")=="manual_review": t += 1
    return dict(N=N, manual_review=t, outcome_differs_from_file_order=changed)

# ---------- 10 ТЕСТОВИХ СИТУАЦІЙ (очікування зафіксовано до запуску рушія) ----------
def base(**kw):
    f = dict(type="SNP", QD=10, QUAL=300, SOR=1, FS=1, MQ=60, MQRankSum=0, ReadPosRankSum=0, DP=40,
             in_gnomad=True, af=0.0005, insilico="uncertain", clinvar="none", lof=False, lof_mech=False)
    f.update(kw); return f
def novel(**kw):
    f = base(in_gnomad=False); f.pop("af"); f.update(kw); return f
TESTS = [
 ("T1","SNP, QD=1.2 (низька якість)", base(QD=1.2), dict(qc="FAIL", action="do_not_report_confirm", cls=None)),
 ("T2","Новий LoF-варіант у гені з LoF-механізмом + ClinVar pathogenic",
       novel(lof=True, lof_mech=True, insilico="damaging", clinvar="pathogenic"),
       dict(qc="PASS", cls="Pathogenic", action="report")),
 ("T3","Поширений (AF=12 %), in silico benign", base(af=0.12, insilico="benign"),
       dict(qc="PASS", cls="Benign", action="no_report")),
 ("T4","AF=7 %, але курований ClinVar pathogenic (виняток BA1)", base(af=0.07, clinvar="pathogenic"),
       dict(qc="PASS", cls="Pathogenic", action="report")),
 ("T5","Новий варіант, in silico damaging, не LoF, ClinVar немає", novel(insilico="damaging"),
       dict(qc="PASS", cls="VUS", action="list_in_VUS_section")),
 ("T6","INDEL, FS=250", base(type="INDEL", FS=250), dict(qc="FAIL", action="do_not_report_confirm", cls=None)),
 ("T7","INDEL, FS=100 (для SNP було б FAIL, для INDEL ні)", base(type="INDEL", FS=100),
       dict(qc="PASS", cls="VUS", action="list_in_VUS_section")),
 ("T8","DP=8 при інших чистих метриках", base(DP=8), dict(qc="FAIL", action="do_not_report_confirm", cls=None)),
 ("T9","ClinVar benign, AF=0.1 %", base(clinvar="benign", af=0.001), dict(qc="PASS", cls="Benign", action="no_report")),
 ("T10","Новий LoF-варіант (LoF-механізм), in silico damaging, ClinVar немає",
       novel(lof=True, lof_mech=True, insilico="damaging"),
       dict(qc="PASS", cls="Likely pathogenic", action="report")),
]
def run_tests(rules, strat):
    res = []
    for tid, desc, facts, exp in TESTS:
        st, _ = run(rules, facts, strat)
        got = dict(qc=st.get("qc"), cls=st.get("class"), action=st.get("action"))
        res.append(dict(id=tid, desc=desc, expected=exp, got=got, ok=(got==exp)))
    return res

# ---------- «АДВОКАТ ДИЯВОЛА» (сценарії, запропоновані LLM; перевіряє рушій) ----------
DEVIL = [
 ("D1","Поширений варіант (AF 7 %) з ClinVar pathogenic: BA1 проти ClinVar", base(af=0.07, clinvar="pathogenic")),
 ("D2","Новий LoF + ClinVar pathogenic: Likely pathogenic чи Pathogenic?", novel(lof=True, lof_mech=True, clinvar="pathogenic")),
 ("D3","Новий LoF, in silico damaging: LP проти VUS, і «report» проти «discard»", novel(lof=True, lof_mech=True, insilico="damaging")),
 ("D4","ClinVar pathogenic, AF 2 %, in silico benign: P проти LB", base(af=0.02, insilico="benign", clinvar="pathogenic")),
 ("D5","Чистий QC, але DP=8 — чи спрацює правило низької глибини-VUS?", base(DP=8)),
]
def devil(rules):
    out = []
    for did, d, facts in DEVIL:
        st, fired = run(rules, facts, "first")
        out.append(dict(id=did, scenario=d,
            fired_class=[r["id"] for r in fired["class"]], fired_action=[r["id"] for r in fired["action"]],
            qc=st["qc"], result_first=dict(cls=st.get("class"), action=st.get("action"))))
    return out

if __name__ == "__main__":
    for name, rules in (("rules_draft.json", draft), ("rules_fixed.json", fixed)):
        json.dump(dict(domain="Триаж варіантів: QC за GATK + спрощена ACMG-класифікація",
                       conflict_strategy=("порядок файлу" if name=="rules_draft.json" else
                           "priority → specificity → мета-правило (нерозв'язний конфлікт → VUS/manual_review)"),
                       closed_world="qc=PASS, якщо жодне QC-FAIL правило не спрацювало; відсутня анотація → умова хибна",
                       rules=rules), open(name,"w"), ensure_ascii=False, indent=1)
    out = dict(draft=analyze(draft), fixed=analyze(fixed),
               tests_before=run_tests(draft,"first"), tests_after=run_tests(fixed,"resolved"),
               tests_fixed_rules_first=run_tests(fixed,"first"),
               devil=devil(draft), n_draft=len(draft), n_fixed=len(fixed))
    out["fixed_ties"] = ties(fixed)
    # залишкові неузгодженості виправленої версії під стратегією resolved: пари з рівним пріоритетом і специфічністю
    json.dump(out, open("analysis.json","w"), ensure_ascii=False, indent=1)
    print("rules", len(draft), "->", len(fixed))
    a = out["draft"]
    print("dups", a["dups"]); print("redundant", a["redundant"]); print("unreachable", a["unreachable"], a["unreachable_why"])
    for c in a["conflicts"]: print("conflict", c)
    print("fixed: dups", out["fixed"]["dups"], "red", out["fixed"]["redundant"], "unr", out["fixed"]["unreachable"])
    for c in out["fixed"]["conflicts"]: print("fixed-conflict(file-order view)", c)
    print("ties", out["fixed_ties"])
    print("before", sum(t["ok"] for t in out["tests_before"]), "/10; after", sum(t["ok"] for t in out["tests_after"]), "/10")
    for t in out["tests_before"]+out["tests_after"]:
        if not t["ok"]: print("FAIL", t["id"], t["got"], "exp", t["expected"])
    for d in out["devil"]: print(d)
