"""Tests for dedupe and tag stats."""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from memory_store import MemoryStore


def test_dedupe_removes_exact_duplicates():
    with tempfile.TemporaryDirectory() as d:
        store = MemoryStore(Path(d) / "m.json")
        store.remember("use pnpm", project="app")
        store.remember("use pnpm", project="app")      # duplicate
        store.remember("use pnpm", project="other")     # different project: kept
        store.remember("pin python 3.12", project="app")
        removed = store.dedupe()
        assert removed == 1
        assert store.stats()["total"] == 3
        # keeping the earliest entry: only one "use pnpm" survives, and it
        # is the first-inserted one (lower id than the removed duplicate's twin)
        app_items = store.list_all(project="app")
        texts = [m["text"] for m in app_items]
        assert sorted(texts) == ["pin python 3.12", "use pnpm"]
    print("test_dedupe_removes_exact_duplicates: ok")


def test_dedupe_project_scoped():
    with tempfile.TemporaryDirectory() as d:
        store = MemoryStore(Path(d) / "m.json")
        store.remember("same fact", project="a")
        store.remember("same fact", project="a")
        store.remember("same fact", project="b")
        removed = store.dedupe(project="a")
        assert removed == 1
        assert store.stats()["total"] == 2
    print("test_dedupe_project_scoped: ok")


def test_stats_by_tag():
    with tempfile.TemporaryDirectory() as d:
        store = MemoryStore(Path(d) / "m.json")
        store.remember("fact one", project="app", tags=["build", "ci"])
        store.remember("fact two", project="app", tags=["build"])
        s = store.stats()
        assert s["by_tag"]["build"] == 2
        assert s["by_tag"]["ci"] == 1
    print("test_stats_by_tag: ok")


if __name__ == "__main__":
    test_dedupe_removes_exact_duplicates()
    test_dedupe_project_scoped()
    test_stats_by_tag()
    print("agent-memory dedupe tests passed")
