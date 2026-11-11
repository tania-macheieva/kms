import os, sys, json, pathlib, pytest
ROOT = pathlib.Path(__file__).resolve().parents[2]; sys.path.insert(0, str(ROOT))
from quality import profile as P
@pytest.fixture(scope="session")
def store():
    s = os.environ.get("QUALITY_STORE", "store_clean"); p = pathlib.Path(s); return p if p.is_absolute() else ROOT / p
@pytest.fixture(scope="session")
def chunks_(store):
    from quality.common import chunks; return chunks(store)
@pytest.fixture(scope="session")
def profile(store):
    raw = ROOT / "llm_log/raw"; files = [raw / "accuracy_expert.json"]
    if store.name != "store":   # the re-review applies to the repaired snapshot only
        files += [raw / "accuracy_expert_after.json", raw / "accuracy_expert_after_absorbed.json"]
    M, info = P.metrics(store, files); return P.verdicts(M)
@pytest.fixture(scope="session")
def rdf(store):
    from quality.shacl_run import to_rdf; return to_rdf(store)
