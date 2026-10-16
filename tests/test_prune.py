"""Tests for MemoryStore.prune."""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from memory_store import MemoryStore


def _store():
    tmp = tempfile.TemporaryDirectory()
    return MemoryStore(Path(tmp.name) / "m.json"), tmp


def test_prune_keeps_newest():
    s, tmp = _store()
    for i in range(10):
        s.remember(f"memory number {i}", project="p1")
    removed = s.prune(max_entries=3)
    assert removed == 7
    items = s.list_all(project="p1")
    assert len(items) == 3
    # list_all returns newest first
    assert items[0]["text"] == "memory number 9"
    s.close() if hasattr(s, "close") else None
    tmp.cleanup()
    print("test_prune_keeps_newest: ok")


def test_prune_noop_when_under_limit():
    s, tmp = _store()
    s.remember("only one")
    assert s.prune(max_entries=10) == 0
    assert len(s.list_all()) == 1
    tmp.cleanup()
    print("test_prune_noop_when_under_limit: ok")


def test_prune_scoped_to_project():
    s, tmp = _store()
    for i in range(5):
        s.remember(f"a{i}", project="keep")
        s.remember(f"b{i}", project="drop")
    removed = s.prune(max_entries=2, project="drop")
    assert removed == 3
    assert len(s.list_all(project="keep")) == 5
    assert len(s.list_all(project="drop")) == 2
    tmp.cleanup()
    print("test_prune_scoped_to_project: ok")


if __name__ == "__main__":
    test_prune_keeps_newest()
    test_prune_noop_when_under_limit()
    test_prune_scoped_to_project()
    print("agent-memory prune tests passed")
