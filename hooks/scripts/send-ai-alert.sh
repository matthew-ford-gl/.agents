#!/usr/bin/env bash
# send-ai-alert.sh — Fire-and-forget POST to the AI alert API.
# Called by Devin CLI hooks on Stop, Notification, and SessionEnd events.
# Always exits 0 so it never blocks the agent.
#
# This script now uses session-info.py to look up the Devin sessions.db and
# determine whether the current session is a subagent. Subagent completions
# are skipped so only the parent session triggers an Echo alert.

# ── Version ──────────────────────────────────────────────────────────────────
# Bump this whenever the script's alerting behavior changes, so alerts in
# flight can be traced back to the version that emitted them.
SCRIPT_VERSION="1.6.0"

# ── Configuration ────────────────────────────────────────────────────────────
API_BASE="${ECHO_ALERT_API_BASE:-https://echo.uk.hos.accessacloud.com}"
API_KEY="${ECHO_ALERT_API_KEY:-}"

if [ -z "$API_KEY" ]; then
    exit 0
fi

ENDPOINT="${API_BASE}/api/alerts/aialert?apikey=${API_KEY}&type=standard"

# Prefer `python`, but fall back to `python3` (e.g. in WSL/Git Bash).
PYTHON_BIN=""
if command -v python &>/dev/null; then
    PYTHON_BIN="python"
elif command -v python3 &>/dev/null; then
    PYTHON_BIN="python3"
fi

if [ -z "$PYTHON_BIN" ]; then
    echo "send-ai-alert.sh: Python is required but was not found (tried 'python' and 'python3'). Skipping alert." >&2
    exit 0
fi

# ── Read stdin (hook event JSON) ─────────────────────────────────────────────
INPUT=$(cat 2>/dev/null || echo '{}')

# Helper: extract a JSON string value by key (lightweight, no jq needed)
json_val() {
    echo "$INPUT" | $PYTHON_BIN -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(data.get('$1', '$2'))
except:
    print('$2')
" 2>/dev/null || echo "$2"
}

EVENT_NAME=$(json_val "hook_event_name" "unknown")
SESSION_ID=$(json_val "session_id" "")

# ── Look up the session's real title and last agent message from the local
#    Devin CLI sessions.db (SQLite), so alerts show useful context instead of
#    a generic placeholder. Best-effort: any failure here is silently ignored.
SESSION_TITLE=""
LAST_MESSAGE=""
IS_SUBAGENT="false"
HAS_PENDING_SUBAGENTS="false"
if [ -n "$SESSION_ID" ] && [ -n "$PYTHON_BIN" ]; then
    HELPER_SCRIPT="$(dirname "$0")/session-info.py"
    if [ -f "$HELPER_SCRIPT" ]; then
        INFO_JSON=$($PYTHON_BIN "$HELPER_SCRIPT" "$SESSION_ID" 2>/dev/null)
        if [ -n "$INFO_JSON" ]; then
            IS_SUBAGENT=$(echo "$INFO_JSON" | $PYTHON_BIN -c "import sys,json; print(str(json.load(sys.stdin).get('is_subagent', False)).lower())" 2>/dev/null || echo "false")
            HAS_PENDING_SUBAGENTS=$(echo "$INFO_JSON" | $PYTHON_BIN -c "import sys,json; print(str(json.load(sys.stdin).get('has_pending_subagents', False)).lower())" 2>/dev/null || echo "false")
            SESSION_TITLE=$(echo "$INFO_JSON" | $PYTHON_BIN -c "import sys,json; print(json.load(sys.stdin).get('title') or '')" 2>/dev/null)
            LAST_MESSAGE=$(echo "$INFO_JSON" | $PYTHON_BIN -c "import sys,json; print(json.load(sys.stdin).get('last_message') or '')" 2>/dev/null)
        fi
    fi
fi

# Skip alerts for subagent sessions — only the parent session should notify.
if [ "$IS_SUBAGENT" = "true" ]; then
    exit 0
fi

# Skip Stop alerts while subagents (background or foreground) are still
# running — the orchestrator will auto-resume on its own, so this isn't
# really "waiting for user input". SessionEnd/Notification events still
# alert regardless.
if [ "$EVENT_NAME" = "Stop" ] && [ "$HAS_PENDING_SUBAGENTS" = "true" ]; then
    exit 0
fi

# ── Dedupe identical back-to-back alerts ─────────────────────────────────────
# Long-running autonomous tasks (e.g. the ship/quality-audit skills) can end
# their turn more than once with no real progress — same session, same
# event, same last message — before anything has actually changed (e.g.
# waiting out a backend retry/rate-limit). Skip an exact repeat of the same
# alert within a short cooldown window. Best-effort: any failure here should
# not block a genuinely new alert, so it defaults to "send".
DEDUPE_SCRIPT="$(dirname "$0")/alert-dedupe.py"
if [ -f "$DEDUPE_SCRIPT" ] && [ -n "$PYTHON_BIN" ]; then
    LAST_MESSAGE_FOR_KEY=$(echo "$LAST_MESSAGE" | cut -c1-300)
    DEDUPE_KEY="${SESSION_ID}|${EVENT_NAME}|${LAST_MESSAGE_FOR_KEY}"
    DEDUPE_RESULT=$($PYTHON_BIN "$DEDUPE_SCRIPT" "$DEDUPE_KEY" 300 2>/dev/null)
    if [ "$DEDUPE_RESULT" = "skip" ]; then
        exit 0
    fi
fi

# ── Derive repo (org/repo) from git remote ──────────────────────────────────
REPO=""
PROJECT_DIR="${DEVIN_PROJECT_DIR:-$(pwd)}"

if command -v git &>/dev/null && git -C "$PROJECT_DIR" rev-parse --is-inside-work-tree &>/dev/null; then
    REMOTE_URL=$(git -C "$PROJECT_DIR" remote get-url origin 2>/dev/null || echo "")
    if [ -n "$REMOTE_URL" ]; then
        # Azure DevOps: dev.azure.com/org/project/_git/repo -> org/project/repo
        if echo "$REMOTE_URL" | grep -q 'dev\.azure\.com'; then
            REPO=$(echo "$REMOTE_URL" | sed -E 's|.*dev\.azure\.com/([^/]+)/([^/]+)/_git/(.+)$|\1/\2/\3|' | sed 's/%20/ /g')
        # GitHub/GitLab SSH or HTTPS: extract org/repo
        else
            REPO=$(echo "$REMOTE_URL" | sed -E 's/\.git$//' | sed -E 's|.*[:/]([^/]+/[^/]+)$|\1|')
        fi
    fi
fi

# Fallback: use the directory name
if [ -z "$REPO" ]; then
    REPO=$(basename "$PROJECT_DIR")
fi

# ── Derive taskDescription from git branch or directory ──────────────────────
TASK_DESC=""
if command -v git &>/dev/null && git -C "$PROJECT_DIR" rev-parse --is-inside-work-tree &>/dev/null; then
    BRANCH=$(git -C "$PROJECT_DIR" symbolic-ref --short HEAD 2>/dev/null || echo "")
    if [ -n "$BRANCH" ] && [ "$BRANCH" != "main" ] && [ "$BRANCH" != "master" ]; then
        TASK_DESC="Working on branch: ${BRANCH}"
    fi
fi

if [ -z "$TASK_DESC" ]; then
    TASK_DESC="AI session in ${REPO}"
fi

# Prefer the session's actual title (from sessions.db) over the derived guess.
if [ -n "$SESSION_TITLE" ]; then
    TASK_DESC="$SESSION_TITLE"
fi

# ── Build reason from event type ─────────────────────────────────────────────
case "$EVENT_NAME" in
    Stop)
        STOP_ACTIVE=$(json_val "stop_hook_active" "false")
        REASON="Agent stopped — waiting for user input (stop_hook_active: ${STOP_ACTIVE})"
        ;;
    Notification)
        NOTIF_TYPE=$(json_val "tool_name" "general")
        REASON="Notification: ${NOTIF_TYPE}"
        ;;
    SessionEnd)
        END_REASON=$(json_val "reason" "session closed")
        REASON="Session ended — ${END_REASON}"
        ;;
    *)
        REASON="Hook event: ${EVENT_NAME}"
        ;;
esac

# Append the agent's last message to the user, when available, so the alert
# shows what actually happened rather than just the generic event reason.
# Truncated to keep the alert payload/notification reasonably sized.
if [ -n "$LAST_MESSAGE" ]; then
    TRUNCATED=$(echo "$LAST_MESSAGE" | cut -c1-500)
    REASON="${REASON}

Last message: ${TRUNCATED}"
fi

# Tag the reason with the emitting script's version, so alerts can be traced
# back to the script version that sent them.
# Include the emitting session's own ID (there's no separate "parent session
# id" recorded in sessions.db for subagents to link back to -- isolation is
# done purely via the is_subagent/has_pending_subagents content heuristics
# above) so a misfire can be traced straight back to the exact session via
# `python session-info.py <SESSION_ID>` without needing to guess.
SESSION_ID_SUFFIX=""
if [ -n "$SESSION_ID" ]; then
    SESSION_ID_SUFFIX=" | Session: ${SESSION_ID}"
fi
REASON="[send-ai-alert.sh v${SCRIPT_VERSION}] ${REASON}${SESSION_ID_SUFFIX}"

# ── Timestamp ────────────────────────────────────────────────────────────────
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || echo "")

# ── Session URL (no web UI session for local CLI runs) ───────────────────────
SESSION_URL="${DEVIN_SESSION_URL:-}"

# ── Build JSON payload (using python for safe escaping) ──────────────────────
PAYLOAD=$($PYTHON_BIN -c "
import json, sys
print(json.dumps({
    'taskDescription': sys.argv[1],
    'repo': sys.argv[2],
    'reason': sys.argv[3],
    'sessionUrl': sys.argv[4] or None,
    'timestamp': sys.argv[5]
}))
" "$TASK_DESC" "$REPO" "$REASON" "$SESSION_URL" "$TIMESTAMP" 2>/dev/null)

if [ -z "$PAYLOAD" ]; then
    exit 0
fi

# ── POST (fire-and-forget, backgrounded) ─────────────────────────────────────
curl -s -X POST "$ENDPOINT" \
    -H "Content-Type: application/json" \
    -d "$PAYLOAD" \
    --connect-timeout 5 \
    --max-time 10 \
    >/dev/null 2>&1 &

exit 0
