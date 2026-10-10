"""Tests for tag suggestion."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from memory_store import MemoryStore, suggest_tags


def test_suggest_tags_english():
    tags = suggest_tags(
        "remember to use redis for caching in the service layer")
    assert "redis" in tags
    assert "caching" in tags
    assert "service" in tags
    assert "the" not in tags  # stopwords excluded
    print("test_suggest_tags_english: ok")


def test_suggest_tags_short():
    tags = suggest_tags("hello world")
    assert tags == ["hello", "world"]
    print("test_suggest_tags_short: ok")


def test_suggest_tags_top_n():
    tags = suggest_tags("apple banana cherry apple banana", top_n=2)
    assert tags == ["apple", "banana"]
    print("test_suggest_tags_top_n: ok")


def test_remember_with_suggested_tags(tmp_path):
    store = MemoryStore(Path(tmp_path) / "m.json")
    text = "deploy uses docker compose with nginx"
    entry = store.remember(text, project="ops",
                           tags=suggest_tags(text))
    assert "docker" in entry["tags"]
    assert "deploy" in entry["tags"]
    print("test_remember_with_suggested_tags: ok")


if __name__ == "__main__":
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        test_remember_with_suggested_tags(d)
    test_suggest_tags_english()
    test_suggest_tags_short()
    test_suggest_tags_top_n()
    print("agent-memory tag tests passed")
