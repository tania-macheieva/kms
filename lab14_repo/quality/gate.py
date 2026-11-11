"""Quality gate. Runs the pytest suite on one store, classifies failures as blocking/warning (Q11 by `severity` in thresholds.json,
every other check is blocking), writes quality/gate_report_<label>.{json,md}, appends a line to quality/history.jsonl and exits 1 on blocking failures.
Usage: python quality/gate.py --store store_clean --label ci [--no-history]"""
import argparse, json, os, subprocess, sys, tempfile, datetime, pathlib, re
import xml.etree.ElementTree as ET
ROOT = pathlib.Path(__file__).resolve().parent.parent
def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--store", required=True); ap.add_argument("--label", required=True)
    ap.add_argument("--history", default=str(ROOT / "quality/history.jsonl")); ap.add_argument("--no-history", action="store_true"); a = ap.parse_args()
    T = json.load(open(ROOT / "quality/thresholds.json")); xml = tempfile.mktemp(suffix=".xml")
    subprocess.run([sys.executable, "-m", "pytest", str(ROOT / "quality/tests"), "-q", "-p", "no:cacheprovider", f"--junitxml={xml}"], cwd=ROOT, env=dict(os.environ, QUALITY_STORE=a.store), capture_output=True, text=True)
    res = []
    for tc in ET.parse(xml).getroot().iter("testcase"):
        name = tc.get("name"); bad = tc.find("failure") if tc.find("failure") is not None else tc.find("error"); skipped = tc.find("skipped") is not None
        sev = "blocking"; m = re.search(r"\[(M\d+_[^\]]+)\]", name)
        if m: sev = T[m.group(1)].get("severity", "blocking")
        res.append(dict(check=name, status="skip" if skipped else ("fail" if bad is not None else "pass"), severity=sev, message=((bad.get("message") or "")[:220].replace("\n", " ") if bad is not None else "")))
    bf = [r for r in res if r["status"] == "fail" and r["severity"] == "blocking"]; wf = [r for r in res if r["status"] == "fail" and r["severity"] == "warning"]
    rep = dict(label=a.label, store=str(a.store), ts=datetime.datetime.now().isoformat(timespec="seconds"), total=len(res), passed=sum(r["status"] == "pass" for r in res), blocking_failed=len(bf), warnings=len(wf), gate="FAIL" if bf else "PASS", results=res)
    out = ROOT / f"quality/gate_report_{a.label}"; json.dump(rep, open(f"{out}.json", "w"), indent=1, ensure_ascii=False)
    md = [f"# Gate report: {a.label} (`{a.store}`) — **{rep['gate']}**", "", f"{rep['passed']}/{rep['total']} passed; blocking failures {len(bf)}, warnings {len(wf)}", "", "| check | status | severity | message |", "|---|---|---|---|"]
    md += [f"| {r['check']} | {r['status']} | {r['severity']} | {r['message'].replace('|', '/')} |" for r in res]; open(f"{out}.md", "w").write("\n".join(md) + "\n")
    if not a.no_history:
        with open(a.history, "a") as h: h.write(json.dumps({k: rep[k] for k in ("label", "store", "ts", "total", "passed", "blocking_failed", "warnings", "gate")}) + "\n")
    print(f"[gate] {a.label}: {rep['gate']}  passed {rep['passed']}/{rep['total']}  blocking {len(bf)}  warnings {len(wf)}")
    for r in bf: print("  BLOCK", r["check"])
    for r in wf: print("  warn ", r["check"])
    sys.exit(1 if bf else 0)
main()
