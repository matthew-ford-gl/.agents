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

# Default to Claude-style installation (flat .md files in .claude/agents)
# because the skill prompts in this library expect .claude/agents/<name>.md.
if [[ "$WITH_DEVIN" == false && "$WITH_CLAUDE" == false ]]; then
    WITH_CLAUDE=true
fi

SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)
# Default to the parent of this .agents repo so a clone at ~/.agents installs
# into the user's home directory.
TARGET_DIR="${args[0]:-$SCRIPT_DIR/..}"
TARGET_DIR=$(cd "$TARGET_DIR" && pwd)

AGENTS_SOURCE="$SCRIPT_DIR/agents"
SKILLS_SOURCE="$SCRIPT_DIR/skills"

echo "Installing agents and skills from $SCRIPT_DIR into $TARGET_DIR"

if [[ "$WITH_CLAUDE" == true ]]; then
    CLAUDE_AGENTS_DIR="$TARGET_DIR/.claude/agents"
    CLAUDE_SKILLS_DIR="$TARGET_DIR/.claude/skills"
    mkdir -p "$CLAUDE_AGENTS_DIR" "$CLAUDE_SKILLS_DIR"
fi

if [[ "$WITH_DEVIN" == true ]]; then
    DEVIN_AGENTS_DIR="$TARGET_DIR/.devin/agents"
    DEVIN_SKILLS_DIR="$TARGET_DIR/.devin/skills"
    mkdir -p "$DEVIN_AGENTS_DIR" "$DEVIN_SKILLS_DIR"
fi

shopt -s nullglob

# Agents
if [[ -d "$AGENTS_SOURCE" ]]; then
    for agent_dir in "$AGENTS_SOURCE"/*/; do
        agent_dir=${agent_dir%/}
        agent_name=$(basename "$agent_dir")
        agent_file="$agent_dir/AGENT.md"

        if [[ ! -f "$agent_file" ]]; then
            echo "SKIP $agent_name — no AGENT.md at $agent_file"
            continue
        fi

        if [[ "$WITH_CLAUDE" == true ]]; then
            claude_link="$CLAUDE_AGENTS_DIR/$agent_name.md"
            if [[ -e "$claude_link" || -L "$claude_link" ]]; then
                rm -f "$claude_link"
            fi
            ln -s "$agent_file" "$claude_link"
            echo "Linked Claude agent: $claude_link -> $agent_file"
        fi

        if [[ "$WITH_DEVIN" == true ]]; then
            devin_link="$DEVIN_AGENTS_DIR/$agent_name"
            if [[ -e "$devin_link" || -L "$devin_link" ]]; then
                rm -rf "$devin_link"
            fi
            ln -s "$agent_dir" "$devin_link"
            echo "Linked Devin agent: $devin_link -> $agent_dir"
        fi
    done
fi

# Skills
if [[ -d "$SKILLS_SOURCE" ]]; then
    for skill_dir in "$SKILLS_SOURCE"/*/; do
        skill_dir=${skill_dir%/}
        skill_name=$(basename "$skill_dir")
        skill_file="$skill_dir/SKILL.md"

        if [[ ! -f "$skill_file" ]]; then
            echo "SKIP $skill_name — no SKILL.md at $skill_file"
            continue
        fi

        if [[ "$WITH_CLAUDE" == true ]]; then
            claude_link="$CLAUDE_SKILLS_DIR/$skill_name"
            if [[ -e "$claude_link" || -L "$claude_link" ]]; then
                rm -rf "$claude_link"
            fi
            ln -s "$skill_dir" "$claude_link"
            echo "Linked Claude skill: $claude_link -> $skill_dir"
        fi

        if [[ "$WITH_DEVIN" == true ]]; then
            devin_link="$DEVIN_SKILLS_DIR/$skill_name"
            if [[ -e "$devin_link" || -L "$devin_link" ]]; then
                rm -rf "$devin_link"
            fi
            ln -s "$skill_dir" "$devin_link"
            echo "Linked Devin skill: $devin_link -> $skill_dir"
        fi
    done
fi

# Remove stale Devin copies when Devin is present but not being linked.
if [[ "$WITH_DEVIN" == false && -d "$TARGET_DIR/.devin" ]]; then
    if [[ -d "$AGENTS_SOURCE" ]]; then
        for agent_dir in "$AGENTS_SOURCE"/*/; do
            agent_dir=${agent_dir%/}
            agent_name=$(basename "$agent_dir")
            stale="$TARGET_DIR/.devin/agents/$agent_name"
            if [[ -e "$stale" || -L "$stale" ]]; then
                rm -rf "$stale"
                echo "Removed stale Devin agent copy: $agent_name"
            fi
        done
    fi

    if [[ -d "$SKILLS_SOURCE" ]]; then
        for skill_dir in "$SKILLS_SOURCE"/*/; do
            skill_dir=${skill_dir%/}
            skill_name=$(basename "$skill_dir")
            stale="$TARGET_DIR/.devin/skills/$skill_name"
            if [[ -e "$stale" || -L "$stale" ]]; then
                rm -rf "$stale"
                echo "Removed stale Devin skill copy: $skill_name"
            fi
        done
    fi
fi

echo "Done."
