"""Tests for MemoryStore.search (AND semantics, recency, project scoping)."""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from memory_store import MemoryStore


def _store():
    tmp = tempfile.TemporaryDirectory()
    s = MemoryStore(Path(tmp.name) / "mem.json")
    s.remember("cache invalidation strategy for the billing service",
               project="billing", tags=["cache"])
    s.remember("cache key uses model plus prompt hash", project="billing")
    s.remember("agent router picks the cheapest tier", project="router")
    s.remember("prompt compression reduces token usage", project="router")
    return s, tmp


def test_and_semantics():
    s, tmp = _store()
    # both words must hit: only the billing cache entries qualify
    res = s.search("cache billing", project="billing")
    assert len(res) >= 1
    assert all("cache" in m["text"] and "billing" in m["text"] for m in res)
    # OR semantics would have returned the router entry too
    router = s.search("cache router")
    assert all("router" not in m["text"] for m in router)
    tmp.cleanup()
    print("test_and_semantics: ok")


def test_fuzzy_subsequence():
    s, tmp = _store()
    # "cch" is a subsequence of "cache" -> fuzzy match
    res = s.search("cch", fuzzy=True)
    assert any("cache" in m["text"] for m in res)
    # without fuzzy, no match at all
    res2 = s.search("cch", fuzzy=False)
    assert res2 == []
    tmp.cleanup()
    print("test_fuzzy_subsequence: ok")


def test_project_scoping():
    s, tmp = _store()
    res = s.search("cache", project="router")
    assert res == []
    tmp.cleanup()
    print("test_project_scoping: ok")


def test_since_days_filter():
    s, tmp = _store()
    res = s.search("cache", since_days=3650)
    assert len(res) >= 1  # everything is recent in this store
    res2 = s.search("cache", since_days=0)
    assert res2 == []     # cutoff = now, nothing older than now matches
    tmp.cleanup()
    print("test_since_days_filter: ok")


def test_empty_query():
    s, tmp = _store()
    assert s.search("   ") == []
    tmp.cleanup()
    print("test_empty_query: ok")


if __name__ == "__main__":
    test_and_semantics()
    test_fuzzy_subsequence()
    test_project_scoping()
    test_since_days_filter()
    test_empty_query()
    print("agent-memory search tests passed")
