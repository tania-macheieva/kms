"""One-off: bge-small embeddings of the 680 items (needs ../lab11_repo models). Result is shipped as hub/emb_bge.npy (680x384, L2-normalised) so that the demo needs no models."""
import sys, os, pathlib, numpy as np
ROOT = pathlib.Path(__file__).resolve().parent.parent; sys.path.insert(0, str(ROOT))
L11 = pathlib.Path(os.environ.get("LAB11_REPO", ROOT.parent / "lab11_repo")); sys.path.insert(0, str(L11)); os.chdir(L11)
from src.embed import Embedder; from reco.data import load_items
items = load_items(); E = Embedder("bge").encode([f"{it['title']} — {it['section']}\n{it['text']}"[:2000] for it in items]); np.save(ROOT / "hub/emb_bge.npy", E.astype(np.float32)); print(E.shape)
