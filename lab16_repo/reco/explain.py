"""Explanations generated from a graph path (R3). The explanation is built from a TEMPLATE filled with the path facts; an LLM may only paraphrase it (offline replay cache),
and an automatic checker accepts a text only if every entity, quoted title and number in it is present in the path facts. Also verifies that the path really exists in the graph."""
from __future__ import annotations
import re, json
import numpy as np
from .entities import build_vocab, extract
from .llm import ReplayLLM, Pending
VOCAB = build_vocab(); NUM = re.compile(r"\d+(?:[.,]\d+)?")
SYSTEM = ("Ти перефразовуєш пояснення рекомендації українською ОДНИМ реченням. Дозволено використовувати ЛИШЕ факти з шаблону: не додавай жодних сутностей, назв, чисел чи тверджень, яких немає в шаблоні. "
          "Назви розділів у «лапках», назви сутностей (GATK, bcftools тощо) та числа залиш без змін. Виведи лише перефразоване речення.")
def label(it):
    """unique, short item label: chunk id + (truncated) section heading (headings alone are ambiguous: several chunks share one)"""
    sec = it["section"] if len(it["section"]) <= 60 else it["section"][:59].rstrip() + "…"; return f"{it['id']} · {sec}"
def facts_of(items, cand, path):
    """structured facts of one recommendation; `path` comes from GraphReco/KNNReco.explain_path (or None -> popularity fallback)"""
    f = dict(cand=items[cand]["id"], cand_label=label(items[cand]))
    if path is None: f["kind"] = "popular"; return f
    ids = {it["id"]: it for it in items}; f.update(kind=path["kind"], via=path["via"] if isinstance(path["via"], str) else path["via"], via_label=label(ids[path["via"]]))
    if path["kind"] == "entity": f.update(entity=path["entity"], etype=path["etype"])
    if path["kind"] == "similar": f["cosine"] = path["cosine"]
    return f
def template(f, pop=None):
    c = f"«{f['cand_label']}»"
    if f["kind"] == "entity": return f"Рекомендовано {c}, бо ви читали «{f['via_label']}», і обидва розділи згадують {f['entity']} ({f['etype']})."
    if f["kind"] == "next": return f"Рекомендовано {c}: це розділ, суміжний із прочитаним вами «{f['via_label']}» у тому самому документі."
    if f["kind"] == "doc": return f"Рекомендовано {c} з того самого документа, що й прочитаний вами «{f['via_label']}»."
    if f["kind"] == "similar": return f"Рекомендовано {c}: він змістовно близький до прочитаного вами «{f['via_label']}» (косинусна подібність {f['cosine']})."
    if f["kind"] == "topic": return f"Рекомендовано {c}: один із найчитаніших розділів за темою {f['topic']}, яку ви обрали."
    return f"Рекомендовано {c}: один із найчитаніших розділів Hub для вашої ролі."
def paraphrase(llm, f, tpl):
    """LLM paraphrase (offline replay); on a cache miss returns None and the template is used"""
    user = f"ШАБЛОН: {tpl}\nФАКТИ: {json.dumps({k: v for k, v in f.items() if k not in ('cand', 'via')}, ensure_ascii=False)}"
    try: return llm.generate(SYSTEM, user, tag="explain").strip()
    except Pending: return None
def verify_path(G, E, items, f):
    """the path in the explanation must exist in the graph (Cypher) / embeddings (cosine recomputed)"""
    k = f["kind"]; a, c = f.get("via"), f["cand"]
    if k == "entity": return G.q("MATCH (a:Chunk {id:$a})-[:MENTIONS]->(e:Entity {name:$e})<-[:MENTIONS]-(c:Chunk {id:$c}) RETURN count(e)", a=a, e=f["entity"], c=c)[0][0] > 0
    if k == "next": return G.q("MATCH (a:Chunk {id:$a})-[:NEXT]-(c:Chunk {id:$c}) RETURN count(a)", a=a, c=c)[0][0] > 0
    if k == "doc": return G.q("MATCH (a:Chunk {id:$a})-[:IN_DOC]->(d:Doc)<-[:IN_DOC]-(c:Chunk {id:$c}) RETURN count(d)", a=a, c=c)[0][0] > 0
    if k == "similar":
        pos = {it["id"]: i for i, it in enumerate(items)}; return abs(float(E[pos[a]] @ E[pos[c]]) - f["cosine"]) < 1e-3
    return True            # popularity/topic fallbacks have no graph path
def allowed_facts(f):
    ents = set(extract(f["cand_label"] + " " + f.get("via_label", ""), VOCAB)); ents |= {f["entity"], f["etype"].lower()} if "entity" in f else set()     # the entity and its type word (both are part of the path facts)
    nums = set(NUM.findall(f["cand_label"] + " " + f.get("via_label", ""))); 
    if "entity" in f: nums |= set(NUM.findall(f["entity"]))       # digits that are part of an entity name (hg19, VerifyBamID2)
    if "cosine" in f: nums |= {str(f["cosine"]), str(f["cosine"]).replace(".", ",")}
    labels = {f["cand_label"]} | ({f["via_label"]} if "via_label" in f else set())
    return ents, nums, labels
def check(text, f):
    """automatic consistency check: every entity, quoted title and number must come from the path facts; the cited items/entity must be mentioned"""
    ents, nums, labels = allowed_facts(f); why = []
    ents_cf = {e.casefold() for e in ents}; extra = {n for n in extract(text, VOCAB) if n.casefold() not in ents_cf}
    if extra: why.append(f"entity not in path: {sorted(extra)}")
    quoted = set(re.findall(r"«([^»]+)»", text)); bad = quoted - labels
    if bad: why.append(f"title not in path: {sorted(bad)}")
    stray = {n for n in NUM.findall(text) if n not in nums}
    if stray: why.append(f"number not in path: {sorted(stray)}")
    if f["cand_label"] not in quoted: why.append("recommended item not named")
    if "via_label" in f and f["via_label"] not in quoted: why.append("source item not named")
    if f["kind"] == "entity" and f["entity"] not in text: why.append("path entity not mentioned")
    if f["kind"] == "similar" and not any(n in text for n in (str(f["cosine"]), str(f["cosine"]).replace(".", ","))): why.append("cosine not stated")
    return not why, why
def explain(items, cand, path, llm=None):
    f = facts_of(items, cand, path); tpl = template(f); para = paraphrase(llm, f, tpl) if llm else None
    ok_t, _ = check(tpl, f); out = dict(facts=f, template=tpl, template_ok=ok_t, paraphrase=para)
    if para is not None: ok_p, why = check(para, f); out.update(paraphrase_ok=ok_p, why=why)
    out["final"] = para if para is not None and out["paraphrase_ok"] else tpl; out["used"] = "paraphrase" if out["final"] is para else "template"; return out
TAMPER = {"extra_entity": lambda t, f: t.rstrip(".") + ", так само як у GATK та Mutect2.", "wrong_number": lambda t, f: t.rstrip(".") + " (подібність 0.99).", "wrong_title": lambda t, f: t.replace(f["cand_label"], "sarek_readme: Credits_X"), "drop_source": lambda t, f: t.replace(f"«{f.get('via_label', 'x')}»", "вашого попереднього розділу")}
def tamper_test(facts_list):
    """negative controls: deliberately corrupted explanations must be rejected"""
    res = {k: [0, 0] for k in TAMPER}
    for f in facts_list:
        if f["kind"] == "popular": continue
        t = template(f)
        for k, fn in TAMPER.items():
            bad = fn(t, f)
            if bad == t: continue
            res[k][1] += 1; res[k][0] += (not check(bad, f)[0])
    return {k: dict(rejected=a, total=b) for k, (a, b) in res.items()}
