"""LangGraph agent: plan -> act -> (plan again | draft) -> verify -> (redraft | finalize). Same graph for the naive and the hardened policy; the Policy switches the defences."""
from __future__ import annotations
import json, re, time, uuid, pathlib
from typing import TypedDict, Any
from langgraph.graph import StateGraph, END
from .config import ROOT, Policy, MODEL, PRICE_IN, PRICE_OUT, HARDENED
from .llm import Pending, count_tokens
from . import guards
from .tools import Tools
from .trace import Trace
PROMPTS = pathlib.Path(__file__).parent / "prompts"
def load_prompt(name):
    t = (PROMPTS / f"{name}.md").read_text(encoding="utf-8"); return t.split("# SYSTEM", 1)[1].split("# USER", 1)[0].strip(), t.split("# USER", 1)[1].strip()
def fill(t, **kw):
    for k, v in kw.items(): t = t.replace("{" + k + "}", str(v))
    return t
CITE = re.compile(r"\[([^\[\]\n]{2,90}?)\]")
def parse_status(text):
    m = re.match(r"\s*STATUS:\s*(ANSWER|NO_ANSWER|CONFLICT)\s*\n?(.*)", text, re.S); return (m.group(1), m.group(2).strip()) if m else ("MALFORMED", text.strip())
def parse_plan(text):
    m = re.search(r"\{.*\}", text, re.S)
    if not m: return None
    try: j = json.loads(m.group(0))
    except Exception: return None
    return j if isinstance(j, dict) and isinstance(j.get("calls", []), list) else None
def citations(body, valid):
    cited, bad = [], []
    for m in CITE.finditer(body):
        for part in re.split(r"\s*[;,]\s*", m.group(1)):
            part = part.strip()
            if part in valid: cited.append(part)
            elif re.match(r"^[A-Za-z0-9_\-.]+[#:][A-Za-z0-9_:\-.#]+$", part): bad.append(part)
    return cited, bad
NUM = re.compile(r"(?<![\w.#:])\d+(?:[.,]\d+)?")
def _derived(obs_text):
    """differences and sums of pairs of numbers that occur in the observations (rounded to 4 decimals) -> strings accepted as grounded"""
    nums = sorted({float(x) for x in re.findall(r"(?<![\w.#:])\d+(?:\.\d+)?", obs_text.replace(",", " "))})[:40]; out = set()
    for i, a in enumerate(nums):
        for b in nums[i + 1:]:
            for v in (b - a, a + b): out.add(round(abs(v), 4))
    return out
def ungrounded_numbers(body, question, obs_text, derived=False):
    """numbers in the answer (outside [id] brackets, > 9 or with decimals) that appear neither in the observations nor in the question"""
    b = CITE.sub(" ", body); out = []
    for n in NUM.findall(b):
        n2 = n.replace(",", ".")
        if re.fullmatch(r"\d", n2): continue
        if n in obs_text or n2 in obs_text or n in question: continue
        try:
            if re.search(r"(?<![\d.])" + re.escape(str(float(n2)).rstrip("0").rstrip(".")) + r"(?![\d])", obs_text): continue
        except ValueError: pass
        if derived:
            try:
                if round(abs(float(n2)), 4) in _derived(obs_text): continue
            except ValueError: pass
        out.append(n)
    return out

class S(TypedDict, total=False):
    question: str; role: str; qid: str; calls: list; rounds: int; obs: list; plan_reason: str; cont: bool; answer: str; status: str; cited: list; redrafts: int; feedback: str; steps: int
    tin: int; tout: int; tool_calls: list; flagged: list; verify: dict; guard: list; stop: str; draft_raw: str; t_tools: float

def build(kb, llm, pol: Policy, mem=None, extra_tools=None, poison=None, trace_path=None):
    psys, pusr = load_prompt(pol.plan_prompt); dsys, dusr = load_prompt(pol.draft_prompt); restricted = kb.restricted_values(); graph_schema = kb.schema()
    from hub.semantic import sl
    catalog = "metrics=" + ", ".join(sl.LAYER["metrics"]) + "; dimensions=" + ", ".join(sl.LAYER["dimensions"]) + " (a metric accepts only dimensions of its fact: call-based metrics vs pipeline-day metrics cpu_hours/avg_daily_backlog)"
    ctx = {}      # per-query objects (tools, trace) keyed by qid

    def _gen(st, system, user, tag):
        text, ti, to = llm.generate(system, user, tag=f"{st['qid']}:{tag}"); return text, ti, to
    def n_plan(st):
        c = ctx[st["qid"]]; T: Tools = c["tools"]; tr: Trace = c["trace"]; reg = T.registry()
        if T.denied: tr.ev("tool_registry", rejected=list(T.denied))
        mem_txt = st.get("obs") and ("TOOL RESULTS SO FAR: " + " | ".join(f"[{o['id']}] {o['text'][:120]}" for o in st["obs"][-6:])) or (mem.hint(st["role"], st["question"]) if mem else "none")
        system = fill(psys, tools=json.dumps(reg, ensure_ascii=False), schema=graph_schema, catalog=catalog); user = fill(pusr, role=st["role"], memory=mem_txt, question=st["question"])
        text, ti, to = _gen(st, system, user, "plan"); j = parse_plan(text)
        if j is None: tr.ev("plan", error="unparseable", raw=text[:200]); j = dict(calls=[], reason="parse_error")
        calls = [x for x in j.get("calls", []) if isinstance(x, dict) and "tool" in x]; cap = pol.max_calls; done = len(st.get("tool_calls", [])); room = max(0, pol.max_calls * pol.max_rounds - done)       # total call budget = calls per round x rounds
        cut = calls[:min(cap, room)]
        if len(calls) > len(cut): tr.ev("limit", what="max_calls", planned=len(calls), kept=len(cut))
        tr.ev("plan", round=st.get("rounds", 0) + 1, calls=cut, reason=j.get("reason", ""), cont=bool(j.get("continue")), tokens=[ti, to])
        return dict(calls=cut, plan_reason=j.get("reason", ""), cont=bool(j.get("continue")), rounds=st.get("rounds", 0) + 1, steps=st.get("steps", 0) + 1, tin=st.get("tin", 0) + ti, tout=st.get("tout", 0) + to)
    def n_act(st):
        c = ctx[st["qid"]]; T: Tools = c["tools"]; tr: Trace = c["trace"]; obs = list(st.get("obs", [])); tcs = list(st.get("tool_calls", [])); flagged = list(st.get("flagged", [])); t_used = st.get("t_tools", 0.0); stop = ""
        for call in st.get("calls", []):
            if t_used > pol.max_seconds: stop = "time_limit"; tr.ev("limit", what="max_seconds"); break
            t0 = time.perf_counter(); r = T.call(call["tool"], call.get("args", {})); dt_ = time.perf_counter() - t0; t_used += dt_
            tcs.append(dict(tool=call["tool"], args=call.get("args", {}), ok=r["ok"], error=r["error"], ids=[o["id"] for o in r["obs"]]))
            for o in r["obs"]:
                txt = o["text"]
                if pol.input_filter:
                    txt, fl = guards.sanitize(txt)
                    if fl: flagged.append(o["id"]); tr.ev("input_filter", id=o["id"])
                obs.append(dict(id=o["id"], text=txt[: pol.max_chars_obs + 800]))
            tr.ev("act", tool=call["tool"], args=call.get("args", {}), ok=r["ok"], error=r["error"], ids=[o["id"] for o in r["obs"]], ms=round(dt_ * 1000, 1), preview=(r["obs"][0]["text"][:160] if r["obs"] else ""))
            if r["error"] and not r["ok"]: obs.append(dict(id=f"err#{len(tcs)}", text=f"tool {call['tool']} failed: {r['error']}"))
        return dict(obs=obs, tool_calls=tcs, flagged=flagged, steps=st.get("steps", 0) + len(st.get("calls", [])), stop=stop, t_tools=t_used)
    def r_act(st):
        more = st.get("cont") and not st.get("stop") and st.get("calls") and st.get("rounds", 0) < pol.max_rounds
        if st.get("cont") and not more and st.get("rounds", 0) >= pol.max_rounds: ctx[st["qid"]]["trace"].ev("limit", what="max_rounds")
        return "plan" if more else "draft"
    def n_draft(st):
        c = ctx[st["qid"]]; tr: Trace = c["trace"]
        if st["tin"] + st["tout"] > pol.max_tokens: tr.ev("limit", what="max_tokens"); return dict(answer="Ліміт токенів вичерпано: відповідь не сформовано.", status="NO_ANSWER", cited=[], stop="token_limit", draft_raw="")
        blocks = [f"[{o['id']}] {o['text']}" for o in st.get("obs", [])] or ["(no tool results)"]
        obs_txt = guards.wrap_observations(blocks) if pol.isolate else "\n\n".join(blocks)
        user = fill(dusr, question=st["question"], role=st["role"], observations=obs_txt) + (f"\n\nVERIFIER FEEDBACK (fix and answer again): {st['feedback']}" if st.get("feedback") else "")
        text, ti, to = _gen(st, dsys, user, "draft" + str(st.get("redrafts", 0))); status, body = parse_status(text)
        tr.ev("draft", status=status, redraft=st.get("redrafts", 0), tokens=[ti, to], chars=len(body))
        return dict(answer=body, status=status, draft_raw=text, steps=st.get("steps", 0) + 1, tin=st["tin"] + ti, tout=st["tout"] + to)
    def n_verify(st):
        tr: Trace = ctx[st["qid"]]["trace"]
        if st.get("stop") == "token_limit": return dict(verify=dict(ok=True, skipped="token_limit"))
        valid = {o["id"] for o in st.get("obs", [])}; body, status = st["answer"], st["status"]; cited, bad = citations(body, valid); issues = []
        if status == "MALFORMED": issues.append("output must start with 'STATUS: ANSWER|NO_ANSWER|CONFLICT'")
        if status in ("ANSWER", "CONFLICT") and not cited: issues.append("no valid citation [id] found")
        if bad: issues.append("invalid citation ids (not among the observations): " + ", ".join(sorted(set(bad))))
        if status in ("ANSWER", "CONFLICT"):
            un = ungrounded_numbers(body, st["question"], " ".join(o["text"] for o in st.get("obs", [])), derived=pol.derived_numbers)
            if un: issues.append("numbers not found in the observations: " + ", ".join(sorted(set(un))))
        v = dict(ok=not issues, issues=issues, cited=cited, invalid=bad); tr.ev("verify", **v)
        return dict(verify=v, cited=cited, feedback="; ".join(issues), steps=st.get("steps", 0) + 1)
    def r_verify(st):
        if not pol.verify or st["verify"]["ok"]: return "finalize"
        return "draft" if st.get("redrafts", 0) < pol.max_redraft else "finalize"
    def n_redraft_mark(st): return dict(redrafts=st.get("redrafts", 0) + 1)
    def n_final(st):
        tr: Trace = ctx[st["qid"]]["trace"]; ans, status, guard = st["answer"], st["status"], []
        if pol.verify and not st["verify"]["ok"]:
            bad = set(st["verify"].get("invalid", []))
            if bad or not st["verify"].get("cited") and status in ("ANSWER", "CONFLICT") or status == "MALFORMED":
                ans, status = "Не вдалося підтвердити відповідь джерелами (перевірка цитат не пройдена); відповідь не надається.", "NO_ANSWER"; guard.append("verify_abstain")
            else: guard.append("verify_warning:" + "; ".join(st["verify"]["issues"])[:120])
        if pol.output_guard:
            ans2, reasons = guards.output_guard(ans, st["role"], restricted)
            if reasons: guard += reasons; ans, status = ans2, "NO_ANSWER"; tr.ev("output_guard", reasons=reasons)
        return dict(answer=ans, status=status, guard=guard)
    g = StateGraph(S)
    for name, fn in [("plan", n_plan), ("act", n_act), ("draft", n_draft), ("verify", n_verify), ("redraft", n_redraft_mark), ("finalize", n_final)]: g.add_node(name, fn)
    g.set_entry_point("plan"); g.add_edge("plan", "act"); g.add_conditional_edges("act", r_act, {"plan": "plan", "draft": "draft"}); g.add_edge("draft", "verify")
    g.add_conditional_edges("verify", lambda st: "redraft" if r_verify(st) == "draft" else "finalize", {"redraft": "redraft", "finalize": "finalize"}); g.add_edge("redraft", "draft"); g.add_edge("finalize", END)
    app = g.compile()

    def run(question, role="reader", qid=None, poison=poison, extra_tools=extra_tools):
        qid = qid or uuid.uuid4().hex[:8]; tr = Trace(qid, question, role, pol.name, trace_path); T = Tools(kb, pol, role, extra_tools=extra_tools, poison=poison)
        ctx[qid] = dict(tools=T, trace=tr); st0 = S(question=question, role=role, qid=qid, steps=0, tin=0, tout=0, redrafts=0, rounds=0, obs=[], tool_calls=[])
        try:
            st = app.invoke(st0, config=dict(recursion_limit=60)); pending = False
        except Pending as e: st, pending = dict(st0, answer="", status="PENDING", cited=[], guard=[], verify={}), True
        finally: pass
        res = dict(qid=qid, question=question, role=role, policy=pol.name, answer=st.get("answer", ""), status=st.get("status", ""), cited=st.get("cited", []), tool_calls=st.get("tool_calls", []), steps=st.get("steps", 0),
                   tokens_in=st.get("tin", 0), tokens_out=st.get("tout", 0), cost_usd=round(st.get("tin", 0) * PRICE_IN + st.get("tout", 0) * PRICE_OUT, 6), guard=st.get("guard", []), flagged=st.get("flagged", []), verify=st.get("verify", {}),
                   stop=st.get("stop", ""), denied=T.denied, exfil=T.exfil, rounds=st.get("rounds", 0), redrafts=st.get("redrafts", 0), pending=pending, obs_ids=[o["id"] for o in st.get("obs", [])], plan_reason=st.get("plan_reason", ""))
        tr.close(**{k: res[k] for k in ("status", "answer", "cited", "steps", "cost_usd", "guard", "pending")}); ctx.pop(qid, None)
        if mem and not pending: mem.remember_episode(role, question, [t["tool"] for t in res["tool_calls"]], res["status"])
        return res
    return run
