"""Tests for agent-memory store."""
import tempfile
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from memory_store import MemoryStore


def test_remember_and_recall():
    with tempfile.TemporaryDirectory() as d:
        store = MemoryStore(Path(d) / "m.json")
        e = store.remember("use pnpm", project="demo", tags=["build"])
        assert e["text"] == "use pnpm"
        hits = store.recall("pnpm", project="demo")
        assert len(hits) == 1
    print("test_remember_and_recall: ok")


def test_tag_filter():
    with tempfile.TemporaryDirectory() as d:
        store = MemoryStore(Path(d) / "m.json")
        store.remember("a", tags=["x"])
        store.remember("b", tags=["y"])
        items = store.list_all(tag="x")
        assert len(items) == 1
        assert items[0]["text"] == "a"
    print("test_tag_filter: ok")


if __name__ == "__main__":
    test_remember_and_recall()
    test_tag_filter()
    print("agent-memory tests passed")
