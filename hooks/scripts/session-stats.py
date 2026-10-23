#!/usr/bin/env python3
"""session-stats.py -- Write a per-session tool-usage sidecar for the retro skill.

Called by the Devin CLI Stop hook. Reads the hook event JSON on stdin for
session_id, opens sessions.db read-only, and writes:

    ~/.agents/session-stats/<session_id>.json

containing tool-call counts and the most common shell-command prefixes —
the mechanical evidence the `retro` skill checks for repeated friction.

Design constraints (hook context):
  * Must be fast: read-only DB access with immutable=1, hard row limits.
  * Must never block or alert: always exits 0, writes nothing to stdout.
  * Idempotent: overwrites the same sidecar on every Stop; harmless if the
    retro never reads it.
"""
import json
import os
import re
import sqlite3
import sys

MAX_TOOL_ROWS = 5000
MAX_PREFIXES = 15


def maybe_wsl_path(path):
    """If running under WSL and given a Windows path, convert it to /mnt/X/..."""
    if not path or os.sep != "/":
        return path
    if path.startswith("/mnt/"):
        return path
    m = re.match(r"^([A-Za-z]):[\\/](.*)$", path)
    if m:
        return f"/mnt/{m.group(1).lower()}/{m.group(2).replace(chr(92), '/')}"
    return path


def find_db_path():
    candidates = []
    chisel_db = os.environ.get("CHISEL_SESSION_DB")
    if chisel_db:
        candidates.append(chisel_db)
    for env_var in ("APPDATA", "LOCALAPPDATA", "USERPROFILE"):
        base = os.environ.get(env_var)
        if base:
            candidates.append(os.path.join(base, "devin", "cli", "sessions.db"))
    candidates.append(os.path.expanduser("~/.config/devin/cli/sessions.db"))
    candidates.append(
        os.path.expanduser("~/Library/Application Support/devin/cli/sessions.db")
    )
    for p in candidates:
        if p and os.path.isfile(maybe_wsl_path(p)):
            return maybe_wsl_path(p)
    return None


def shell_prefix(command):
    """Reduce a shell command to a coarse prefix for histogram purposes.

    'cd /x && dotnet test --filter Foo' -> 'cd && dotnet'
    'CHROME_PATH=/p npm test'           -> 'ENV= npm'
    """
    if not command:
        return ""
    cmd = command.strip()
    cmd = re.sub(r"^(\w+)=([^\s]+)\s+", r"\1= ", cmd)  # env var prefix
    if "&&" in cmd:
        parts = [p.strip().split()[0] if p.strip() else "" for p in cmd.split("&&")[:2]]
        return " && ".join(p for p in parts if p)
    return cmd.split()[0] if cmd.split() else ""


def collect(conn, session_id):
    stats = {"session_id": session_id, "tool_calls": {}, "shell_prefixes": {}}
    cur = conn.cursor()

    # tool_call_state holds every tool invocation when present.
    cur.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='tool_call_state'"
    )
    if cur.fetchone():
        cur.execute(
            "SELECT tool_call_json, tool_call_update_json FROM tool_call_state "
            "WHERE session_id = ? LIMIT ?",
            (session_id, MAX_TOOL_ROWS),
        )
        for tc_json, tcu_json in cur.fetchall():
            name = ""
            try:
                tcu = json.loads(tcu_json) if tcu_json else {}
                name = tcu.get("_meta", {}).get("cognition.ai/inferenceToolName", "")
            except Exception:
                pass
            if not name:
                try:
                    name = json.loads(tc_json).get("title", "") or "unknown"
                except Exception:
                    name = "unknown"
            stats["tool_calls"][name] = stats["tool_calls"].get(name, 0) + 1

            if name == "exec":
                try:
                    entry = json.loads(tc_json)["content"][0]
                    cmd = entry["content"]["resource"]["text"]
                except Exception:
                    cmd = ""
                prefix = shell_prefix(cmd)
                if prefix:
                    stats["shell_prefixes"][prefix] = (
                        stats["shell_prefixes"].get(prefix, 0) + 1
                    )

    # Trim to the most frequent prefixes.
    stats["shell_prefixes"] = dict(
        sorted(stats["shell_prefixes"].items(), key=lambda kv: -kv[1])[:MAX_PREFIXES]
    )
    return stats


def main():
    try:
        raw = sys.stdin.read() or "{}"
        session_id = json.loads(raw).get("session_id", "")
        if not session_id:
            return

        db_path = find_db_path()
        if not db_path:
            return

        conn = sqlite3.connect(
            f"file:{db_path}?mode=ro&immutable=1", uri=True, timeout=2
        )
        try:
            stats = collect(conn, session_id)
        finally:
            conn.close()

        out_dir = os.path.join(os.path.expanduser("~"), ".agents", "session-stats")
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, f"{session_id}.json")
        tmp_path = out_path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(stats, f, indent=1)
        os.replace(tmp_path, out_path)
    except Exception:
        pass
    sys.exit(0)


if __name__ == "__main__":
    main()
