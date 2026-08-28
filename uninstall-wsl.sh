#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)
MAC_UNINSTALLER="$SCRIPT_DIR/uninstall-mac.sh"

if [[ ! -f "$MAC_UNINSTALLER" ]]; then
    echo "uninstall-mac.sh not found; is this repo intact?" >&2
    exit 1
fi

# Default the uninstall target to the WSL home directory so it matches
# install-wsl.sh even when the repo lives on a Windows-mounted drive.
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

exec "$MAC_UNINSTALLER" "$TARGET_DIR" "${USER_FLAGS[@]}"
