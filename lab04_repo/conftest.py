import json
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parent
GOLD = json.loads((ROOT / "tests" / "gold_cases.json").read_text(encoding="utf-8"))["cases"]


def pytest_addoption(parser):
    parser.addoption("--rules", default=str(ROOT / "models" / "rules.json"), help="шлях до файлу правил")


@pytest.fixture(scope="session")
def rules_path(request):
    return request.config.getoption("--rules")


def pytest_generate_tests(metafunc):
    if "case" in metafunc.fixturenames:
        metafunc.parametrize("case", GOLD, ids=[c["id"] for c in GOLD])
