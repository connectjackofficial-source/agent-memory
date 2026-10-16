"""Project-scoped, file-backed memory store for AI coding agents.

No external dependencies. Storage is a single JSON file so it is easy to
inspect, back up, and diff.
"""
from __future__ import annotations

import json
import os
import re
import time
from collections import Counter
from pathlib import Path
from typing import Optional


def default_path() -> Path:
    root = os.environ.get("AGENT_MEMORY_DIR")
    if root:
        return Path(root) / "memory.json"
    return Path.home() / ".agent-memory" / "memory.json"


# Words that carry no tagging signal.
_STOPWORDS = {
    "the", "a", "an", "and", "or", "of", "to", "in", "for", "on", "with",
    "is", "are", "be", "it", "this", "that", "these", "those", "you", "your",
    "our", "we", "i", "as", "at", "by", "from", "about", "if", "not", "can",
    "will", "should", "would", "could", "do", "does", "did", "how", "what",
    "when", "where", "why", "use", "using", "used", "remember", "please",
    "make", "sure", "need", "needs", "want", "like", "just", "also", "have",
    "has", "had", "been", "was", "were", "than", "then", "there", "their",
    "they", "them", "him", "her", "his", "its", "me", "my", "so", "very",
}


def suggest_tags(text: str, top_n: int = 3) -> list:
    """Suggest memory tags from the most distinctive words in *text*."""
    words = re.findall(r"[a-z0-9]+", text.lower())
    counts = Counter(w for w in words if w not in _STOPWORDS and len(w) > 2)
    return [w for w, _ in counts.most_common(top_n)]


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

    def search(self, query: str, project: Optional[str] = None,
               limit: int = 5, since_days: Optional[int] = None,
               fuzzy: bool = True) -> list:
        """AND-search: *every* query word must match the memory text.

        Unlike :meth:`recall` (any-word OR scoring), search is precise —
        every word must appear as a substring, or as a character
        subsequence when *fuzzy* is enabled. Optionally restrict to
        memories created within the last *since_days* days.
        """
        words = [w for w in query.lower().split() if w]
        if not words:
            return []
        cutoff = None
        if since_days is not None:
            cutoff = time.time() - since_days * 86400
        scored = []
        for m in self._data["memories"]:
            if project and m.get("project") != project:
                continue
            if cutoff is not None:
                created = m.get("created", "")
                try:
                    ts = time.mktime(
                        time.strptime(created, "%Y-%m-%dT%H:%M:%S"))
                except ValueError:
                    ts = 0
                if ts < cutoff:
                    continue
            text = m["text"].lower()
            score = 0
            matched = True
            for w in words:
                if w in text:
                    score += 2
                elif fuzzy and _subsequence_score(text, w):
                    score += 1
                else:
                    matched = False
                    break
            if matched:
                scored.append((score, m))
        scored.sort(key=lambda x: (-x[0], -x[1]["hits"]))
        return [m for _, m in scored[:limit]]

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

    def dedupe(self, project: Optional[str] = None) -> int:
        """Remove exact-duplicate memories (same project + same text),
        keeping the earliest. Returns the number of entries removed."""
        seen = set()
        kept = []
        removed = 0
        for m in self._data["memories"]:
            if project and m.get("project") != project:
                kept.append(m)
                continue
            key = (m.get("project", "default"), m.get("text", "").strip())
            if key in seen:
                removed += 1
                continue
            seen.add(key)
            kept.append(m)
        self._data["memories"] = kept
        if removed:
            self._save()
        return removed

    def merge(self, project: Optional[str] = None) -> dict:
        """Merge substring-duplicate memories within a project.

        If memory A's text is a substring of memory B's text (same
        project), B absorbs A's tags and hit count and A is dropped —
        the long entry is the more complete statement. Returns
        {"merged": n, "kept": n}.
        """
        items = list(self._data["memories"])
        others = [m for m in items
                  if project and m.get("project") != project]
        pool = [m for m in items
                if not (project and m.get("project") != project)]
        merged = 0
        survivors = []
        while pool:
            base = pool.pop(0)
            base_text = base.get("text", "").strip().lower()
            absorbed, rest = [], []
            for m in pool:
                t = m.get("text", "").strip().lower()
                if (base_text and t and t in base_text
                        and t != base_text):
                    absorbed.append(m)
                else:
                    rest.append(m)
            if absorbed:
                tags = set(base.get("tags") or [])
                hits = base.get("hits", 0)
                for m in absorbed:
                    tags.update(m.get("tags") or [])
                    hits += m.get("hits", 0)
                    merged += 1
                base["tags"] = sorted(tags)
                base["hits"] = hits
            survivors.append(base)
            pool = rest
        self._data["memories"] = others + survivors
        if merged:
            self._save()
        return {"merged": merged, "kept": len(survivors)}

    def export_json(self) -> str:
        return json.dumps(self._data, indent=2, ensure_ascii=False)

    def import_json(self, payload: str):
        data = json.loads(payload)
        if "memories" not in data:
            raise ValueError("payload must contain 'memories'")
        self._data["memories"].extend(data["memories"])
        self._save()

    def prune(self, max_entries: int = 500,
              project: Optional[str] = None) -> int:
        """Keep only the newest *max_entries* memories, drop the oldest.

        Useful as a nightly janitor: memories accrete fast, and old
        low-value entries should age out before they bloat the store.
        Returns the number of entries removed.
        """
        pool = [m for m in self._data["memories"]
                if not (project and m.get("project") != project)]
        others = [m for m in self._data["memories"]
                  if project and m.get("project") != project]
        if len(pool) <= max_entries:
            return 0
        pool.sort(key=lambda m: (m.get("created", ""), m.get("id", 0)))
        keep = pool[-max_entries:]
        self._data["memories"] = others + keep
        self._save()
        return len(pool) - max_entries

    def stats(self) -> dict:
        items = self._data["memories"]
        by_project = {}
        by_tag = {}
        total_hits = 0
        for m in items:
            proj = m.get("project", "default")
            by_project[proj] = by_project.get(proj, 0) + 1
            total_hits += m.get("hits", 0)
            for t in m.get("tags") or []:
                by_tag[t] = by_tag.get(t, 0) + 1
        return {
            "total": len(items),
            "by_project": by_project,
            "by_tag": by_tag,
            "total_hits": total_hits,
        }
