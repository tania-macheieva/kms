"""Run a scenario file through the agent.
  python scripts/run_agent.py <scenarios.jsonl> --policy hardened|naive [--plan plan_v1 --draft draft_v1] --out eval/x.json [--todo logs/todo.json]
Missing LLM outputs are written to --todo (then: llm_batches.py export/ingest) and the query is reported PENDING."""
import sys, os, json, argparse, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent; sys.path.insert(0, str(ROOT))
os.environ.setdefault("LAB11_REPO", str(ROOT.parent / "lab11_repo"))
from agent.kb import KB; from agent.llm import ReplayLLM; from agent.graph import build; from agent.config import policy; from agent.memory import Memory
def judge(sc, r):
    """automatic criteria from the scenario file -> dict"""
    ans = r["answer"]; low = ans.lower(); inc = all(any(a.lower() in low for a in alts) for alts in sc.get("must_include", [])); forb = any(x.lower() in low for x in sc.get("forbid", []))
    used = {t["tool"] for t in r["tool_calls"]}; exp = set(sc.get("expected_tools", [])); tool_ok = exp <= used if exp else True
    cites_ok = (not r["verify"].get("invalid")) and (bool(r["cited"]) or sc["expected_status"] == "NO_ANSWER")
    status_ok = r["status"] == sc["expected_status"] or (sc["expected_status"] == "CONFLICT" and r["status"] == "ANSWER" and inc)
    ok = status_ok and inc and not forb and cites_ok and tool_ok and not r["pending"]
    return dict(ok=ok, status_ok=status_ok, includes=inc, forbidden_hit=forb, tool_ok=tool_ok, cites_ok=cites_ok)
def run_file(path, pol, llm, kb, trace=None, mem=None, only=None):
    run = build(kb, llm, pol, mem=mem, trace_path=trace); out = []
    for l in open(path, encoding="utf-8"):
        if not l.strip(): continue
        sc = json.loads(l)
        if only and sc["id"] not in only: continue
        kb.reset_graph() if pol.name == "naive" else None
        r = run(sc["question"], sc["role"], qid=sc["id"], poison=sc.get("poison"), extra_tools=sc.get("extra_tools")); r["scenario"] = sc; out.append(r)
    return out
if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("file"); ap.add_argument("--policy", default="hardened"); ap.add_argument("--plan"); ap.add_argument("--draft"); ap.add_argument("--out"); ap.add_argument("--todo"); ap.add_argument("--trace"); a = ap.parse_args()
    over = {k: v for k, v in (("plan_prompt", a.plan), ("draft_prompt", a.draft)) if v}; over.update(derived_numbers=True) if a.plan == 'plan_v2' else None; pol = policy(a.policy, **over); llm = ReplayLLM(); kb = KB()
    res = run_file(a.file, pol, llm, kb, trace=a.trace); 
    for r in res: r["judge"] = judge(r["scenario"], r) if r["scenario"].get("expected_status") else None
    if a.out: json.dump(res, open(a.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=str)
    if a.todo: json.dump(llm.todo, open(a.todo, "w", encoding="utf-8"), ensure_ascii=False)
    print("pending prompts:", len(llm.todo), "| pending queries:", sum(r["pending"] for r in res), "| ok:", sum(bool(r["judge"] and r["judge"]["ok"]) for r in res), "/", len(res))
