# Changelog

All notable changes to this project are documented here.

## [1.3.0] - 2026-10-10

### Added
- `suggest_tags()` — auto-tag memories from distinctive words
- Tag-suggestion tests and corrected dedupe ordering assertion

## [1.2.0] - 2026-10-10

### Added
- `dedupe()` — remove exact-duplicate memories (same project + text)
- `dedupe` CLI command with `--project` filter
- `stats` now reports per-tag counts

## [1.1.0] - 2026-10-08

### Added
- Fuzzy subsequence search (`recall --fuzzy`) for abbreviations and typos
- `stats` command: total, per-project counts, total hits
- JSON export / import commands

## [1.0.0] - 2026-09-23

### Added
- `memory_store.py` — file-backed, project-scoped fact store
- `mcp_server.py` — MCP tools: remember / recall / list / forget
- `cli.py` — command line with auto project detection from git root
