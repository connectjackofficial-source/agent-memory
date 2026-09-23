"""Project-scoped, file-backed memory store for AI coding agents.

No external dependencies. Storage is a single JSON file so it is easy to
inspect, back up, and diff.
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Optional


def default_path() -> Path:
    root = os.environ.get("AGENT_MEMORY_DIR")
    if root:
        return Path(root) / "memory.json"
    return Path.home() / ".agent-memory" / "memory.json"


class MemoryStore:
    def __init__(self, path: Optional[Path] = None):
        self.path = Path(path) if path else default_path()
        self._data = {"memories": []}
        self._load()

    def _load(self):
        if self.path.exists():
            try:
                self._data = json.loads(self.path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                self._data = {"memories": []}
        self._data.setdefault("memories", [])

    def _save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(self._data, indent=2, ensure_ascii=False),
                       encoding="utf-8")
        tmp.replace(self.path)

    def remember(self, text: str, project: str = "default",
                 tags: Optional[list] = None) -> dict:
        entry = {
            "id": int(time.time() * 1000),
            "text": text.strip(),
            "project": project,
            "tags": tags or [],
            "created": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "hits": 0,
        }
        self._data["memories"].append(entry)
        self._save()
        return entry

    def recall(self, query: str, project: Optional[str] = None,
               limit: int = 5) -> list:
        q = query.lower()
        scored = []
        for m in self._data["memories"]:
            if project and m.get("project") != project:
                continue
            text = m["text"].lower()
            score = sum(1 for w in q.split() if w in text)
            if q in text:
                score += 2
            if score > 0:
                scored.append((score, m))
        scored.sort(key=lambda x: (-x[0], -x[1]["hits"]))
        results = [m for _, m in scored[:limit]]
        for m in results:
            m["hits"] += 1
        if results:
            self._save()
        return results

    def list_all(self, project: Optional[str] = None) -> list:
        items = self._data["memories"]
        if project:
            items = [m for m in items if m.get("project") == project]
        return list(reversed(items))

    def forget(self, memory_id: int) -> bool:
        before = len(self._data["memories"])
        self._data["memories"] = [
            m for m in self._data["memories"] if m["id"] != memory_id
        ]
        changed = len(self._data["memories"]) != before
        if changed:
            self._save()
        return changed
