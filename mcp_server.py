#!/usr/bin/env python3
"""MCP server exposing agent-memory as tools for any MCP-compatible agent.

Tools:
  remember  - store a fact (text, project, tags)
  recall    - search memories by query
  list      - list recent memories for the current project
  forget    - delete a memory by id

Run with:  python mcp_server.py
Requires:  pip install mcp
"""
import json
import sys

from memory_store import MemoryStore, default_path

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:  # pragma: no cover
    print("The 'mcp' package is required: pip install mcp", file=sys.stderr)
    sys.exit(1)

mcp = FastMCP("agent-memory")
store = MemoryStore()


@mcp.tool()
def remember(text: str, project: str = "default", tags: list[str] | None = None) -> str:
    """Save a fact the agent should remember across sessions.

    Good facts: project decisions, conventions, build commands, gotchas,
    account choices. Bad facts: things available in the code itself.
    """
    e = store.remember(text, project=project, tags=tags or [])
    return json.dumps({"saved": True, "id": e["id"]})


@mcp.tool()
def recall(query: str, project: str = "default", limit: int = 5) -> str:
    """Search past memories before answering project-specific questions."""
    hits = store.recall(query, project=project, limit=limit)
    return json.dumps(hits, ensure_ascii=False)


@mcp.tool()
def list_memories(project: str = "default") -> str:
    """List all stored memories for this project, newest first."""
    return json.dumps(store.list_all(project=project), ensure_ascii=False)


@mcp.tool()
def forget(memory_id: int) -> str:
    """Delete a memory by its id."""
    return json.dumps({"deleted": store.forget(memory_id)})


if __name__ == "__main__":
    mcp.run()
