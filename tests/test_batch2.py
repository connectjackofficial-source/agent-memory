"""Tests for MemoryStore.forget_before and move_memory."""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from memory_store import MemoryStore


def _make_store(entries):
    tmp = tempfile.mkdtemp()
    store = MemoryStore(Path(tmp) / "mem.json")
    for text, project in entries:
        store.remember(text, project=project)
    return store


def test_forget_before():
    store = _make_store([("old note", "default"), ("new note", "default")])
    # rewrite created times: first entry older than cutoff
    import json
    store._data["memories"][0]["created"] = "2026-01-01T00:00:00"
    store._data["memories"][1]["created"] = "2026-10-01T00:00:00"
    removed = store.forget_before("2026-06-01T00:00:00")
    assert removed == 1
    assert [m["text"] for m in store.list_all()] == ["new note"]
    print("test_forget_before: ok")


def test_forget_before_project_scope():
    store = _make_store([("old a", "alpha"), ("old b", "beta")])
    store._data["memories"][0]["created"] = "2026-01-01T00:00:00"
    store._data["memories"][1]["created"] = "2026-01-01T00:00:00"
    removed = store.forget_before("2026-06-01T00:00:00", project="alpha")
    assert removed == 1
    assert len(store.list_all()) == 1
    print("test_forget_before_project_scope: ok")


def test_forget_before_bad_cutoff():
    store = _make_store([("x", "default")])
    try:
        store.forget_before("not-a-date")
        raise AssertionError("expected ValueError")
    except ValueError:
        pass
    print("test_forget_before_bad_cutoff: ok")


def test_move_memory():
    store = _make_store([("note", "default")])
    mid = store.list_all()[0]["id"]
    assert store.move_memory(mid, "archive") is True
    assert store.list_all()[0]["project"] == "archive"
    assert store.move_memory(999999, "x") is False
    print("test_move_memory: ok")


if __name__ == "__main__":
    test_forget_before()
    test_forget_before_project_scope()
    test_forget_before_bad_cutoff()
    test_move_memory()
    print("agent-memory batch2 tests passed")
