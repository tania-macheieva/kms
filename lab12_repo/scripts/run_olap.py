"""Run every sql/olap/*.sql on the warehouse; save results to eval/olap_results.json (rows + elapsed ms) and print them."""
import duckdb, json, time, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
con = duckdb.connect(str(ROOT / "data/warehouse.duckdb"), read_only=True); out = {}
for f in sorted((ROOT / "sql/olap").glob("*.sql")):
    sql = f.read_text(); t0 = time.perf_counter(); df = con.execute(sql).df(); ms = (time.perf_counter() - t0) * 1000
    out[f.stem] = dict(question=[l[12:].strip() for l in sql.splitlines() if l.startswith("-- question:")][0], operation=[l[13:].strip() for l in sql.splitlines() if l.startswith("-- operation:")][0], columns=list(df.columns), rows=json.loads(df.to_json(orient="values", date_format="iso")), ms=round(ms, 1))
    if "-v" in sys.argv: print("\n##", f.stem, f"({ms:.0f} ms, {len(df)} rows)\n", df.head(14).to_string(index=False))
json.dump(out, open(ROOT / "eval/olap_results.json", "w"), indent=1, ensure_ascii=False); print("queries:", len(out))
