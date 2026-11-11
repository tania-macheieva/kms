"""Semantic layer: metric name -> SQL. `metric_sql('pass_rate', by=['year'], where={'cohort': ['HBOC']})` returns (sql, params)."""
import yaml, re
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
LAYER = yaml.safe_load((ROOT / "semantic/metrics.yml").read_text(encoding="utf-8"))
REQUIRED = ["label", "definition", "fact", "expression", "unit", "owner", "sources", "additivity", "limitations", "status", "reviewed"]

class SemanticError(ValueError): pass

def metric_sql(metric: str, by=(), where=None, order_by=None, limit=None, layer=LAYER):
    m = layer["metrics"].get(metric)
    if m is None: raise SemanticError(f"unknown metric '{metric}'; known: {sorted(layer['metrics'])}")
    fact = layer["facts"][m["fact"]]; dims = layer["dimensions"]; where = where or {}; by = list(by)
    for d in list(by) + list(where):
        if d not in dims: raise SemanticError(f"unknown dimension '{d}'")
        if m["fact"] not in dims[d]["facts"]: raise SemanticError(f"dimension '{d}' is not available for metric '{metric}' (fact {m['fact']})")
    joins = []                                           # one join per distinct join clause
    for d in by + list(where): j = dims[d]["join"]; joins += [j] if j not in joins else []
    if m.get("extra_join"): joins.append(m["extra_join"])
    sel = [f"{dims[d]['column']} AS {d}" for d in by] + [f"{m['expression']} AS {metric}"]
    sql = f"SELECT {', '.join(sel)}\nFROM {fact['table']} f" + "".join(f"\n{j}" for j in joins)
    params = []
    if where:
        conds = []
        for d, vals in where.items():
            vals = vals if isinstance(vals, (list, tuple)) else [vals]; conds.append(f"{dims[d]['column']} IN ({', '.join('?' * len(vals))})"); params += list(vals)
        sql += "\nWHERE " + " AND ".join(conds)
    if by: sql += "\nGROUP BY " + ", ".join(dims[d]["column"] for d in by)
    if by: sql += "\nORDER BY " + (order_by or ", ".join(dims[d]["column"] for d in by))
    if limit: sql += f"\nLIMIT {int(limit)}"
    return sql, params

def validate(layer=LAYER):
    """every metric has all required fields; dimension facts exist; used fact exists"""
    errs = []
    for k, m in layer["metrics"].items():
        errs += [f"{k}: missing {f}" for f in REQUIRED if not m.get(f)]
        if m.get("fact") not in layer["facts"]: errs.append(f"{k}: unknown fact")
    return errs

def run(con, metric, **kw):
    sql, params = metric_sql(metric, **kw); return con.execute(sql, params).df()

if __name__ == "__main__":
    import sys; print(metric_sql(sys.argv[1], by=sys.argv[2:])[0])
