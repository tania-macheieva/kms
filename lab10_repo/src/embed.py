"""Embedding models on ONNX Runtime (weights from data/models, see scripts/fetch_models.sh)."""
from __future__ import annotations
import hashlib, time
from pathlib import Path
import numpy as np, onnxruntime as ort
from tokenizers import Tokenizer

ROOT = Path(__file__).resolve().parents[1]
MODELS = {
    # name: (dir, query prefix, max_len, license, note)
    "minilm": ("data/models/minilm", "", 256, "Apache-2.0", "sentence-transformers/all-MiniLM-L6-v2, int8 (Xenova ONNX)"),
    "bge": ("data/models/bge", "Represent this sentence for searching relevant passages: ", 512, "MIT", "BAAI/bge-small-en-v1.5, fp32 (Xenova ONNX)"),
}
CACHE = ROOT / "data" / "cache"


class Embedder:
    def __init__(self, name: str):
        d, self.qprefix, self.max_len, _, _ = MODELS[name]
        self.name = name
        p = ROOT / d
        so = ort.SessionOptions(); so.intra_op_num_threads = 2
        self.sess = ort.InferenceSession(str(p / "model.onnx"), so, providers=["CPUExecutionProvider"])
        self.tok = Tokenizer.from_file(str(p / "tokenizer.json"))
        self.tok.enable_truncation(self.max_len); self.tok.enable_padding()
        self.names = {i.name for i in self.sess.get_inputs()}

    def _run(self, texts):
        enc = self.tok.encode_batch(texts)
        ids = np.array([e.ids for e in enc], dtype=np.int64); am = np.array([e.attention_mask for e in enc], dtype=np.int64)
        feed = {"input_ids": ids, "attention_mask": am}
        if "token_type_ids" in self.names: feed["token_type_ids"] = np.zeros_like(ids)
        return self.sess.run(None, feed)[0], am

    def encode(self, texts, query=False, bs=32):
        """L2-normalised sentence vectors: CLS pooling for bge, mean pooling for MiniLM."""
        if query and self.qprefix: texts = [self.qprefix + t for t in texts]
        out = []
        order = np.argsort([len(t) for t in texts])  # batch similar lengths -> less padding
        for i in range(0, len(texts), bs):
            idx = order[i:i + bs]; h, am = self._run([texts[j] for j in idx])
            v = h[:, 0] if self.name == "bge" else (h * am[..., None]).sum(1) / am.sum(1, keepdims=True)
            out.append((idx, v))
        res = np.zeros((len(texts), out[0][1].shape[1]), dtype=np.float32)
        for idx, v in out: res[idx] = v
        return res / np.linalg.norm(res, axis=1, keepdims=True)

    def tokens(self, text, query=False):
        """Token-level normalised vectors (for the late-interaction reranker)."""
        h, am = self._run([(self.qprefix if query else "") + text])
        v = h[0][am[0] == 1][1:-1]  # drop [CLS]/[SEP]
        return v / np.maximum(np.linalg.norm(v, axis=1, keepdims=True), 1e-9)


def cached_encode(emb: Embedder, texts, tag: str, query=False):
    """Disk cache keyed by model+texts hash; keeps repeated runs fast and deterministic."""
    CACHE.mkdir(parents=True, exist_ok=True)
    h = hashlib.sha1((emb.name + "|" + str(query) + "|" + "\x00".join(texts)).encode()).hexdigest()[:16]
    f = CACHE / f"{emb.name}_{tag}_{h}.npy"
    if f.exists(): return np.load(f)
    v = emb.encode(texts, query=query); np.save(f, v); return v
