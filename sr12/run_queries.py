import argparse
from pathlib import Path

import duckdb


ROOT = Path(__file__).resolve().parent
parser = argparse.ArgumentParser()
parser.add_argument("--db", type=Path, default=ROOT / "out" / "sr12.duckdb")
args = parser.parse_args()

if not args.db.is_file():
    raise FileNotFoundError(f"DuckDB database not found: {args.db}")

sql_path = ROOT / "sql" / "queries.sql"
output_path = ROOT / "sql" / "queries_results.txt"
connection = duckdb.connect(str(args.db), read_only=True)
sections = []
for number, statement in enumerate(sql_path.read_text(encoding="utf-8").split(";"), 1):
    if not statement.strip():
        continue
    result = connection.execute(statement).fetchdf()
    sections.append(f"Query {number}\n{result.to_string(index=False)}")
connection.close()

output_path.write_text("\n\n".join(sections) + "\n", encoding="utf-8")
print(f"Wrote {len(sections)} query results to {output_path}")
