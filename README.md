# agent-memory

> Give your coding agent a brain that survives between sessions. A tiny,
> local-first MCP server that lets Claude Code / Cursor / Codex remember
> project decisions, conventions, and gotchas — across restarts.

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](#)
[![MCP](https://img.shields.io/badge/MCP-server-667ee8.svg)](https://modelcontextprotocol.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Coding agents are amnesiac. Every new conversation starts at zero — they
re-ask which package manager you use, rediscover why that directory is
gitignored, and relitigate the architecture decision you made three weeks ago.

**agent-memory** fixes that. It is a small MCP server that stores facts on
your machine and lets the agent recall them before answering project-specific
questions. One JSON file, zero services, zero telemetry.

## Install

```bash
pip install mcp
git clone https://github.com/connectjackofficial-source/agent-memory.git
```

Add to your MCP client config (Claude Code example):

```json
{
  "mcpServers": {
    "agent-memory": {
      "command": "python",
      "args": ["/absolute/path/to/agent-memory/mcp_server.py"]
    }
  }
}
```

## What it remembers

- **Decisions** — "we use pnpm, not npm, because of the monorepo lockfile"
- **Conventions** — "tests live next to the source file as `*.test.ts`"
- **Gotchas** — "the auth service needs `DATABASE_URL` even for unit tests"
- **Workflow** — "deploy via `make deploy-staging`, never push to main"

It does **not** store secrets.

## Usage (CLI)

```bash
python cli.py remember "use pnpm, not npm" --project myapp --tags build
python cli.py recall "which package manager"
python cli.py list --project myapp
python cli.py forget 1727000000000
```

## How the agent uses it

1. You say: *"by the way, we use pnpm"* — the agent calls `remember`.
2. Next session you ask: *"how do I install deps?"* — the agent calls
   `recall("package manager")` before answering.
3. Facts are scoped per project (auto-detected from the git repo root).

## Storage

Everything lives in one file:

```
~/.agent-memory/memory.json
```

Inspect it, back it up, or check it into a private dotfiles repo. No
database, no cloud.

## Layout

```
agent-memory/
├── memory_store.py   # file-backed key/fact store (no deps)
├── mcp_server.py    # MCP tool layer
├── cli.py           # command line
└── README.md
```

## License

[MIT](LICENSE)
