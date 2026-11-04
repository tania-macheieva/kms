"""Shared helpers: normalization, offsets, passage loading."""
import json, re, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
ENT_TYPES = ["Tool", "Procedure", "FileFormat", "Metric", "Option", "Resource"]
REL_TYPES = {"ACCEPTS": ("Tool", "FileFormat"), "PRODUCES": ("Tool", "FileFormat"),
             "PERFORMS": ("Tool", "Procedure"), "HAS_OPTION": ("Tool", "Option"),
             "COMPUTES_METRIC": ("Tool", "Metric"), "USES_RESOURCE": ("Tool", "Resource"),
             "INVOKES": ("Tool", "Tool")}

def norm(s: str) -> str:
    """Normalization rules N1-N4 (docs/extraction_schema.md): strip markup, lowercase,
    drop 'nf-core/' prefix, collapse whitespace/trailing punctuation."""
    s = re.sub(r"[`*_\[\]]", "", s) if not s.startswith("--") else s.strip("`")
    s = s.strip().strip(".,;:()\"'").lower().replace("nf-core/", "")
    return re.sub(r"\s+", " ", s)

def load_passages():
    return [json.loads(l) for l in open(ROOT / "data/passages.jsonl", encoding="utf-8")]

def find_offset(text: str, span: str):
    i = text.find(span)
    if i < 0:
        i = text.lower().find(span.lower())
    return i
