#!/usr/bin/env python3
"""session-info.py -- Look up a Devin CLI session's title, last assistant
message, and whether it is a subagent session.

Usage:
    python session-info.py [db_path] <session_id>
    python session-info.py <session_id>

If db_path is omitted, the script tries (in order):
    1. The CHISEL_SESSION_DB environment variable (set by Devin CLI).
    2. %APPDATA%\\devin\\cli\\sessions.db (Windows).
    3. %LOCALAPPDATA%\\devin\\cli\\sessions.db (Windows fallback).
    4. %USERPROFILE%\\devin\\cli\\sessions.db (Windows fallback).
    5. ~/.config/devin/cli/sessions.db (Linux).
    6. ~/Library/Application Support/devin/cli/sessions.db (macOS).

Prints a single-line JSON object on stdout:
    {"title": "...", "last_message": "...", "is_subagent": true/false}
Missing/unavailable values are null. Always exits 0 -- callers should treat
any output parse failure as "no extra info available" and fall back gracefully.
"""
import json
import os
import re
import sqlite3
import sys


SUBAGENT_MARKERS = [
    "Conversation to summarize:",
    "Output a summary from the following messages:",
    "<project_context",
    "<session>",
    "$ARGUMENTS",
    "Task: $ARGUMENTS",
]


def maybe_wsl_path(path):
    """If running under WSL and given a Windows path, convert it to /mnt/X/..."""
    if not path or os.sep != "/":
        return path
    if path.startswith("/mnt/"):
        return path
    # Match Windows absolute paths like C:\... or C:/...
    m = re.match(r"^([A-Za-z]):[\\/](.*)$", path)
    if m:
        drive = m.group(1).lower()
        rest = m.group(2).replace("\\", "/")
        return f"/mnt/{drive}/{rest}"
    return path


def find_db_path(provided=None):
    """Return the first existing Devin sessions.db we can find."""
    candidates = []
    if provided:
        candidates.append(provided)
    chisel_db = os.environ.get("CHISEL_SESSION_DB")
    if chisel_db:
        candidates.append(chisel_db)
    # Windows (native, Git Bash, or WSL with inherited env)
    for env_var in ("APPDATA", "LOCALAPPDATA", "USERPROFILE"):
        base = os.environ.get(env_var)
        if base:
            candidates.append(os.path.join(base, "devin", "cli", "sessions.db"))
    # Linux
    candidates.append(os.path.expanduser("~/.config/devin/cli/sessions.db"))
    # macOS
    candidates.append(
        os.path.expanduser("~/Library/Application Support/devin/cli/sessions.db")
    )
    for p in candidates:
        if p:
            p = maybe_wsl_path(p)
            if os.path.isfile(p):
                return p
    return None


def is_injected_subagent_prompt(content):
    """Best-effort check that a first user message is an injected subagent prompt."""
    if not content:
        return False
    content = content.strip()
    # Explicit markers found in subagent/skill prompts.
    for marker in SUBAGENT_MARKERS:
        if marker in content:
            return True
    # Custom agent / skill prompts: "You are ..." plus structured task directives.
    if content.lower().startswith("you are") and (
        "$ARGUMENTS" in content or "Task:" in content or "##" in content
    ):
        return True
    return False


def is_subagent_session(conn, session_id):
    """Return True if this session was spawned by run_subagent, not by a user.

    Heuristic:
      * A real parent session has at least one entry in prompt_history (the user's
        typed prompt). Subagent sessions do not.
      * If prompt_history is unavailable/empty (older sessions), inspect the first
        user message in message_nodes. Injected subagent/skill prompts contain
        markers like "You are the ...", "$ARGUMENTS", "Conversation to summarize:".
        A single natural-language question is treated as a parent session.
      * Sessions with no user message at all are treated as subagent/failed sessions.
    """
    try:
        cur = conn.cursor()

        # Strong signal: the user typed something into this session.
        cur.execute("SELECT COUNT(*) FROM prompt_history WHERE session_id = ?", (session_id,))
        if cur.fetchone()[0] > 0:
            return False

        # No typed prompts. Look at the first user message to decide whether it was injected.
        cur.execute(
            "SELECT chat_message FROM message_nodes WHERE session_id = ? "
            "ORDER BY node_id ASC",
            (session_id,),
        )
        for (chat_message,) in cur.fetchall():
            try:
                msg = json.loads(chat_message)
            except Exception:
                continue
            if msg.get("role") == "user":
                return is_injected_subagent_prompt(msg.get("content", ""))

        # No user message found: assume an empty/subagent session and skip alerting.
        return True
    except Exception:
        return False


def main():
    result = {"title": None, "last_message": None, "is_subagent": False}
    try:
        if len(sys.argv) >= 3:
            db_path = find_db_path(sys.argv[1])
            session_id = sys.argv[2]
        elif len(sys.argv) == 2:
            db_path = find_db_path()
            session_id = sys.argv[1]
        else:
            print(json.dumps(result))
            return

        if not db_path:
            print(json.dumps(result))
            return

        conn = sqlite3.connect(f"file:{db_path}?mode=ro&immutable=1", uri=True, timeout=2)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        cur.execute("SELECT title FROM sessions WHERE id = ?", (session_id,))
        row = cur.fetchone()
        if row and row["title"]:
            result["title"] = row["title"]

        # Most recent node first; find the latest assistant message with
        # non-empty text content (skips tool-call-only / empty steps).
        cur.execute(
            "SELECT chat_message FROM message_nodes WHERE session_id = ? "
            "ORDER BY node_id DESC LIMIT 200",
            (session_id,),
        )
        for (chat_message,) in cur.fetchall():
            try:
                msg = json.loads(chat_message)
            except Exception:
                continue
            if msg.get("role") == "assistant" and msg.get("content"):
                result["last_message"] = msg["content"]
                break

        result["is_subagent"] = is_subagent_session(conn, session_id)
    except Exception:
        pass

    print(json.dumps(result))


if __name__ == "__main__":
    main()
