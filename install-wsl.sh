#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)
MAC_INSTALLER="$SCRIPT_DIR/install-mac.sh"

if [[ ! -f "$MAC_INSTALLER" ]]; then
    echo "install-mac.sh not found; is this repo intact?" >&2
    exit 1
fi

# Default the install target to the WSL home directory so a checkout on a
# Windows-mounted drive (e.g. /mnt/c/Users/<you>/.agents) still installs
# into the Linux filesystem where Claude Code / Devin CLI expect it.
TARGET_DIR="$HOME"
USER_FLAGS=()

for arg in "$@"; do
    case "$arg" in
        --devin|--claude)
            USER_FLAGS+=("$arg")
            ;;
        *)
            TARGET_DIR="$arg"
            ;;
    esac
done

exec "$MAC_INSTALLER" "$TARGET_DIR" "${USER_FLAGS[@]}"
