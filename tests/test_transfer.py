"""Test export/import."""
import tempfile
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from memory_store import MemoryStore


def test_export_import():
    with tempfile.TemporaryDirectory() as d:
        store = MemoryStore(Path(d) / "m.json")
        store.remember("fact one", tags=["a"])
        payload = store.export_json()
        store2 = MemoryStore(Path(d) / "m2.json")
        store2.import_json(payload)
        assert len(store2.list_all()) == 1
    print("test_export_import: ok")


if __name__ == "__main__":
    test_export_import()
    print("export/import test passed")
