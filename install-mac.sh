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
HOOKS_SOURCE="$SCRIPT_DIR/hooks/hooks.json"

install_skill_dependencies() {
    local python_cmd
    if command -v python3 >/dev/null 2>&1; then
        python_cmd=$(command -v python3)
    elif command -v python >/dev/null 2>&1; then
        python_cmd=$(command -v python)
    else
        echo "Python 3 is required to install screenshot and browser-control dependencies." >&2
        return 1
    fi

    "$python_cmd" -m pip install \
        -r "$SKILLS_SOURCE/screenshot/requirements.txt" \
        -r "$SKILLS_SOURCE/browser-control/requirements.txt"
    "$python_cmd" -m playwright install chromium
}

render_claude_definition() {
    local source_file=$1
    local destination_file=$2
    local model_info model_count source_model claude_model

    model_info=$(awk '
        NR == 1 && $0 == "---" { in_frontmatter = 1; next }
        in_frontmatter && $0 == "---" { in_frontmatter = 0; next }
        in_frontmatter && /^model:[[:space:]]*[^[:space:]]+[[:space:]]*$/ {
            count++
            model = $0
            sub(/^model:[[:space:]]*/, "", model)
            sub(/[[:space:]]*$/, "", model)
        }
        END { printf "%d:%s", count, model }
    ' "$source_file")
    model_count=${model_info%%:*}
    source_model=${model_info#*:}

    if [[ "$model_count" == "0" ]]; then
        cp "$source_file" "$destination_file"
        return
    fi
    if [[ "$model_count" != "1" ]]; then
        echo "Expected at most one model declaration in $source_file, found $model_count" >&2
        return 1
    fi

    case "$source_model" in
        opus) claude_model=opus ;;
        sonnet) claude_model=sonnet ;;
        swe) claude_model=haiku ;;
        *)
            echo "No Claude Code model mapping for '$source_model' in $source_file" >&2
            return 1
            ;;
    esac

    awk -v model="$claude_model" '
        NR == 1 && $0 == "---" { in_frontmatter = 1; print; next }
        in_frontmatter && $0 == "---" { in_frontmatter = 0; print; next }
        in_frontmatter && /^model:[[:space:]]*[^[:space:]]+[[:space:]]*$/ { print "model: " model; next }
        { print }
    ' "$source_file" > "$destination_file"
}

echo "Installing agents and skills from $SCRIPT_DIR into $TARGET_DIR"
install_skill_dependencies

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
            render_claude_definition "$agent_file" "$claude_link"
            echo "Rendered Claude agent: $claude_link"
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
            cp -R "$skill_dir" "$claude_link"
            render_claude_definition "$skill_file" "$claude_link/SKILL.md"
            echo "Rendered Claude skill: $claude_link"
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

# Hooks — symlink hooks.json to ~/.claude/settings.local.json
if [[ -f "$HOOKS_SOURCE" && -d "$TARGET_DIR/.claude" ]]; then
    CLAUDE_SETTINGS_LOCAL="$TARGET_DIR/.claude/settings.local.json"
    if [[ -e "$CLAUDE_SETTINGS_LOCAL" || -L "$CLAUDE_SETTINGS_LOCAL" ]]; then
        rm -f "$CLAUDE_SETTINGS_LOCAL"
    fi
    ln -s "$HOOKS_SOURCE" "$CLAUDE_SETTINGS_LOCAL"
    echo "Linked hooks: $CLAUDE_SETTINGS_LOCAL -> $HOOKS_SOURCE"
fi

# Remove stale Devin copies when Devin is present but not being linked.
if [[ "$WITH_DEVIN" == false && -d "$TARGET_DIR/.devin" ]]; then
    if [[ -d "$AGENTS_SOURCE" ]]; then
        for agent_dir in "$AGENTS_SOURCE"/*/; do
            agent_dir=${agent_dir%/}
            agent_name=$(basename "$agent_dir")
            stale="$TARGET_DIR/.devin/agents/$agent_name"
            if [[ -e "$stale" && ! -L "$stale" ]]; then
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
            if [[ -e "$stale" && ! -L "$stale" ]]; then
                rm -rf "$stale"
                echo "Removed stale Devin skill copy: $skill_name"
            fi
        done
    fi
fi

echo "Done."
