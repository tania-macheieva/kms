import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from agent import kb


def test_search_cache_reads_utf8(tmp_path, monkeypatch):
    cache_dir = tmp_path / "logs"
    cache_dir.mkdir()
    cache = {"query": [{"text": "український текст"}]}
    (cache_dir / "search_cache.json").write_text(
        json.dumps(cache, ensure_ascii=False), encoding="utf-8"
    )
    monkeypatch.setattr(kb, "ROOT", tmp_path)

    assert kb.KB()._scache == cache
