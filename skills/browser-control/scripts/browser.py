#!/usr/bin/env python3
"""Cross-platform browser automation via Playwright.

Reads a JSON scenario file and executes it step-by-step. Prints a JSON result to stdout and writes artifacts to disk.

Usage:
    python browser.py --scenario scenario.json
    python browser.py --scenario scenario.json --channel chrome
"""

import argparse
import json
import sys
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
except ImportError:
    print(
        json.dumps({
            "error": "playwright not installed. Run: pip install playwright && playwright install chromium"
        }),
        file=sys.stderr,
    )
    sys.exit(1)

DEFAULT_WAIT_UNTIL = "networkidle"
DEFAULT_TIMEOUT = 30000


def run_scenario(scenario):
    results = []
    try:
        with sync_playwright() as p:
            browser_type_name = scenario.get("browser", "chromium")
            if browser_type_name not in ("chromium", "firefox", "webkit"):
                raise ValueError(f"Unsupported browser: {browser_type_name}")
            bt = getattr(p, browser_type_name)

            launch_args = {
                "headless": scenario.get("headless", True),
            }
            if scenario.get("channel"):
                launch_args["channel"] = scenario["channel"]

            browser = bt.launch(**launch_args)

            context_options = {}
            if "viewport" in scenario:
                w, h = scenario["viewport"]
                context_options["viewport"] = {"width": w, "height": h}
            if "device" in scenario and scenario["device"] in p.devices:
                context_options.update(p.devices[scenario["device"]])
            if scenario.get("record_har_path"):
                context_options["record_har_path"] = scenario["record_har_path"]

            context = browser.new_context(**context_options)
            page = context.new_page()
            page.set_default_timeout(scenario.get("timeout", DEFAULT_TIMEOUT))

            for step in scenario.get("steps", []):
                action = step.get("action")
                res = {"action": action, "status": "ok"}
                try:
                    if action == "navigate":
                        page.goto(
                            step["url"],
                            wait_until=step.get("wait_until", DEFAULT_WAIT_UNTIL),
                        )
                    elif action == "click":
                        page.locator(step["selector"]).click()
                    elif action in ("fill", "type"):
                        page.locator(step["selector"]).fill(step["text"])
                    elif action == "press":
                        page.keyboard.press(step["key"])
                    elif action == "screenshot":
                        page.screenshot(
                            path=step["path"], full_page=step.get("full_page", False)
                        )
                        res["path"] = step["path"]
                    elif action == "pdf":
                        page.pdf(path=step["path"])
                        res["path"] = step["path"]
                    elif action == "axtree":
                        snapshot = page.accessibility.snapshot()
                        Path(step["path"]).write_text(json.dumps(snapshot, indent=2))
                        res["path"] = step["path"]
                    elif action == "evaluate":
                        res["result"] = page.evaluate(step["script"])
                    elif action == "wait_for_selector":
                        page.locator(step["selector"]).wait_for(
                            state=step.get("state", "visible"),
                            timeout=step.get("timeout"),
                        )
                    elif action == "wait_for_text":
                        page.get_by_text(step["text"]).wait_for(
                            state="visible", timeout=step.get("timeout")
                        )
                    elif action == "set_viewport":
                        page.set_viewport_size(
                            {"width": step["width"], "height": step["height"]}
                        )
                    else:
                        raise ValueError(f"Unknown action: {action}")
                except PlaywrightTimeout:
                    res["status"] = "timeout"
                    res["error"] = "Timeout waiting for step"
                    if step.get("continue_on_error"):
                        results.append(res)
                        continue
                    results.append(res)
                    raise
                except Exception as e:
                    res["status"] = "error"
                    res["error"] = str(e)
                    if step.get("continue_on_error"):
                        results.append(res)
                        continue
                    results.append(res)
                    raise
                results.append(res)

            context.close()
            browser.close()

        result = {"status": "ok", "results": results}
        if scenario.get("record_har_path"):
            result["har_path"] = scenario["record_har_path"]
        return result
    except Exception as e:
        return {"status": "error", "error": str(e), "results": results}


def main():
    parser = argparse.ArgumentParser(description="Run a Playwright browser scenario")
    parser.add_argument("--scenario", required=True, help="Path to JSON scenario file")
    parser.add_argument(
        "--channel",
        default=None,
        help="Browser channel, e.g. chrome, msedge, chromium",
    )
    args = parser.parse_args()

    scenario_path = Path(args.scenario)
    if not scenario_path.exists():
        print(json.dumps({"error": f"Scenario file not found: {args.scenario}"}), file=sys.stderr)
        sys.exit(1)

    scenario = json.loads(scenario_path.read_text())
    if args.channel and not scenario.get("channel"):
        scenario["channel"] = args.channel

    result = run_scenario(scenario)
    print(json.dumps(result, indent=2, default=str))
    sys.exit(0 if result["status"] == "ok" else 1)


if __name__ == "__main__":
    main()
