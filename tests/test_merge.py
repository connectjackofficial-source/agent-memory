"""Tests for agent-memory merge (substring dedup)."""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from memory_store import MemoryStore


def _store():
    tmp = tempfile.TemporaryDirectory()
    s = MemoryStore(Path(tmp.name) / "mem.json")
    return s, tmp


def test_substring_merged():
    s, tmp = _store()
    s.remember("deploy uses docker compose", project="ops", tags=["ci"])
    s.remember("docker compose", project="ops", tags=["infra"])
    report = s.merge(project="ops")
    assert report["merged"] == 1
    assert report["kept"] == 1
    left = s.list_all(project="ops")
    assert left[0]["text"] == "deploy uses docker compose"
    assert "infra" in left[0]["tags"]  # absorbed tags
    s.path.unlink(missing_ok=True)
    tmp.cleanup()
    print("test_substring_merged: ok")


def test_merge_keeps_hits():
    s, tmp = _store()
    s.remember("long statement about the build", project="p", tags=["a"])
    s.remember("the build", project="p", tags=["b"])
    s.recall("build", project="p")  # bump hits on both? no — recall OR-scores
    m = s.list_all(project="p")
    for entry in m:
        entry["hits"] += 1
    s._save()
    report = s.merge(project="p")
    assert report["merged"] == 1
    survivor = s.list_all(project="p")[0]
    assert survivor["hits"] >= 1
    s.path.unlink(missing_ok=True)
    tmp.cleanup()
    print("test_merge_keeps_hits: ok")


def test_project_scope():
    s, tmp = _store()
    s.remember("docker compose", project="ops")
    s.remember("docker compose", project="web")
    report = s.merge(project="ops")
    assert report["merged"] == 0  # other project untouched
    assert len(s.list_all(project="web")) == 1
    s.path.unlink(missing_ok=True)
    tmp.cleanup()
    print("test_project_scope: ok")


def test_no_substrings():
    s, tmp = _store()
    s.remember("alpha build", project="p")
    s.remember("beta deploy", project="p")
    report = s.merge(project="p")
    assert report["merged"] == 0 and report["kept"] == 2
    s.path.unlink(missing_ok=True)
    tmp.cleanup()
    print("test_no_substrings: ok")


if __name__ == "__main__":
    test_substring_merged()
    test_merge_keeps_hits()
    test_project_scope()
    test_no_substrings()
    print("agent-memory merge tests passed")
