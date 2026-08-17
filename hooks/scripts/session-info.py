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
    {"title": "...", "last_message": "...", "is_subagent": true/false,
     "has_pending_subagents": true/false}
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
    # Custom agent / skill prompts: "You are ..." combined with a persona/task
    # reference or structured directives. A real user typing a question
    # essentially never opens a message with this phrasing. Note run_subagent
    # tasks (e.g. "You are the quality-auditor agent defined in ...AGENT.md.
    # Read that file and adopt its persona exactly.") don't always contain
    # "$ARGUMENTS"/"Task:"/"##", so also match on "agent"/"persona"/".md"
    # appearing alongside the "you are" opener.
    lower = content.lower()
    if lower.startswith("you are") and (
        "$ARGUMENTS" in content
        or "Task:" in content
        or "##" in content
        or "agent" in lower
        or "persona" in lower
        or ".md" in lower
    ):
        return True
    return False


def is_subagent_session(conn, session_id):
    """Return True if this session was spawned by run_subagent, not by a user.

    Heuristic:
      * Inspect the *content* of the first prompt_history entry, not just
        whether one exists. A real parent session's entry is what the human
        actually typed -- typically short, e.g. a question or a slash command
        like "/quality-audit" (even though that command may expand into a
        large templated first message in message_nodes). A background
        subagent's entry, on the other hand, is the entire long injected
        task text verbatim (e.g. "You are the quality-auditor agent defined
        in ...AGENT.md. Read that file and adopt its persona exactly...").
        So prompt_history existing is NOT enough on its own -- we still need
        to run the injected-prompt check against its actual content.
      * If there's no prompt_history entry at all (older sessions, or
        session not yet populated), fall back to the first user message in
        message_nodes.
      * Sessions with neither are treated as subagent/failed sessions.
    """
    try:
        cur = conn.cursor()

        cur.execute(
            "SELECT content FROM prompt_history WHERE session_id = ? ORDER BY id ASC LIMIT 1",
            (session_id,),
        )
        row = cur.fetchone()
        if row is not None:
            return is_injected_subagent_prompt(row[0])

        # No prompt_history entry -- fall back to the first user message.
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


# Markers written into the transcript when a background subagent is launched
# (role "tool", from run_subagent) and when it later completes (role "system",
# a <subagent_completion_notification>). Diffing launched vs. completed IDs
# tells us whether a Stop event is a genuine end (nothing left to wait on) or
# just the orchestrator's turn ending while other background subagents are
# still running -- in which case it will auto-resume on its own and a Stop
# alert would be noise.
SUBAGENT_LAUNCH_RE = re.compile(r"Background subagent started with agent_id=([0-9a-fA-F]+)")
SUBAGENT_COMPLETE_RE = re.compile(r"Background subagent with agent_id=([0-9a-fA-F]+) completed")


def has_pending_background_subagents(conn, session_id):
    """Return True if a background subagent was launched in this session but
    has no matching completion notification yet."""
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT chat_message FROM message_nodes WHERE session_id = ? ORDER BY node_id ASC",
            (session_id,),
        )
        launched = set()
        completed = set()
        for (chat_message,) in cur.fetchall():
            try:
                msg = json.loads(chat_message)
            except Exception:
                continue
            content = msg.get("content")
            if not isinstance(content, str):
                continue
            m = SUBAGENT_LAUNCH_RE.search(content)
            if m:
                launched.add(m.group(1))
                continue
            m = SUBAGENT_COMPLETE_RE.search(content)
            if m:
                completed.add(m.group(1))
        return bool(launched - completed)
    except Exception:
        return False


def has_pending_subagent_tool_calls(conn, session_id):
    """Return True if a run_subagent tool call exists for this session that
    has not yet completed.

    This catches *foreground* subagents that the transcript-based
    has_pending_background_subagents() misses.  Foreground subagents
    (is_background=false) block the parent agent while they run -- the Devin
    CLI fires a Stop hook when the parent's turn ends, but the parent will
    auto-resume once the foreground subagent finishes.  Without this check,
    that Stop event would generate a spurious alert.

    The tool_call_state table stores every tool invocation.  A run_subagent
    row whose tool_call_update_json status is not "completed" (or whose
    update row is NULL / missing) is still in-flight.
    """
    try:
        cur = conn.cursor()
        # Check whether the tool_call_state table exists (older CLI versions
        # may not have it).
        cur.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='tool_call_state'"
        )
        if not cur.fetchone():
            return False

        cur.execute(
            "SELECT tool_call_json, tool_call_update_json "
            "FROM tool_call_state WHERE session_id = ?",
            (session_id,),
        )
        for (tc_json, tcu_json) in cur.fetchall():
            # Identify run_subagent calls via the update metadata or the
            # title field in the original call JSON.
            tool_name = ""
            try:
                tcu = json.loads(tcu_json) if tcu_json else {}
                tool_name = tcu.get("_meta", {}).get(
                    "cognition.ai/inferenceToolName", ""
                )
            except Exception:
                tcu = {}

            if tool_name != "run_subagent":
                # Fallback: check the title in the original call JSON.
                try:
                    tc = json.loads(tc_json) if tc_json else {}
                except Exception:
                    continue
                title = tc.get("title", "")
                if "subagent" not in title.lower():
                    continue

            status = tcu.get("status", "")
            if status != "completed":
                return True
        return False
    except Exception:
        return False


def main():
    result = {
        "title": None,
        "last_message": None,
        "is_subagent": False,
        "has_pending_subagents": False,
    }
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
        result["has_pending_subagents"] = (
            has_pending_background_subagents(conn, session_id)
            or has_pending_subagent_tool_calls(conn, session_id)
        )
    except Exception:
        pass

    print(json.dumps(result))


if __name__ == "__main__":
    main()
