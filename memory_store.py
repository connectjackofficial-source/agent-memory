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


def _subsequence_score(text: str, query: str) -> int:
    """Return a small score when *query* appears as a character subsequence
    of *text* (useful for abbreviations and typos). 0 when it does not."""
    it = iter(text)
    matched = all(ch in it for ch in query)
    return 1 if matched else 0


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
               limit: int = 5, tag: Optional[str] = None,
               fuzzy: bool = False) -> list:
        q = query.lower()
        scored = []
        for m in self._data["memories"]:
            if project and m.get("project") != project:
                continue
            if tag and tag not in (m.get("tags") or []):
                continue
            text = m["text"].lower()
            score = sum(1 for w in q.split() if w in text)
            if q in text:
                score += 2
            if fuzzy:
                score += _subsequence_score(text, q)
            if score > 0:
                scored.append((score, m))
        scored.sort(key=lambda x: (-x[0], -x[1]["hits"]))
        results = [m for _, m in scored[:limit]]
        for m in results:
            m["hits"] += 1
        if results:
            self._save()
        return results

    def list_all(self, project: Optional[str] = None,
                 tag: Optional[str] = None) -> list:
        items = self._data["memories"]
        if project:
            items = [m for m in items if m.get("project") == project]
        if tag:
            items = [m for m in items if tag in (m.get("tags") or [])]
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

    def clear_all(self, project: Optional[str] = None):
        if project:
            self._data["memories"] = [
                m for m in self._data["memories"] if m.get("project") != project]
        else:
            self._data["memories"] = []
        self._save()

    def export_json(self) -> str:
        return json.dumps(self._data, indent=2, ensure_ascii=False)

    def import_json(self, payload: str):
        data = json.loads(payload)
        if "memories" not in data:
            raise ValueError("payload must contain 'memories'")
        self._data["memories"].extend(data["memories"])
        self._save()

    def stats(self) -> dict:
        items = self._data["memories"]
        by_project = {}
        total_hits = 0
        for m in items:
            proj = m.get("project", "default")
            by_project[proj] = by_project.get(proj, 0) + 1
            total_hits += m.get("hits", 0)
        return {
            "total": len(items),
            "by_project": by_project,
            "total_hits": total_hits,
        }
