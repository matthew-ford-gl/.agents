#!/usr/bin/env python3
"""session-info.py -- Look up a Devin CLI session's title and last assistant
message from its local sessions.db (SQLite), given a session_id.

Usage: python session-info.py <db_path> <session_id>

Prints a single-line JSON object on stdout: {"title": ..., "last_message": ...}
Missing/unavailable values are null. Always exits 0 -- callers should treat
any output parse failure as "no extra info available" and fall back gracefully.
"""
import json
import sqlite3
import sys


def main():
    result = {"title": None, "last_message": None}
    try:
        db_path, session_id = sys.argv[1], sys.argv[2]
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True, timeout=2)
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
    except Exception:
        pass

    print(json.dumps(result))


if __name__ == "__main__":
    main()
