"""Tests for fuzzy search and stats."""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from memory_store import MemoryStore, _subsequence_score


def test_subsequence_score():
    assert _subsequence_score("pipeline manager", "plmn") == 1
    assert _subsequence_score("deployment", "depl") == 1
    assert _subsequence_score("caching layer", "zzz") == 0
    print("test_subsequence_score: ok")


def test_fuzzy_recall():
    with tempfile.TemporaryDirectory() as d:
        store = MemoryStore(Path(d) / "m.json")
        store.remember("use pnpm for this project", project="app")
        hits = store.recall("pnpm", project="app", fuzzy=True)
        assert hits and "pnpm" in hits[0]["text"]
        # subsequence: "use pnpm" matched by "uspm"
        hits2 = store.recall("uspm", project="app", fuzzy=True)
        assert hits2
    print("test_fuzzy_recall: ok")


def test_stats():
    with tempfile.TemporaryDirectory() as d:
        store = MemoryStore(Path(d) / "m.json")
        store.remember("a", project="app")
        store.remember("b", project="app")
        store.remember("c", project="web")
        store.recall("a", project="app")
        stats = store.stats()
        assert stats["total"] == 3
        assert stats["by_project"] == {"app": 2, "web": 1}
        assert stats["total_hits"] == 1
    print("test_stats: ok")


if __name__ == "__main__":
    test_subsequence_score()
    test_fuzzy_recall()
    test_stats()
    print("fuzzy/stats tests passed")
