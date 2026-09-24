"""Smoke tests for the memory store. Run: python test_store.py"""
import tempfile
import os
from pathlib import Path

from memory_store import MemoryStore


def main():
    with tempfile.TemporaryDirectory() as d:
        s = MemoryStore(Path(d) / "m.json")
        s.remember("use pnpm", project="demo")
        s.remember("tests next to source", project="demo")
        assert len(s.list_all()) == 2
        hits = s.recall("pnpm")
        assert hits and "pnpm" in hits[0]["text"], hits
        assert s.forget(hits[0]["id"]) is True
        assert len(s.list_all()) == 1
    print("all smoke tests passed")


if __name__ == "__main__":
    main()
