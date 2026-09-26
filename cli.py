#!/usr/bin/env python3
"""agent-memory CLI: remember, recall, list, forget facts across sessions.

Examples:
    python cli.py remember "use pnpm, not npm" --project myapp --tags build
    python cli.py recall "which package manager"
    python cli.py list --project myapp
    python cli.py forget 1727000000000
"""
import argparse
import json
import sys

from memory_store import MemoryStore


def project_from_git() -> str:
    import subprocess
    try:
        out = subprocess.run(["git", "rev-parse", "--show-toplevel"],
                             capture_output=True, text=True, timeout=5)
        if out.returncode == 0:
            return out.stdout.strip().replace("\\", "/").split("/")[-1]
    except Exception:
        pass
    return "default"


def main():
    ap = argparse.ArgumentParser(prog="agent-memory")
    sub = ap.add_subparsers(dest="cmd", required=True)

    r = sub.add_parser("remember", help="store a fact")
    r.add_argument("text")
    r.add_argument("--project", default=None)
    r.add_argument("--tags", nargs="*", default=[])

    rc = sub.add_parser("recall", help="search memories")
    rc.add_argument("query")
    rc.add_argument("--project", default=None)
    rc.add_argument("--limit", type=int, default=5)

    l = sub.add_parser("list", help="list memories")
    l.add_argument("--project", default=None)
    l.add_argument("--tag", default=None)

    f = sub.add_parser("forget", help="delete a memory by id")
    f.add_argument("id", type=int)

    args = ap.parse_args()
    store = MemoryStore()
    project = getattr(args, "project", None) or project_from_git()

    if args.cmd == "remember":
        e = store.remember(args.text, project=project, tags=args.tags)
        print(json.dumps({"saved": True, "id": e["id"], "project": project},
                         ensure_ascii=False))
    elif args.cmd == "recall":
        hits = store.recall(args.query, project=project, limit=args.limit)
        for h in hits:
            print(f"[{h['id']}] ({h['project']}) {h['text']}")
        if not hits:
            print("(no memories found)")
    elif args.cmd == "list":
        tag = getattr(args, "tag", None)
        items = store.list_all(project=project, tag=tag)
        for m in items:
            tags = (" [" + ",".join(m["tags"]) + "]") if m.get("tags") else ""
            print(f"[{m['id']}] ({m['project']}){tags} {m['text']}")
        if not items:
            print("(empty)")
    elif args.cmd == "forget":
        ok = store.forget(args.id)
        print("deleted" if ok else "not found")


if __name__ == "__main__":
    main()
