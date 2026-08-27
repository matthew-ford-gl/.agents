#!/usr/bin/env bash
set -euo pipefail

WITH_DEVIN=false
WITH_CLAUDE=false
args=()

for arg in "$@"; do
    case "$arg" in
        --devin)
            WITH_DEVIN=true
            ;;
        --claude)
            WITH_CLAUDE=true
            ;;
        *)
            args+=("$arg")
            ;;
    esac
done

if [[ "$WITH_DEVIN" == false && "$WITH_CLAUDE" == false ]]; then
    WITH_CLAUDE=true
fi

SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)
TARGET_DIR="${args[0]:-$SCRIPT_DIR/..}"
TARGET_DIR=$(cd "$TARGET_DIR" && pwd)

AGENTS_SOURCE="$SCRIPT_DIR/agents"
SKILLS_SOURCE="$SCRIPT_DIR/skills"

echo "Uninstalling agents and skills from $TARGET_DIR"

shopt -s nullglob

if [[ -d "$AGENTS_SOURCE" ]]; then
    for agent_dir in "$AGENTS_SOURCE"/*/; do
        agent_dir=${agent_dir%/}
        agent_name=$(basename "$agent_dir")

        if [[ "$WITH_CLAUDE" == true ]]; then
            claude_link="$TARGET_DIR/.claude/agents/$agent_name.md"
            if [[ -e "$claude_link" || -L "$claude_link" ]]; then
                rm -f "$claude_link"
                echo "Removed Claude agent: $agent_name"
            fi
        fi

        if [[ "$WITH_DEVIN" == true ]]; then
            devin_link="$TARGET_DIR/.devin/agents/$agent_name"
            if [[ -e "$devin_link" || -L "$devin_link" ]]; then
                rm -rf "$devin_link"
                echo "Removed Devin agent: $agent_name"
            fi
        fi
    done
fi

if [[ -d "$SKILLS_SOURCE" ]]; then
    for skill_dir in "$SKILLS_SOURCE"/*/; do
        skill_dir=${skill_dir%/}
        skill_name=$(basename "$skill_dir")

        if [[ "$WITH_CLAUDE" == true ]]; then
            claude_link="$TARGET_DIR/.claude/skills/$skill_name"
            if [[ -e "$claude_link" || -L "$claude_link" ]]; then
                rm -rf "$claude_link"
                echo "Removed Claude skill: $skill_name"
            fi
        fi

        if [[ "$WITH_DEVIN" == true ]]; then
            devin_link="$TARGET_DIR/.devin/skills/$skill_name"
            if [[ -e "$devin_link" || -L "$devin_link" ]]; then
                rm -rf "$devin_link"
                echo "Removed Devin skill: $skill_name"
            fi
        fi
    done
fi

# Remove hooks symlink
CLAUDE_SETTINGS_LOCAL="$TARGET_DIR/.claude/settings.local.json"
if [[ -L "$CLAUDE_SETTINGS_LOCAL" ]]; then
    rm -f "$CLAUDE_SETTINGS_LOCAL"
    echo "Removed hooks symlink: $CLAUDE_SETTINGS_LOCAL"
fi

echo "Done."
