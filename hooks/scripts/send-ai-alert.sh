#!/usr/bin/env bash
# send-ai-alert.sh — Fire-and-forget POST to the AI alert API.
# Called by Devin CLI hooks on Stop, Notification, and SessionEnd events.
# Always exits 0 so it never blocks the agent.
#
# NOTE: This script previously tried to detect and skip subagent invocations by
# walking the parent process tree looking for a `devin acp` ancestor. That
# heuristic is no longer valid: in current Devin CLI builds, both the main
# session's own tool/hook execution AND background subagents run their shell
# commands as children of the same shared `devin acp` worker process, so the
# check always matched and the alert never fired. Devin CLI's Stop/SessionEnd
# hooks are also not documented as firing for subagents (no SubagentStop event
# or agent_id field), so no subagent filtering should be necessary here.

# ── Configuration ────────────────────────────────────────────────────────────
API_BASE="${ECHO_ALERT_API_BASE:-https://echo.uk.hos.accessacloud.com}"
API_KEY="${ECHO_ALERT_API_KEY:-}"

if [ -z "$API_KEY" ]; then
    exit 0
fi

ENDPOINT="${API_BASE}/api/alerts/aialert?apikey=${API_KEY}&type=standard"

# ── Read stdin (hook event JSON) ─────────────────────────────────────────────
INPUT=$(cat 2>/dev/null || echo '{}')

# Helper: extract a JSON string value by key (lightweight, no jq needed)
json_val() {
    echo "$INPUT" | python -c "
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
if [ -n "$SESSION_ID" ] && command -v python &>/dev/null; then
    HELPER_SCRIPT="$(dirname "$0")/session-info.py"
    for CANDIDATE_DB in "$HOME/.config/devin/cli/sessions.db" "$HOME/Library/Application Support/devin/cli/sessions.db"; do
        if [ -f "$CANDIDATE_DB" ] && [ -f "$HELPER_SCRIPT" ]; then
            INFO_JSON=$(python "$HELPER_SCRIPT" "$CANDIDATE_DB" "$SESSION_ID" 2>/dev/null)
            if [ -n "$INFO_JSON" ]; then
                SESSION_TITLE=$(echo "$INFO_JSON" | python -c "import sys,json; print(json.load(sys.stdin).get('title') or '')" 2>/dev/null)
                LAST_MESSAGE=$(echo "$INFO_JSON" | python -c "import sys,json; print(json.load(sys.stdin).get('last_message') or '')" 2>/dev/null)
                break
            fi
        fi
    done
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

# ── Timestamp ────────────────────────────────────────────────────────────────
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || echo "")

# ── Session URL (no web UI session for local CLI runs) ───────────────────────
SESSION_URL="${DEVIN_SESSION_URL:-}"

# ── Build JSON payload (using python for safe escaping) ──────────────────────
PAYLOAD=$(python -c "
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
