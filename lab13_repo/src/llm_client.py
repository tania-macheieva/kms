"""LLM access with a replay cache (offline protocol).
Order: (1) cache hit -> return; (2) ANTHROPIC_API_KEY in env and package `anthropic` -> real call, result cached (NOT exercised in this
submission: no key was available); (3) otherwise record the prompt as pending and raise CacheMiss. Pending prompts are answered by
a batch run of a model outside the pipeline and ingested with scripts/ingest_llm.py (see llm_log/README.md). The key is read only from the env."""
import hashlib, json, os, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
CACHE = ROOT / "llm_cache" / "cache.jsonl"

class CacheMiss(Exception):
    pass

def key(model, system, user):
    return hashlib.sha256("\x1f".join([model, system, user]).encode()).hexdigest()

def load_cache():
    d = {}
    if CACHE.exists():
        for l in open(CACHE, encoding="utf-8"):
            r = json.loads(l); d[r["key"]] = r
    return d

class LLM:
    def __init__(self, model="claude-haiku-4-5", temperature=0.0, max_tokens=2000):
        self.model, self.temperature, self.max_tokens = model, temperature, max_tokens
        self.cache = load_cache(); self.pending = {}; self.hits = 0

    def complete(self, system, user, meta=None):
        k = key(self.model, system, user)
        if k in self.cache:
            self.hits += 1; return self.cache[k]["output"]
        if os.environ.get("ANTHROPIC_API_KEY"):
            import anthropic
            c = anthropic.Anthropic()
            r = c.messages.create(model=self.model, max_tokens=self.max_tokens, temperature=self.temperature, system=system,
                                  messages=[{"role": "user", "content": user}])
            out = r.content[0].text
            CACHE.parent.mkdir(exist_ok=True)
            rec = {"key": k, "model": self.model, "output": out, "usage": {"in": r.usage.input_tokens, "out": r.usage.output_tokens}, "live": True}
            open(CACHE, "a", encoding="utf-8").write(json.dumps(rec, ensure_ascii=False) + "\n"); self.cache[k] = rec
            return out
        self.pending[k] = {"key": k, "user": user, **(meta or {})}
        raise CacheMiss(k)
