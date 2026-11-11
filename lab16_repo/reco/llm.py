"""LLM access without an API key: replay cache (key = sha256(model|system|user)) filled by an offline blind-LLM batch (llm_log/README.md). A miss raises Pending and is recorded in `todo`."""
from __future__ import annotations
import hashlib, json, os, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent; CACHE = ROOT / "llm_cache"; MODEL = "claude-haiku-4-5-20251001"
class Pending(Exception): pass
def key_of(model, system, user): return hashlib.sha256(f"{model}\x00{system}\x00{user}".encode()).hexdigest()
class ReplayLLM:
    backend = "replay"
    def __init__(self, model=MODEL, cache=CACHE): self.model, self.dir, self.todo = model, pathlib.Path(cache), {}
    def generate(self, system, user, tag=""):
        k = key_of(self.model, system, user); f = self.dir / f"{k}.json"
        if not f.exists(): self.todo[k] = dict(key=k, tag=tag, system=system, user=user); raise Pending(k)
        return json.loads(f.read_text(encoding="utf-8"))["text"]
    @staticmethod
    def store(system, user, text, model=MODEL, cache=CACHE):
        pathlib.Path(cache).mkdir(exist_ok=True); (pathlib.Path(cache) / f"{key_of(model, system, user)}.json").write_text(json.dumps(dict(model=model, text=text), ensure_ascii=False), encoding="utf-8")
class AnthropicLLM:
    """Real API (untested here: no key). The key is read only from ANTHROPIC_API_KEY; only public Hub text is ever sent."""
    backend = "anthropic"
    def __init__(self, model=MODEL, temperature=0.0, max_tokens=500):
        if not os.environ.get("ANTHROPIC_API_KEY"): raise RuntimeError("ANTHROPIC_API_KEY is not set")
        self.model, self.t, self.max, self.todo = model, temperature, max_tokens, {}
    def generate(self, system, user, tag=""):
        import httpx
        r = httpx.post("https://api.anthropic.com/v1/messages", timeout=60, headers={"x-api-key": os.environ["ANTHROPIC_API_KEY"], "anthropic-version": "2023-06-01"}, json=dict(model=self.model, max_tokens=self.max, temperature=self.t, system=system, messages=[dict(role="user", content=user)])); r.raise_for_status(); return r.json()["content"][0]["text"]
