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

The check-and-write is wrapped in a small lock file so concurrent hook
processes (e.g. the same event delivered to both send-ai-alert.sh and
send-ai-alert.ps1 in parallel) can't both read the state file before
either writes and both pass the check.
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

        # Best-effort inter-process lock via an exclusive-create lock file.
        # Spin briefly; give up after ~2s and fall back to unlocked (fail
        # open -- a stalled lock must not swallow alerts). Stale locks older
        # than 30s are broken to recover from a crashed holder.
        lock_path = path + ".lock"
        locked = False
        deadline = now + 2
        while time.time() < deadline:
            try:
                os.makedirs(os.path.dirname(lock_path), exist_ok=True)
                try:
                    if now - os.path.getmtime(lock_path) > 30:
                        os.remove(lock_path)
                except OSError:
                    pass
                fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                os.close(fd)
                locked = True
                break
            except OSError:
                time.sleep(0.05)

        data = {}
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = {}

        # Prune expired entries so the file doesn't grow unbounded.
        data = {k: v for k, v in data.items() if now - v < ttl}

        try:
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
        finally:
            if locked:
                try:
                    os.remove(lock_path)
                except OSError:
                    pass
    except Exception:
        print("send")


if __name__ == "__main__":
    main()
