"""Method B: LLM extraction with JSON schema, closed vocabulary, verbatim evidence and >=2 retries on error.
Usage: python src/extract_llm.py --split dev|test|all --tag dev_v1 --out results/llm_<tag>.jsonl [--prompt v1]
If some prompts are not in the replay cache the run exits with code 3 and writes llm_log/in/pending_<tag>.json (see llm_client.py)."""
import argparse, json, sys, pathlib, re
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from common import *
from llm_client import LLM, CacheMiss

SCHEMA = json.load(open(ROOT / "schema/extraction_output.schema.json"))
MAX_RETRIES = 2
MODEL = "claude-haiku-4-5"

def system_prompt(version):
    return open(ROOT / f"llm_log/prompts/extract_{version}.txt", encoding="utf-8").read()

def validate(obj, text):
    """Returns list of error strings: schema, closed vocabulary, type constraints, verbatim evidence."""
    errs = []
    if not isinstance(obj, dict) or set(obj) != {"entities", "relations"}: return ["top-level must be an object with exactly keys entities, relations"]
    for i, e in enumerate(obj["entities"]):
        if not isinstance(e, dict) or set(e) != {"text", "type"} or not isinstance(e["text"], str) or not e["text"]: errs.append(f"entities[{i}] malformed"); continue
        if e["type"] not in ENT_TYPES: errs.append(f"entities[{i}].type '{e['type']}' not in closed vocabulary {ENT_TYPES}")
        elif e["text"] not in text and e["text"].lower() not in text.lower(): errs.append(f"entities[{i}].text '{e['text']}' not found in the passage")
    for i, r in enumerate(obj["relations"]):
        if not isinstance(r, dict) or set(r) != {"subject", "relation", "object", "evidence"}: errs.append(f"relations[{i}] malformed"); continue
        if r["relation"] not in REL_TYPES: errs.append(f"relations[{i}].relation '{r['relation']}' not in closed vocabulary {list(REL_TYPES)}")
        if not isinstance(r["evidence"], str) or len(r["evidence"]) < 3 or r["evidence"] not in text: errs.append(f"relations[{i}].evidence is not a verbatim substring of the passage")
    return errs

def parse(out):
    m = re.search(r"\{.*\}", out, re.S)
    return json.loads(m.group(0)) if m else None

def run_passage(llm, system, p):
    """Returns (obj, attempts, first_attempt_obj, errors_log); raises CacheMiss if a prompt is missing in the cache."""
    user = f"PASSAGE_ID: {p['id']}\n\n{p['text']}"
    log, first = [], None
    for attempt in range(MAX_RETRIES + 1):
        out = llm.complete(system, user, meta={"passage_id": p["id"], "attempt": attempt})
        try: obj = parse(out); errs = validate(obj, p["text"]) if obj is not None else ["no JSON object in reply"]
        except json.JSONDecodeError as ex: obj, errs = None, [f"invalid JSON: {ex}"]
        if first is None: first = (obj, errs)
        if not errs: return obj, attempt + 1, first, log
        log.append(errs)
        user = (f"PASSAGE_ID: {p['id']}\n\n{p['text']}\n\nYour previous answer was rejected by the validator:\n- " + "\n- ".join(errs[:8]) +
                "\nReturn the corrected full JSON object only.")
    # retries exhausted: keep only valid items (drop fabricated / invalid ones)
    if obj is None: obj = {"entities": [], "relations": []}
    obj = {"entities": [e for e in obj["entities"] if isinstance(e, dict) and e.get("type") in ENT_TYPES and isinstance(e.get("text"), str) and (e["text"].lower() in p["text"].lower())],
           "relations": [r for r in obj["relations"] if isinstance(r, dict) and r.get("relation") in REL_TYPES and r.get("evidence") in p["text"]]}
    return obj, MAX_RETRIES + 1, first, log

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--split", default="dev"); ap.add_argument("--tag", required=True)
    ap.add_argument("--out", required=True); ap.add_argument("--prompt", default="v1")
    a = ap.parse_args()
    system = system_prompt(a.prompt); llm = LLM(MODEL)
    P = [p for p in load_passages() if a.split in ("all", p["split"])]
    rows, stats, missing = [], [], 0
    for p in P:
        try: obj, att, first, log = run_passage(llm, system, p)
        except CacheMiss: missing += 1; continue
        txt = p["text"]
        stats.append({"passage_id": p["id"], "attempts": att, "first_errors": first[1], "first_n_relations": len((first[0] or {}).get("relations", [])),
                      "first_bad_evidence": sum("evidence" in e for e in first[1]), "first_bad_entities": sum("not found" in e for e in first[1])})
        base = dict(method="llm", passage_id=p["id"], document=p["doc_id"], model=MODEL, prompt_version=f"extract_{a.prompt}")
        for e in obj["entities"]:
            i = find_offset(txt, e["text"]); rows.append(dict(base, kind="entity", text=e["text"], type=e["type"], start=i, end=i + len(e["text"]), doc_start=p["start"] + i, confidence=None))
        for r in obj["relations"]:
            i = find_offset(txt, r["evidence"]); rows.append(dict(base, kind="relation", subject=r["subject"], relation=r["relation"], object=r["object"],
                         evidence=r["evidence"], start=i, end=i + len(r["evidence"]), doc_start=p["start"] + i, confidence=None))
    if llm.pending:
        pf = ROOT / f"llm_log/in/pending_{a.tag}.json"
        json.dump({"system_file": f"llm_log/prompts/extract_{a.prompt}.txt", "model": MODEL, "items": list(llm.pending.values())}, open(pf, "w"), ensure_ascii=False, indent=1)
        print(f"{len(llm.pending)} prompts missing from cache -> {pf}; {missing} passages incomplete"); sys.exit(3)
    with open(a.out, "w", encoding="utf-8") as f:
        for r in rows: f.write(json.dumps(r, ensure_ascii=False) + "\n")
    json.dump(stats, open(pathlib.Path(a.out).with_suffix(".stats.json"), "w"), indent=1)
    print(f"{len(P)} passages, {len(rows)} statements, cache hits {llm.hits} -> {a.out}")

if __name__ == "__main__":
    main()
