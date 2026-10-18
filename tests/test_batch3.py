"""Tests for agent-memory batch 3: rename_tag and related."""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from memory_store import MemoryStore


def _store():
    return MemoryStore(Path(tempfile.mkdtemp()) / "m.json")


def test_rename_tag_updates_all():
    st = _store()
    m1 = st.remember("billing endpoint moved", tags=["billing"])
    st.remember("billing retry logic", tags=["billing", "retry"])
    st.remember("unrelated note", tags=["notes"])
    n = st.rename_tag("billing", "usage")
    assert n == 2
    tags = {m["id"]: m["tags"] for m in st.list_all()}
    assert m1["id"] not in tags or "billing" not in tags[m1["id"]]
    assert all("billing" not in m.get("tags") for m in st.list_all())
    print("test_rename_tag_updates_all: ok")


def test_related_ranks_by_tags():
    st = _store()
    target = st.remember("auth token rotation for CI", tags=["auth", "ci"])
    st.remember("auth retry on 401", tags=["auth", "ci"])
    st.remember("cache eviction policy", tags=["cache"])
    st.remember("deploy to staging", tags=["deploy", "ci"])
    rel = st.related(target["id"], limit=3)
    assert len(rel) == 2, rel  # only two entries share tags
    assert "401" in rel[0]["text"] or rel[0]["tags"] == ["auth", "ci"]
    print("test_related_ranks_by_tags: ok")


if __name__ == "__main__":
    test_rename_tag_updates_all()
    test_related_ranks_by_tags()
    print("agent-memory batch3 tests passed")
