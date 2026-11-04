"""Judge protocol, step 1: write llm_log/in/judge_<set>.json (question, full context, answer) for the answers of results_<set>.json."""
import json, re, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]

def main(which, split=2):
    res = json.load(open(ROOT / f"eval/results_{which}.json", encoding="utf-8")); items = []
    for m in res:
        ctx = m["prompt_user"].split("<context>")[1].split("</context>")[0].strip()
        items.append(dict(id=f"{which}:{m['id']}", question=m["question"], context=ctx, answer=m["answer"] if m["status"] != "BLOCKED" else "STATUS: NO_ANSWER\n(withheld)"))
    n = len(items); step = -(-n // split)
    for p in range(split): json.dump(items[p * step:(p + 1) * step], open(ROOT / f"llm_log/in/judge_{which}_part{p + 1}.json", "w"), ensure_ascii=False)
    print(which, n, "items,", split, "parts")
if __name__ == "__main__": main(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 2)
