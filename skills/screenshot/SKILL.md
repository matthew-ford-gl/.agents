---
name: screenshot
description: Capture and summarize screenshots from the local desktop, active window, or a named window. Use when the user asks for a screenshot, screen capture, active-window capture, visual inspection of the current screen, or named-window screenshot. Not for browser-page screenshots when browser or ui-review tools are already controlling a page.
---

# screenshot

Capture a local screenshot and summarize the visual result without loading large image data unnecessarily.

## Dependencies

```bash
pip install -r requirements.txt
```

`requirements.txt` covers `mss`, `Pillow`, and `pygetwindow` (Windows only, via platform marker). Named-window capture also relies on OS-specific tools that are not pip packages:

- **Windows**: `pygetwindow` (installed via requirements.txt)
- **macOS**: built-in `osascript` and `screencapture`
- **Linux**: `xdotool` (system package, install separately)

## Usage

From the skill directory (`~/.agents/skills/screenshot`):

```bash
# Full primary screen (default)
python scripts/capture.py

# Active/frontmost window
python scripts/capture.py --mode active

# Specific window by name (best-effort per OS)
python scripts/capture.py --mode window --name "Firefox"
python scripts/capture.py --mode window --name "Code"
python scripts/capture.py --mode window --name "Terminal"

# List available windows
python scripts/capture.py --list-windows
```

Output (JSON to stdout):

```json
{
  "timestamp": "...",
  "mode": "active",
  "platform": "Windows",
  "full_resolution": {
    "path": "C:/Users/.../Temp/screenshot_full.png",
    "width": 2560,
    "height": 1440,
    "size_bytes": 123456
  },
  "thumbnail": {
    "path": "C:/Users/.../Temp/screenshot_thumb.png",
    "width": 480,
    "height": 270,
    "size_bytes": 23456
  },
  "window": {
    "matched_name": "My Page - Firefox",
    "owner": "Firefox",
    "id": 12345
  }
}
```

The `window` field appears only in `--mode window`.

## Workflow

1. Determine the requested mode: `full`, `active`, or `window`.
2. Run `scripts/capture.py` with the appropriate arguments.
3. Read the full-resolution image from the returned `full_resolution.path`.
4. Return a concise summary: what is visible, key UI elements, state, and any actionable items.
5. If the user asked a specific question, answer it directly.
6. Complete when the summary covers every element the user asked about.

## Cross-platform notes

- `full` and `active` modes work on Windows, macOS, and Linux with only `mss` and `Pillow`.
- `window` mode is native on macOS (`screencapture -l`), uses `pygetwindow` on Windows, and `xdotool` on Linux. If the optional dependency is missing, fall back to `active` mode and explain the limitation.
- Keep the full-resolution file path; do not embed large PNG bytes in the response unless the host requires it.
