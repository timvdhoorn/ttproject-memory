#!/usr/bin/env python3
"""Project-memory turn-end check (Claude Code `Stop` hook). Self-contained; settings below.

Sends the turn back once when it used a live-system tool and no page under KB_DIR changed content
(log.md does not count; touching a file without changing it does not count). A page counts when its
content differs from HEAD and it was modified during the turn, or a commit made during the turn touched it.
`stop_hook_active` prevents a second block. Any error exits silently.

Wire in .claude/settings.json:
  {"hooks": {"Stop": [{"hooks": [{"type": "command", "timeout": 15,
    "command": "python3 \"$CLAUDE_PROJECT_DIR/.claude/hooks/project-memory.py\""}]}]}}
"""
import json
import os
import re
import subprocess
import sys
from datetime import datetime

KB_DIR = "wiki"                                  # knowledge folder, relative to the repo root
TRIGGER_TOOLS = r"^mcp__(ssh|remote)__"          # tool names that touch the live system
TRIGGER_BASH = r"\b(ssh|psql|kubectl)\b"         # Bash commands that touch the live system ("" = none)
MESSAGE = ("This turn touched the live system, but no page under %s/ changed. Record what you verified "
           "or changed on its owning page (plus one log line), or say in one sentence why there was nothing to record.")


def tool_uses(entries):
    for entry in entries:
        content = (entry.get("message") or {}).get("content") if entry.get("type") == "assistant" else None
        if isinstance(content, list):
            for part in content:
                if isinstance(part, dict) and part.get("type") == "tool_use":
                    yield part.get("name", ""), part.get("input") or {}


def is_user_prompt(entry):
    if entry.get("type") != "user" or entry.get("isMeta"):
        return False
    content = (entry.get("message") or {}).get("content")
    if isinstance(content, str):
        return True
    types = {p.get("type") for p in content or [] if isinstance(p, dict)}
    return "text" in types and "tool_result" not in types


def git(root, *args):
    res = subprocess.run(["git", "-C", root] + list(args), capture_output=True, text=True, timeout=5)
    return res.stdout if res.returncode == 0 else ""


def page_changed(root, since):
    log = KB_DIR + "/log.md"
    for line in git(root, "status", "--porcelain", "--untracked-files=all", "--", KB_DIR).splitlines():
        path = line[3:].split(" -> ")[-1].strip('"')
        full = os.path.join(root, path)
        if path.endswith(".md") and path != log and os.path.exists(full) and os.path.getmtime(full) >= since:
            return True
    committed = git(root, "log", "--since=@%d" % int(since), "--name-only", "--format=", "--", KB_DIR)
    return any(p.endswith(".md") and p != log for p in committed.split())


def decide(data, root):
    if data.get("stop_hook_active"):
        return None
    with open(data["transcript_path"], encoding="utf-8") as fh:
        entries = [json.loads(l) for l in fh if l.strip()]
    start = max((i for i, e in enumerate(entries) if is_user_prompt(e)), default=None)
    if start is None:
        return None
    live = any(
        re.search(TRIGGER_TOOLS, name)
        or (TRIGGER_BASH and name == "Bash" and re.search(TRIGGER_BASH, str(inp.get("command", ""))))
        for name, inp in tool_uses(entries[start:])
    )
    if not live:
        return None
    since = datetime.fromisoformat(entries[start]["timestamp"].replace("Z", "+00:00")).timestamp()
    if page_changed(root, since):
        return None
    return {"decision": "block", "reason": MESSAGE % KB_DIR}


def main():
    try:
        data = json.load(sys.stdin)
        result = decide(data, os.environ.get("CLAUDE_PROJECT_DIR") or data.get("cwd") or os.getcwd())
    except Exception:
        return 0
    if result:
        print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
