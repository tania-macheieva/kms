import sys, pathlib, pytest
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
@pytest.fixture(scope="session")
def world():
    from reco.eval import World
    W = World(0); yield W; W.close()
@pytest.fixture(scope="session")
def hub():
    from app.core import Hub
    return Hub()
