#!/usr/bin/env python3
"""alert-dedupe.py -- Lightweight cross-platform dedupe for send-ai-alert.

Prevents sending (and sounding) the exact same alert twice in quick
succession, e.g. when a long-running autonomous task's turn ends more than
once with no new progress (same session, same event type, same last
message) before the caller's cooldown window has elapsed.

Usage:
    python alert-dedupe.py <key> <ttl_seconds>

Prints "send" if this key hasn't been seen within the TTL window (and
records it), or "skip" if it has. Always prints "send" and exits 0 on any
failure (missing args, unwritable state file, corrupt state, etc.) so a
dedupe glitch never silently swallows a real alert.
"""
import hashlib
import json
import os
import sys
import time


def state_path():
    if os.name == "nt":
        base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
        return os.path.join(base, "devin-cli-hooks", "alert-dedupe.json")
    base = os.environ.get("XDG_CACHE_HOME") or os.path.expanduser("~/.cache")
    return os.path.join(base, "devin-cli-hooks", "alert-dedupe.json")


def main():
    try:
        if len(sys.argv) < 3:
            print("send")
            return
        raw_key = sys.argv[1]
        ttl = float(sys.argv[2])
        key = hashlib.sha256(raw_key.encode("utf-8", "ignore")).hexdigest()
        path = state_path()
        now = time.time()

        data = {}
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = {}

        # Prune expired entries so the file doesn't grow unbounded.
        data = {k: v for k, v in data.items() if now - v < ttl}

        if key in data:
            print("skip")
            return

        data[key] = now
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f)
        except Exception:
            pass

        print("send")
    except Exception:
        print("send")


if __name__ == "__main__":
    main()
