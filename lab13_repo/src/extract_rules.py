"""Method A: rule-based extraction (spaCy en_core_web_md + gazetteers + regex + dependency patterns).
Tuned ONLY on dev passages (see eval/tuning_log.md). Usage:
    python src/extract_rules.py --split dev|test|all --out results/rules_<split>.jsonl
"""
import argparse, json, re, sys, time, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from common import *

PROMPT_VERSION = "rules_v1"
GAZ = json.load(open(ROOT / "data/gazetteer.json", encoding="utf-8"))
DOC_TOOL = {"sarek": "nf-core/sarek", "rare": "nf-core/raredisease", "bcftools": "bcftools",
            "gatk_funco": "Funcotator", "gatk_funcotator": "Funcotator WDL", "gatk_mutect2": "Mutect2",
            "gatk_cnv": "GATK", "gatk_readme": "GATK", "gatk_docker": "GATK", "gatk_pathseq": "PathSeq"}
RE_OPT = re.compile(r"(?<![\w-])(--[A-Za-z][\w\-]*)")
RE_OPT1 = re.compile(r"`(-[A-Za-z][\w\-]*)`")
RE_WDL = re.compile(r"\b([A-Za-z]\w*\.[a-z][a-z_0-9]*)\b(?!\.\w)")
RE_WDL_ROW = re.compile(r"^\s*(?:File\??|String\??|Boolean\??|Int\??|Float\??|Array\[[^\]]+\]\??)\s+([A-Za-z_]\w*)\s+-", re.M)
RE_TOOLRX = [re.compile(r"\b(bcftools [a-z][\w-]+)"), re.compile(r"\b(nf-core/[a-z]+)"), re.compile(r"\b(GATK [A-Z]\w+)")]
VERB_REL = {"produce": "PRODUCES", "output": "PRODUCES", "generate": "PRODUCES", "write": "PRODUCES", "create": "PRODUCES",
            "accept": "ACCEPTS", "take": "ACCEPTS", "read": "ACCEPTS", "require": "ACCEPTS", "input": "ACCEPTS",
            "calculate": "COMPUTES_METRIC", "compute": "COMPUTES_METRIC", "report": "COMPUTES_METRIC",
            "use": "USES_RESOURCE", "run": "INVOKES", "call": "INVOKES", "invoke": "INVOKES", "launch": "INVOKES",
            "detect": "PERFORMS", "identify": "PERFORMS", "annotate": "PERFORMS", "filter": "PERFORMS", "align": "PERFORMS", "map": "PERFORMS"}

def gaz_lookup(kind):
    return sorted(GAZ[kind], key=len, reverse=True)

def find_entities(txt, doc_id):
    ents = []  # (start, end, text, type)
    taken = []
    def add(s, e, t, ty):
        if any(not (e <= a or s >= b) for a, b in taken):
            return
        taken.append((s, e)); ents.append((s, e, t, ty))
    for m in RE_OPT.finditer(txt): add(m.start(1), m.end(1), m.group(1), "Option")
    for m in RE_OPT1.finditer(txt): add(m.start(1), m.end(1), m.group(1), "Option")
    for m in RE_WDL.finditer(txt):
        if GAZ["wdl_prefix"] and m.group(1).split(".")[0] in GAZ["wdl_prefix"]: add(m.start(1), m.end(1), m.group(1), "Option")
    for m in RE_WDL_ROW.finditer(txt): add(m.start(1), m.end(1), m.group(1), "Option")
    for rx in RE_TOOLRX:
        for m in rx.finditer(txt): add(m.start(1), m.end(1), m.group(1), "Tool")
    for ty in ["Tool", "Resource", "FileFormat", "Metric", "Procedure"]:
        for g in gaz_lookup(ty):
            cs = ty in ("FileFormat", "Metric") or len(g) <= 3
            for m in re.finditer(r"(?<![\w-])" + re.escape(g) + r"(?![\w-])", txt, 0 if cs else re.I):
                add(m.start(), m.end(), m.group(0), ty)
    return sorted(ents)

_nlp = None
def nlp():
    global _nlp
    if _nlp is None:
        import spacy
        _nlp = spacy.load("en_core_web_md", disable=["ner"])
    return _nlp

CONTAINERS = {"docker", "singularity", "conda", "bioconda", "biocontainers", "anaconda", "podman", "charliecloud", "apptainer"}  # tuning v1 (dev): rule 5
WDL_SUBJECT = {"Mutect2_Multi": "mutect2_multi_sample", "Mutect2": "mutect2"}                                                   # tuning v1 (dev)

def default_tool(p, ents, pos):
    prev = [e for e in ents if e[3] == "Tool" and e[0] < pos and norm(e[2]) not in CONTAINERS]
    if prev: return prev[-1][2]
    for k, v in DOC_TOOL.items():
        if p["doc_id"].startswith(k): return v
    return None

def find_relations(p, ents):
    txt = p["text"]; rels = {}
    d = nlp()(txt)
    def put(s, r, o, ev_s, ev_e, conf):
        if s and norm(s) != norm(o):
            rels.setdefault((norm(s), r, norm(o)), dict(subject=s, relation=r, object=o, evidence=txt[ev_s:ev_e], start=ev_s, end=ev_e, confidence=conf))
    # (1) options -> nearest preceding tool (context heuristic)
    for s, e, t, ty in ents:
        if ty == "Option":
            if re.match(r"[A-Za-z]\w*\.\w", t): subj = WDL_SUBJECT.get(t.split(".")[0], t.split(".")[0])
            elif not t.startswith("-") and p["doc_id"].endswith("_wdl"): subj = "Funcotator WDL" if "funcotator" in p["doc_id"] else default_tool(p, ents, s)
            else: subj = default_tool(p, ents, s)
            ls = txt.rfind("\n", 0, s) + 1; le = txt.find("\n", e); le = len(txt) if le < 0 else le
            put(subj, "HAS_OPTION", t, ls, le, 0.5 if "." not in t else 0.6)
    # (2) dependency patterns: nsubj(verb) = Tool, dobj/pobj = entity of the right type
    by_span = lambda tok: next((x for x in ents if x[0] <= tok.idx < x[1] or tok.idx <= x[0] < tok.idx + len(tok.text)), None)
    for sent in d.sents:
        ss, se = sent.start_char, sent.end_char
        sents_ents = [x for x in ents if ss <= x[0] < se]
        for tok in sent:
            rel = VERB_REL.get(tok.lemma_.lower())
            if tok.pos_ not in ("VERB", "AUX") or not rel: continue
            subj = [c for c in tok.children if c.dep_ in ("nsubj", "nsubjpass")]
            sub_e = None
            for c in subj:
                for x in sents_ents:
                    if x[3] == "Tool" and x[0] <= c.idx < x[1]: sub_e = x[2]
                if sub_e is None and c.dep_ == "nsubj" and c.pos_ in ("PRON", "NOUN") and c.lemma_.lower() in ("it", "plugin", "tool", "pipeline", "workflow"):
                    sub_e = default_tool(p, ents, tok.idx)
            passive = any(c.dep_ == "nsubjpass" for c in tok.children)
            objs = [x for x in sents_ents if tok.idx < x[0] and x[3] != "Option"]
            if passive and not sub_e:      # "X is run with Tool" is not handled
                continue
            if sub_e is None and tok.lemma_.lower() in ("detect", "identify", "map", "align"): continue
            for x in objs:
                want = {"PRODUCES": "FileFormat", "ACCEPTS": "FileFormat", "COMPUTES_METRIC": "Metric",
                        "USES_RESOURCE": "Resource", "INVOKES": "Tool", "PERFORMS": "Procedure"}[rel]
                if rel == "INVOKES" and norm(x[2]) in CONTAINERS: continue
                if x[3] == want and sub_e: put(sub_e, rel, x[2], ss, se, 0.7)
                elif rel == "USES_RESOURCE" and x[3] == "Tool" and sub_e and x[2] != sub_e and norm(x[2]) not in CONTAINERS: put(sub_e, "INVOKES", x[2], ss, se, 0.55)
    # (3) "X is a workflow designed to <verb phrase>" / "<Tool> is used to <verb phrase>" -> PERFORMS
    for m in re.finditer(r"([A-Za-z][\w/\-\.]+)\**\s+(?:is|are)\s+(?:a\s+|an\s+)?(?:[\w\- ]{0,40}?)(?:designed|used|intended)\s+to\s+([a-z][a-z ]{2,40}?)(?=\s+(?:on|from|for|in|of|with|using|and|,|\.))", txt):
        subj = [x for x in ents if x[3] == "Tool" and x[0] <= m.start(1) < x[1]]
        if subj: put(subj[0][2], "PERFORMS", m.group(2).strip(), m.start(), m.end(2), 0.6)
    return list(rels.values())

def extract(p):
    ents = find_entities(p["text"], p["doc_id"])
    rels = find_relations(p, ents)
    return ents, rels

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--split", default="all"); ap.add_argument("--out", required=True)
    a = ap.parse_args()
    P = [p for p in load_passages() if a.split in ("all", p["split"])]
    t0 = time.perf_counter(); n = 0
    with open(a.out, "w", encoding="utf-8") as f:
        for p in P:
            ents, rels = extract(p)
            for s, e, t, ty in ents:
                f.write(json.dumps(dict(method="rules", kind="entity", passage_id=p["id"], document=p["doc_id"], text=t, type=ty, start=s, end=e,
                                        doc_start=p["start"] + s, model="spacy:en_core_web_md+rules", prompt_version=PROMPT_VERSION, confidence=0.8), ensure_ascii=False) + "\n")
            for r in rels:
                f.write(json.dumps(dict(method="rules", kind="relation", passage_id=p["id"], document=p["doc_id"], **r, doc_start=p["start"] + r["start"],
                                        model="spacy:en_core_web_md+rules", prompt_version=PROMPT_VERSION), ensure_ascii=False) + "\n")
            n += 1
    dt = time.perf_counter() - t0
    json.dump({"method": "rules", "passages": n, "cpu_seconds": round(dt, 2), "seconds_per_passage": round(dt / max(n, 1), 3)}, open(pathlib.Path(a.out).with_suffix(".time.json"), "w"))
    print(f"{n} passages in {dt:.1f}s -> {a.out}")

if __name__ == "__main__":
    main()
