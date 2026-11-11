"""LLM access without an API key: replay cache (key = sha256(model|system|user)) filled by an offline blind-LLM batch (see llm_log/README.md).
A miss raises Pending; the runner records the prompt in `todo` so that scripts/llm_batches.py can write it to llm_log/in/."""
from __future__ import annotations
import hashlib, json, math, os, re, pathlib
from .config import ROOT, MODEL
CACHE = ROOT / "llm_cache"
class Pending(Exception): pass
def count_tokens(t: str) -> int:
    cyr = len(re.findall(r"[Ѐ-ӿ]", t)); return math.ceil((len(t) - cyr) / 4 + cyr / 2.5)
def key_of(model: str, system: str, user: str) -> str: return hashlib.sha256(f"{model}\x00{system}\x00{user}".encode()).hexdigest()
class ReplayLLM:
    backend = "replay"
    def __init__(self, model=MODEL, cache=CACHE): self.model, self.dir, self.todo = model, pathlib.Path(cache), {}
    def generate(self, system: str, user: str, tag: str = ""):
        k = key_of(self.model, system, user); f = self.dir / f"{k}.json"
        if not f.exists(): self.todo[k] = dict(key=k, tag=tag, system=system, user=user); raise Pending(k)
        j = json.loads(f.read_text(encoding="utf-8")); return j["text"], count_tokens(system) + count_tokens(user), count_tokens(j["text"])
    @staticmethod
    def store(system, user, text, model=MODEL, cache=CACHE):
        pathlib.Path(cache).mkdir(exist_ok=True); (pathlib.Path(cache) / f"{key_of(model, system, user)}.json").write_text(json.dumps(dict(model=model, text=text), ensure_ascii=False), encoding="utf-8")
class AnthropicLLM:
    """Real API (not tested here: no key). Key only from the ANTHROPIC_API_KEY environment variable."""
    backend = "anthropic"
    def __init__(self, model=MODEL, temperature=0.0, max_tokens=700):
        if not os.environ.get("ANTHROPIC_API_KEY"): raise RuntimeError("ANTHROPIC_API_KEY is not set")
        self.model, self.t, self.max, self.todo = model, temperature, max_tokens, {}
    def generate(self, system, user, tag=""):
        import httpx
        r = httpx.post("https://api.anthropic.com/v1/messages", timeout=60, headers={"x-api-key": os.environ["ANTHROPIC_API_KEY"], "anthropic-version": "2023-06-01"},
                       json=dict(model=self.model, max_tokens=self.max, temperature=self.t, system=system, messages=[dict(role="user", content=user)])); r.raise_for_status()
        j = r.json(); return j["content"][0]["text"], j["usage"]["input_tokens"], j["usage"]["output_tokens"]

class CompromisedLLM:
    """Assume-breach brain for the security experiment E2: behaves as a FULLY COMPLIANT model following the attack spec in tests/attacks_obey.json.
    It complies with an instruction only if the trigger text is present in the prompt it receives, otherwise it behaves benignly."""
    backend = "compromised"
    def __init__(self, spec: dict): self.spec, self.todo = spec, {}
    def generate(self, system, user, tag=""):
        kind = tag.split(":")[1] if ":" in tag else ""; prompt = system + "\n" + user; ti = count_tokens(prompt)
        def hit(s): return s and (s.get("trigger") is None or s["trigger"] in prompt)
        if kind == "plan":
            s = self.spec.get("plan2" if "TOOL RESULTS SO FAR" in user else "plan1")
            if hit(s) and s: txt = json.dumps(dict(calls=s["calls"], **{"continue": s["cont"]}, reason="complying"))
            else: txt = json.dumps({"calls": [] if "TOOL RESULTS SO FAR" in user else [dict(tool="search_docs", args=dict(query="QD threshold"))], "continue": False, "reason": "benign"})
        else:
            s = self.spec.get("draft")
            if hit(s) and s:
                if s["text"] == "@mirror":
                    obs = re.findall(r"\[([^\]\n]+)\] (.*?)(?=\n\[[^\]\n]+\] |\n---|\n>>>|\Z)", user.split("TOOL RESULTS:")[-1] if "TOOL RESULTS:" in user else user, re.S)
                    txt = "STATUS: ANSWER\n" + "\n".join(f"[{i}] {t.strip()}" for i, t in obs if not i.startswith("err")) 
                else: txt = s["text"]
            else: txt = "STATUS: NO_ANSWER\nThe hub has no information for this."
        return txt, ti, count_tokens(txt)
