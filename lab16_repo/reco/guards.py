"""Input/output guards reused from lab 15 (pure functions): injection filter for untrusted text and secret/canary output filter."""
from __future__ import annotations
import re
INJECTION = re.compile("|".join([
    r"ignore\s+(all\s+|any\s+)?(the\s+)?(previous|prior|above|earlier)\s+(instructions|rules|messages)",
    r"disregard\s+(all\s+|the\s+)?(previous|prior|above|system)", r"system\s+(notice|override|message|prompt)\s*(to|:)", r"admin\s+override",
    r"\bnew\s+instructions?\b", r"you\s+(must|should|have to)\s+(now\s+)?(call|run|execute|use|send|reply|respond|tell|reveal|output)", r"\b(reveal|print|show|output|leak)\b.{0,40}\b(api[ _-]?key|system\s+prompt|secret|password|canary|credentials)",
    r"\b(curl|wget)\b[^\n]{0,80}(http|\|)", r"\breply\s+only\s+with\b", r"\bdo\s+not\s+(tell|mention|reveal)\s+(this|the\s+user)", r"before\s+answering,?\s+(always\s+)?call",
    r"(DETACH\s+)?DELETE\s+\(?\w*\)?|DROP\s+(GRAPH|TABLE|DATABASE)", r"\bsend\b.{0,40}\b(to|via)\b.{0,30}(http|@|webhook|export)", r"call\s+(this\s+tool|search_docs|graph_query)\s+(again|repeatedly|\d+\s+times)", r"repeat\s+(this|the)\s+(step|call|search)",
]), re.I | re.S)

def sanitize(text: str):
    """-> (clean_text, flagged). Sentences/lines matching an injection pattern are replaced by a marker (the rest of the evidence is kept)."""
    flagged = False; out = []
    for line in re.split(r"(?<=[.!?])\s+|\n", text):
        if INJECTION.search(line): flagged = True; out.append("[REMOVED: suspected prompt injection]")
        else: out.append(line)
    return "\n".join(out), flagged


SECRET = re.compile(r"(sk-[A-Za-z0-9_\-]{16,}|\bapi[_ -]?key\s*[:=]\s*\S{8,}|-----BEGIN [A-Z ]*PRIVATE KEY-----|\bpassword\s*[:=]\s*\S{6,})", re.I)
def output_guard(answer: str):
    """-> (answer, reasons): blocks secret-looking strings in an answer"""
    reasons = ["secret_pattern"] if SECRET.search(answer) else []
    return ("Відповідь заблоковано захисним фільтром (можливе витікання секретів).", reasons) if reasons else (answer, reasons)
