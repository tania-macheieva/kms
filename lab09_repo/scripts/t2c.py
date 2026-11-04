"""Конвеєр text-to-Cypher: промпт (схема графа) → LLM → парсер → безпека (лише читання) → перевірка схеми → виконання з LIMIT і таймаутом → порівняння з еталоном.
Read-only забезпечено двічі: (1) статичний фільтр заборонених конструкцій; (2) виконання лише через GRAPH.RO_QUERY — сервер відхиляє будь-який запис
(у Neo4j відповідник — користувач із роллю `reader`/доступом READ). LLM-виклики тут не робляться: сирі відповіді в llm_log/raw/."""
import csv
import json
import re
from pathlib import Path

import graphdb as gdb

ROOT = gdb.ROOT
LIMIT = 100
TIMEOUT_MS = 3000
FORBIDDEN = re.compile(r"\b(CREATE|MERGE|DELETE|DETACH|SET|REMOVE|DROP|LOAD\s+CSV|FOREACH|CALL)\b", re.I)
TYPES = {("Annotation", "value"): "float", ("Person", "ageYears"): "int", ("Person", "deceased"): "bool", ("Person", "proband"): "bool", ("Threshold", "value"): "float",
         ("Variant", "exonEnd"): "bool", ("Procedure", "minTestingAge"): "int", ("Concept", "probability"): "float"}


def schema():
    """{'labels': {Label: [props]}, 'rels': {TYPE: (From, To)}, 'rel_props': [...]} із CSV."""
    labels = {}
    for f in sorted((ROOT / "data").glob("nodes_*.csv")):
        labels[f.stem[6:]] = list(next(csv.reader(open(f, encoding="utf-8"))))
    for lab in labels: labels[lab] += [p for p in ("pagerank", "community") if False]
    rels = {}
    for f in sorted((ROOT / "data").glob("rels_*.csv")):
        t, ends = f.stem[5:].split("__"); a, b = ends.split("_")
        rels.setdefault(t, []).append((a, b))
    return {"labels": labels, "rels": rels, "rel_props": ["source", "confidence", "validFrom"]}


def schema_text():
    s = schema(); L = ["Вузли (мітка {властивість: тип}):"]
    for lab, ps in s["labels"].items(): L.append(f"(:{lab} {{" + ", ".join(f"{p}: {TYPES.get((lab, p), 'string')}" for p in ps) + "})")
    L.append("Усі вузли додатково мають pagerank: float та community: int.")
    L.append("Зв'язки (усі мають властивості source: string, confidence: float, validFrom: date):")
    for t, ends in s["rels"].items(): L.append("; ".join(f"(:{a})-[:{t}]->(:{b})" for a, b in ends))
    return "\n".join(L)


def extract(raw):
    m = re.search(r"```(?:cypher|Cypher)?\s*\n(.*?)```", raw, re.S)
    return (m.group(1) if m else raw).strip().rstrip(";")


def check_safe(q):
    m = FORBIDDEN.search(q)
    return (m is None), (f"заборонена конструкція: {m.group(0).upper()}" if m else "")


def check_schema(q, s=None):
    s = s or schema(); known_labels = set(s["labels"]); known_types = set(s["rels"])
    props = set(s["rel_props"]) | {p for ps in s["labels"].values() for p in ps} | {"pagerank", "community"}
    bad = []
    for lab in re.findall(r"\(\s*\w*\s*:\s*(\w+)", q):
        if lab not in known_labels: bad.append(f"мітка {lab}")
    for blk in re.findall(r"\[[^\]]*\]", q):
        for t in re.findall(r":\s*(\w+(?:\s*\|\s*:?\w+)*)", blk):
            for x in re.split(r"\s*\|\s*:?", t):
                if x and x not in known_types: bad.append(f"тип зв'язку {x}")
    for p in re.findall(r"\.(\w+)", re.sub(r"'[^']*'|\"[^\"]*\"", "''", q)):
        if p not in props and not p.isdigit() and p not in ("id",): bad.append(f"властивість {p}")
    for p in re.findall(r"[{,]\s*(\w+)\s*:", re.sub(r"'[^']*'|\"[^\"]*\"", "''", q)):
        if p not in props: bad.append(f"властивість {p}")
    return (not bad), sorted(set(bad))


def canon(rows):
    def n(x):
        if isinstance(x, bool): return str(x).lower()
        if isinstance(x, float): return f"{x:.6g}"
        if isinstance(x, (list, tuple)): return "[" + ",".join(n(i) for i in x) + "]"
        return "" if x is None else str(x)
    return sorted([n(c) for c in r] for r in rows)


def with_limit(q):
    q = q.rstrip()
    if re.search(r"(?i)\bLIMIT\s+\d+\s*;?$", q):
        return q
    return q.removesuffix(";").rstrip() + f"\nLIMIT {LIMIT}"


def execute(q, limit=True):
    try:
        r = gdb.graph().ro_query(with_limit(q) if limit else q, timeout=TIMEOUT_MS)
        return {"ok": True, "canon": canon(r.result_set), "error": ""}
    except Exception as e:
        return {"ok": False, "canon": None, "error": str(e)[:200]}


def evaluate_one(raw, gold):
    q = extract(raw); r = {"cypher": q, "safe_ok": False, "schema_ok": False, "exec_ok": False, "result_ok": False, "error_stage": "", "detail": ""}
    ok, msg = check_safe(q)
    if not ok: r.update(error_stage="safety", detail=msg); return r
    r["safe_ok"] = True
    ok, bad = check_schema(q); r["schema_ok"] = ok
    if not ok: r.update(error_stage="schema", detail="поза схемою: " + ", ".join(bad)); return r
    ex = execute(q)
    if not ex["ok"]: r.update(error_stage="execution", detail=ex["error"]); return r
    r["exec_ok"] = True
    if ex["canon"] == gold: r["result_ok"] = True
    else: r.update(error_stage="result", detail=f"отримано {json.dumps(ex['canon'], ensure_ascii=False)[:150]}; очікувалось {json.dumps(gold, ensure_ascii=False)[:150]}")
    return r
