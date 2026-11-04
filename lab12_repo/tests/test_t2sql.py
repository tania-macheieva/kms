import sys, pytest, duckdb
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT))
from t2sql.pipeline import guard, GuardError, Pipeline, ReplayLLM

BAD = {  # sql -> expected guard code
 "DELETE FROM fact_variant_call": "not_select", "DROP TABLE dim_gene": "not_select", "UPDATE dim_sample SET qc_status='pass'": "not_select", "INSERT INTO dim_gene VALUES (99,'X','1')": "not_select",
 "CREATE TABLE t AS SELECT 1": "not_select", "ALTER TABLE dim_gene ADD COLUMN x INT": "not_select", "COPY dim_gene TO '/tmp/x.csv'": "not_select", "ATTACH '/tmp/x.db' AS x": "not_select",
 "PRAGMA database_list": "not_select", "SET enable_external_access=true": "not_select", "SELECT 1; DROP TABLE dim_gene": "multiple_statements",
 "SELECT * FROM read_csv('/etc/passwd')": "table_function", "SELECT * FROM read_parquet('data/parquet/dim_gene.parquet')": "table_function", "SELECT * FROM information_schema.tables": "schema_qualified_table",
 "SELECT * FROM main.dim_gene": "schema_qualified_table", "SELECT * FROM secret_table": "table_not_allowed", "SELECT read_text('/etc/passwd')": "function_not_allowed",
 "SELECT * FROM dim_gene WHERE gene_symbol = (SELECT * FROM read_json('x.json'))": "table_function", "SELEC broken": "not_select", "SELECT * FROM duckdb_tables()": "table_function"}

@pytest.mark.parametrize("sql,code", list(BAD.items()))
def test_guard_blocks(sql, code):
    with pytest.raises(GuardError) as e: guard(sql)
    assert e.value.code == code

def test_limit_enforced():
    assert guard("SELECT * FROM dim_taxon").upper().endswith("LIMIT 200") and guard("SELECT * FROM dim_taxon LIMIT 99999").upper().endswith("LIMIT 1000") and guard("SELECT * FROM dim_taxon LIMIT 5").upper().endswith("LIMIT 5")

@pytest.fixture(scope="module")
def pipe(): return Pipeline(ReplayLLM(), timeout=1.0)
def test_timeout(pipe):
    with pytest.raises(GuardError) as e: pipe.execute("SELECT count(*) FROM fact_variant_call a, fact_variant_call b, fact_variant_call c")
    assert e.value.code == "timeout"
def test_explain_catches_bad_column(pipe):
    with pytest.raises(GuardError) as e: pipe.execute("SELECT nope FROM dim_gene")
    assert e.value.code == "explain_failed"
def test_read_only_connection(pipe):
    with pytest.raises(duckdb.Error): pipe.con.execute("CREATE TABLE x (a INT)")                  # defence in depth: even if the AST check failed
def test_external_access_disabled(pipe):
    with pytest.raises(duckdb.Error): pipe.con.execute("SELECT * FROM read_csv('/etc/passwd')").fetchall()
def test_config_locked(pipe):
    with pytest.raises(duckdb.Error): pipe.con.execute("SET enable_external_access=true")
def test_cte_and_union_allowed(pipe):
    f, c, r = pipe.execute("WITH a AS (SELECT gene_key FROM dim_gene) SELECT count(*) FROM a UNION ALL SELECT count(*) FROM dim_sample"); assert len(r) == 2
def test_eval_file_has_10_plus_questions():
    import json; assert sum(1 for l in open(ROOT / "tests/t2sql.jsonl") if json.loads(l)["expected"] == "result") >= 10
