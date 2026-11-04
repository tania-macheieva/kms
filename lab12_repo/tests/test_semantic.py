import sys, duckdb, pytest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT))
from semantic import sl

@pytest.fixture(scope="module")
def con(): return duckdb.connect(str(ROOT / "data/warehouse.duckdb"), read_only=True)

def test_all_metrics_have_required_fields(): assert sl.validate() == [] and len(sl.LAYER["metrics"]) >= 5
def test_every_metric_generates_and_runs(con):
    for m in sl.LAYER["metrics"]: assert len(sl.run(con, m)) == 1
def test_unknown_metric_and_dimension():
    with pytest.raises(sl.SemanticError): sl.metric_sql("nope")
    with pytest.raises(sl.SemanticError): sl.metric_sql("pass_rate", by=["nope"])
    with pytest.raises(sl.SemanticError): sl.metric_sql("cpu_hours", by=["gene"])        # dimension not available for the snapshot fact
def test_filters_are_parameterised():
    sql, params = sl.metric_sql("call_count", by=["gene"], where={"cohort": ["HBOC'; DROP TABLE x;--"]}); assert "DROP" not in sql and params == ["HBOC'; DROP TABLE x;--"]

def test_order_by_is_limited_to_selected_fields():
    sql, _ = sl.metric_sql("call_count", by=["gene"], order_by="call_count DESC")
    assert sql.endswith("ORDER BY call_count DESC")
    with pytest.raises(sl.SemanticError): sl.metric_sql("call_count", by=["gene"], order_by="gene; DROP TABLE dim_gene")
    with pytest.raises(sl.SemanticError): sl.metric_sql("call_count", by=["gene"], order_by="family")

def test_empty_filters_and_invalid_limits_are_rejected():
    with pytest.raises(sl.SemanticError): sl.metric_sql("call_count", where={"cohort": []})
    with pytest.raises(sl.SemanticError): sl.metric_sql("call_count", limit=0)

def test_pass_rate_is_ratio_of_sums(con):
    total = sl.run(con, "pass_rate").pass_rate.iloc[0]; direct = con.execute("SELECT round(100.0*sum(is_pass)/count(*),1) FROM fact_variant_call").fetchone()[0]; assert total == direct
def test_consistency_report():
    import json; r = json.load(open(ROOT / "eval/semantic_consistency.json")); assert len(r["checks"]) >= 2 and all(c["consistent"] for c in r["checks"])
