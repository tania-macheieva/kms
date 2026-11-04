"""LLM backends. The RAG code depends only on `LLM.generate(system, user) -> LLMResult`.

 * ReplayLLM   - reads answers recorded in data/llm_cache/ (key = sha256(model|system|user)); used for the evaluation in this
                 repository: answers were produced offline by a blind LLM run (see llm_log/), then replayed deterministically.
 * AnthropicLLM- real API call over HTTPS; key only from the ANTHROPIC_API_KEY environment variable (never stored). NOT tested here (no key).
 * ExtractiveLLM- deterministic non-LLM baseline (best sentences + citations); used for the API demo/tests without any key.
"""
from __future__ import annotations
import hashlib, json, math, os, re, time
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CACHE_DIR = ROOT / "data" / "llm_cache"


def count_tokens(text: str) -> int:
    """Rough token estimate (~4 characters per token for English/Latin, ~2.5 for Cyrillic); real counts come from the API usage field."""
    cyr = len(re.findall(r"[Ѐ-ӿ]", text)); return math.ceil((len(text) - cyr) / 4 + cyr / 2.5)


@dataclass
class LLMResult:
    text: str
    in_tokens: int
    out_tokens: int
    latency_ms: float | None
    backend: str
    model: str


def key_of(model: str, system: str, user: str) -> str:
    return hashlib.sha256(f"{model}\x00{system}\x00{user}".encode()).hexdigest()


class CacheMiss(KeyError): pass


class ReplayLLM:
    backend = "replay"

    def __init__(self, model: str, cache_dir: Path = CACHE_DIR):
        self.model, self.dir = model, Path(cache_dir)

    def generate(self, system, user) -> LLMResult:
        f = self.dir / f"{key_of(self.model, system, user)}.json"
        if not f.exists(): raise CacheMiss(f.name)
        j = json.loads(f.read_text(encoding="utf-8"))
        return LLMResult(j["text"], j["in_tokens"], j["out_tokens"], j.get("latency_ms"), "replay", j["model"])

    @classmethod
    def store(cls, model, system, user, text, latency_ms=None, cache_dir: Path = CACHE_DIR):
        Path(cache_dir).mkdir(parents=True, exist_ok=True)
        j = dict(model=model, text=text, in_tokens=count_tokens(system) + count_tokens(user), out_tokens=count_tokens(text), latency_ms=latency_ms)
        (Path(cache_dir) / f"{key_of(model, system, user)}.json").write_text(json.dumps(j, ensure_ascii=False), encoding="utf-8")


class AnthropicLLM:
    backend = "anthropic"

    def __init__(self, model: str | None = None, temperature=0.0, max_tokens=500):
        self.model = model or os.environ.get("DKH_MODEL", "claude-haiku-4-5-20251001"); self.t, self.max = temperature, max_tokens
        if not os.environ.get("ANTHROPIC_API_KEY"): raise RuntimeError("ANTHROPIC_API_KEY is not set")

    def generate(self, system, user) -> LLMResult:
        import httpx
        t0 = time.perf_counter()
        r = httpx.post("https://api.anthropic.com/v1/messages", timeout=60, headers={"x-api-key": os.environ["ANTHROPIC_API_KEY"], "anthropic-version": "2023-06-01"},
                       json=dict(model=self.model, max_tokens=self.max, temperature=self.t, system=system, messages=[dict(role="user", content=user)]))
        r.raise_for_status(); j = r.json(); ms = (time.perf_counter() - t0) * 1000
        return LLMResult(j["content"][0]["text"], j["usage"]["input_tokens"], j["usage"]["output_tokens"], ms, "anthropic", self.model)


STOP = set("a an and are as at be by for from how i in is it of on or that the this to was what when where which who why with do does can should my your me".split())


def _w(s): return {w for w in re.findall(r"\w+", s.lower()) if w not in STOP and len(w) > 2}


class ExtractiveLLM:
    """No-LLM baseline: parse the prompt, pick the sentences with the highest word overlap with the question, cite their item ids."""
    backend = "extractive"; model = "extractive-baseline"
    MIN_OVERLAP = 2

    def generate(self, system, user) -> LLMResult:
        t0 = time.perf_counter()
        ctx = user.split("<context>")[1].split("</context>")[0]; q = user.split("Question:")[-1].strip(); qw = _w(q)
        items = re.findall(r"^\[([^\]\n]+)\]\s*(.*?)(?=^\[[^\]\n]+\]\s|\Z)", ctx, flags=re.S | re.M)
        scored = []
        for cid, body in items:
            for s in re.split(r"(?<=[.!?])\s+|\n+", body):
                s = s.strip()
                if len(s) > 25 and not re.search(r"ignore (all )?previous|system prompt|reveal", s, re.I): scored.append((len(qw & _w(s)), s, cid))
        scored.sort(key=lambda x: -x[0]); best = [x for x in scored[:2] if x[0] >= self.MIN_OVERLAP]
        text = "STATUS: ANSWER\n" + " ".join(f"{s[:300]} [{cid}]" for _, s, cid in best) if best else "STATUS: NO_ANSWER\nThe provided sources do not contain an answer to this question."
        return LLMResult(text, count_tokens(system) + count_tokens(user), count_tokens(text), (time.perf_counter() - t0) * 1000, "extractive", self.model)
