#!/usr/bin/env python3
"""Cross-platform screenshot capture with thumbnail and metadata output.

Usage:
    python capture.py [--mode full|active|window] [--name NAME] [--output DIR] [--thumb-width WIDTH]
    python capture.py --list-windows

Modes:
    full    - Capture the full primary screen (default)
    active  - Capture the frontmost/active window
    window  - Capture a specific window by name (requires --name; best-effort on Windows/Linux, native on macOS)

Outputs:
    - Full resolution: {output}/screenshot_full.png
    - Thumbnail:       {output}/screenshot_thumb.png (default 480px width)
    - Metadata JSON to stdout

Dependencies:
    pip install mss Pillow
Optional:
    Windows named-window capture: pygetwindow
    Linux named-window capture:   xdotool (system package)
    macOS named-window capture:   built-in screencapture + osascript
"""

import argparse
import json
import platform
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path

try:
    import mss
    import mss.tools
except ImportError:
    print("Error: mss not installed. Run: pip install mss", file=sys.stderr)
    sys.exit(1)

try:
    from PIL import Image
except ImportError:
    print("Error: Pillow not installed. Run: pip install Pillow", file=sys.stderr)
    sys.exit(1)

SYSTEM = platform.system()


def _warn(message):
    print(f"Warning: {message}", file=sys.stderr)


def get_active_window_bounds():
    """Return active window bounds as {left, top, width, height} or None."""
    if SYSTEM == "Darwin":
        script = '''
        tell application "System Events"
            set frontApp to first application process whose frontmost is true
            set frontWindow to first window of frontApp
            set {x, y} to position of frontWindow
            set {w, h} to size of frontWindow
            return {x, y, w, h}
        end tell
        '''
        try:
            result = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                values = [int(v.strip()) for v in result.stdout.strip().split(",")]
                return {"left": values[0], "top": values[1],
                        "width": values[2], "height": values[3]}
        except Exception as e:
            _warn(f"Could not get active window: {e}")
        return None

    if SYSTEM == "Windows":
        try:
            import ctypes
            from ctypes import wintypes
            user32 = ctypes.windll.user32
            hwnd = user32.GetForegroundWindow()
            rect = wintypes.RECT()
            user32.GetWindowRect(hwnd, ctypes.byref(rect))
            return {
                "left": rect.left,
                "top": rect.top,
                "width": rect.right - rect.left,
                "height": rect.bottom - rect.top,
            }
        except Exception as e:
            _warn(f"Could not get active window: {e}")
        return None

    if SYSTEM == "Linux":
        return _linux_window_geometry("getactivewindow")

    return None


def _linux_window_geometry(window_arg):
    """Return geometry from xdotool for a window id or getactivewindow."""
    if not shutil.which("xdotool"):
        _warn("xdotool not found. Install it for active/named-window capture on Linux.")
        return None
    try:
        result = subprocess.run(
            ["xdotool", window_arg, "getwindowgeometry", "--shell"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            geo = {}
            for line in result.stdout.strip().split("\n"):
                if "=" in line:
                    key, val = line.split("=", 1)
                    geo[key.strip()] = int(val.strip())
            return {
                "left": geo.get("X", 0),
                "top": geo.get("Y", 0),
                "width": geo.get("WIDTH", 800),
                "height": geo.get("HEIGHT", 600),
            }
    except Exception as e:
        _warn(f"Could not get Linux window geometry: {e}")
    return None


def list_windows():
    """Best-effort list of visible windows."""
    if SYSTEM == "Darwin":
        script = '''
        tell application "System Events"
            set windowList to {}
            repeat with p in (get processes whose background only is false)
                try
                    set n to name of p
                    set w to name of first window of p
                    set end of windowList to (n & "|" & w)
                end try
            end repeat
            return windowList
        end tell
        '''
        try:
            result = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                items = [line.strip().strip('"') for line in result.stdout.split(",") if "|" in line]
                return [{"owner": i.split("|", 1)[1], "name": i.split("|", 1)[1],
                         "title": i.split("|", 1)[1]} for i in items]
        except Exception as e:
            _warn(f"Could not list windows: {e}")

    if SYSTEM == "Windows":
        try:
            import pygetwindow
            return [
                {"owner": w.title, "name": w.title, "title": w.title}
                for w in pygetwindow.getAllWindows() if w.title.strip()
            ]
        except ImportError:
            _warn("pygetwindow not installed. Install it with: pip install pygetwindow")
        except Exception as e:
            _warn(f"Could not list windows: {e}")

    if SYSTEM == "Linux":
        if shutil.which("xdotool"):
            try:
                result = subprocess.run(
                    ["xdotool", "search", "--onlyvisible", "--name", ".*"],
                    capture_output=True, text=True, timeout=5
                )
                windows = []
                for wid in result.stdout.strip().split("\n"):
                    if not wid:
                        continue
                    title = subprocess.run(
                        ["xdotool", "getwindowname", wid],
                        capture_output=True, text=True, timeout=2
                    ).stdout.strip()
                    windows.append({"owner": title, "name": title, "title": title})
                return windows
            except Exception as e:
                _warn(f"Could not list windows: {e}")
        else:
            _warn("xdotool not found. Install it to list windows on Linux.")

    return []


def find_window_by_name(name):
    """Return window info dict with id and bounds, or raise."""
    name_lower = name.lower()

    if SYSTEM == "Darwin":
        script = f'''
        tell application "System Events"
            set matches to {{}}
            repeat with p in (get processes whose background only is false)
                try
                    set pName to name of p
                    repeat with w in (windows of p)
                        set wName to name of w
                        if (wName as string) contains "{name}" or (pName as string) contains "{name}" then
                            set wId to id of w
                            set end of matches to (pName & "|" & wName & "|" & wId)
                        end if
                    end repeat
                end try
            end repeat
            return matches
        end tell
        '''
        try:
            result = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0 and result.stdout.strip():
                parts = result.stdout.strip().split(",")[0].strip().strip('"').split("|")
                return {"id": int(parts[2]), "owner": parts[0], "name": parts[1]}
        except Exception as e:
            _warn(f"Could not find macOS window: {e}")
        raise RuntimeError(f"No window matching '{name}'")

    if SYSTEM == "Windows":
        try:
            import pygetwindow
            windows = [w for w in pygetwindow.getAllWindows() if name_lower in w.title.lower()]
            if not windows:
                raise RuntimeError(f"No window matching '{name}'")
            w = windows[0]
            return {
                "id": w._hWnd,
                "owner": w.title,
                "name": w.title,
                "bounds": {
                    "left": w.left,
                    "top": w.top,
                    "width": w.width,
                    "height": w.height,
                },
            }
        except ImportError:
            _warn("pygetwindow not installed. Install it with: pip install pygetwindow")
            raise RuntimeError("Named window capture requires pygetwindow on Windows")
        except Exception as e:
            raise RuntimeError(f"Could not find window: {e}")

    if SYSTEM == "Linux":
        if not shutil.which("xdotool"):
            raise RuntimeError("Named window capture on Linux requires xdotool")
        try:
            result = subprocess.run(
                ["xdotool", "search", "--name", name],
                capture_output=True, text=True, timeout=5
            )
            wids = [w.strip() for w in result.stdout.strip().split("\n") if w.strip()]
            if not wids:
                raise RuntimeError(f"No window matching '{name}'")
            wid = wids[0]
            title = subprocess.run(
                ["xdotool", "getwindowname", wid],
                capture_output=True, text=True, timeout=2
            ).stdout.strip()
            bounds = _linux_window_geometry(wid)
            if not bounds:
                raise RuntimeError(f"Could not get geometry for '{name}'")
            return {"id": wid, "owner": title, "name": title, "bounds": bounds}
        except RuntimeError:
            raise
        except Exception as e:
            raise RuntimeError(f"Could not find window: {e}")

    raise RuntimeError(f"Window capture not supported on {SYSTEM}")


def capture_full_or_active(sct, mode):
    """Capture full screen or active window using mss."""
    if mode == "active":
        bounds = get_active_window_bounds()
        if bounds:
            return sct.grab(bounds)
        _warn("Falling back to full screen capture")
    monitor = sct.monitors[1] if len(sct.monitors) > 1 else sct.monitors[0]
    return sct.grab(monitor)


def capture_named_window_macos(window_info, full_path):
    """Use macOS screencapture for a window id."""
    subprocess.run(
        ["screencapture", "-x", "-o", "-l", str(window_info["id"]), str(full_path)],
        check=True, timeout=10
    )
    with Image.open(full_path) as img:
        return img.width, img.height


def capture_screenshot(mode="full", output_dir=None, thumb_width=480, window_name=None):
    """Capture screenshot and create thumbnail."""
    if output_dir is None:
        output_dir = tempfile.gettempdir()

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    full_path = output_dir / "screenshot_full.png"
    thumb_path = output_dir / "screenshot_thumb.png"

    window_info = None

    if mode == "window":
        if not window_name:
            raise ValueError("--name is required for window mode")

        if SYSTEM == "Darwin":
            window_info = find_window_by_name(window_name)
            width, height = capture_named_window_macos(window_info, full_path)
        else:
            window_info = find_window_by_name(window_name)
            bounds = window_info.get("bounds") or window_info
            with mss.mss() as sct:
                screenshot = sct.grab(bounds)
                mss.tools.to_png(screenshot.rgb, screenshot.size, output=str(full_path))
                width, height = screenshot.size

    else:
        with mss.mss() as sct:
            screenshot = capture_full_or_active(sct, mode)
            mss.tools.to_png(screenshot.rgb, screenshot.size, output=str(full_path))
            width, height = screenshot.size

    with Image.open(full_path) as img:
        ratio = thumb_width / img.width
        thumb_height = int(img.height * ratio)
        thumb = img.resize((thumb_width, thumb_height), Image.LANCZOS)
        thumb.save(thumb_path, "PNG", optimize=True)

    metadata = {
        "timestamp": datetime.now().isoformat(),
        "mode": mode,
        "platform": SYSTEM,
        "full_resolution": {
            "path": str(full_path),
            "width": width,
            "height": height,
            "size_bytes": full_path.stat().st_size,
        },
        "thumbnail": {
            "path": str(thumb_path),
            "width": thumb_width,
            "height": thumb_height,
            "size_bytes": thumb_path.stat().st_size,
        },
    }

    if window_info:
        metadata["window"] = {
            "matched_name": window_info.get("name", ""),
            "owner": window_info.get("owner", ""),
            "id": window_info.get("id"),
        }

    return metadata


def main():
    parser = argparse.ArgumentParser(description="Capture screenshot with thumbnail")
    parser.add_argument(
        "--mode", choices=["full", "active", "window"], default="full",
        help="Capture mode: full screen, active window, or named window"
    )
    parser.add_argument(
        "--name", type=str, default=None,
        help="Window name to capture (required for --mode window)."
    )
    parser.add_argument(
        "--output", "-o", type=str, default=None,
        help="Output directory (default: system temp)"
    )
    parser.add_argument(
        "--thumb-width", type=int, default=480,
        help="Thumbnail width in pixels (default: 480)"
    )
    parser.add_argument(
        "--list-windows", action="store_true",
        help="List available windows and exit"
    )

    args = parser.parse_args()

    try:
        if args.list_windows:
            windows = list_windows()
            print(json.dumps(windows, indent=2))
            return

        metadata = capture_screenshot(
            mode=args.mode,
            output_dir=args.output,
            thumb_width=args.thumb_width,
            window_name=args.name,
        )
        print(json.dumps(metadata, indent=2))

    except Exception as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
