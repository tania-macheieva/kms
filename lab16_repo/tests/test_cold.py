from reco.graphdb import ItemGraph
from reco.entities import extract
def test_add_item_creates_edges(world):
    G = ItemGraph(world.items[:100], world.ent_of[:100], world.idf, world.types)
    try:
        it = dict(world.items[200]); before = G.stats(); G.add_item(it, world.ent_of[200], world.idf, world.types); after = G.stats()
        assert after["chunks"] == before["chunks"] + 1 and after["mentions"] == before["mentions"] + len(world.ent_of[200])
    finally: G.close()
