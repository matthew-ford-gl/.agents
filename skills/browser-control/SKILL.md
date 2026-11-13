---
name: browser-control
description: "Controls Chrome, Edge, and other Playwright browsers through scripted scenarios or an approved connection to an existing managed browser session. Use when asked to open a browser the agent can see and control, connect to signed-in tabs, test a UI flow, capture screenshots or accessibility snapshots, or inspect browser traffic. Not for: static HTML files on disk, build failures, backend-only debugging, or bypassing company browser and authentication policies."
---

# browser-control

Control a live browser via Playwright and run scripted scenarios. Output is JSON; large artifacts (screenshots, PDFs, HAR, AX tree) are written to disk paths you provide.

## Safety boundary

Confirm scope before automating login/submit flows on systems you do not own; do not hardcode real credentials in scenario files.

## Choose the connection mode

- For a repeatable, isolated test, use the scenario runner below. It launches a fresh context and closes it afterwards; it is not a shared, persistent browser session.
- For interactive assistance in an already signed-in managed Chrome or Edge, use the live connection workflow below. Trigger examples: "open a browser you can control", "connect to my signed-in Edge", and "Chrome remote debugging is running at this port".
- Opening a URL with the OS browser launcher does not establish agent control. A browser-preview proxy can change the origin and therefore storage and authentication behavior. Use the app's configured origin directly.

## Live connection to managed Chrome or Edge

1. Agree the target app origin and permitted actions with the user. Explain that the connection grants broad browser access even though the agent will restrict its actions to the agreed tab. Use this mode only where company policy permits it; stop if browser policy disables it. A blocked extension is not permission to circumvent an organisational restriction.
2. Ask the user to open their normal managed browser and visit `chrome://inspect/#remote-debugging` or `edge://inspect/#remote-debugging`. Have them enable **Allow remote debugging for this browser instance** and supply the displayed loopback endpoint. Do not assume port 9222: Edge used 63645 in the verified session.
3. Connect using Python Playwright in a persistent interactive shell (`exec` with `tty: true`). Use `python3 -i`, not a script that exits after a scenario. Replace `PORT` and `APP_ORIGIN` in this example with the agreed values:

```python
from playwright.sync_api import sync_playwright
from urllib.parse import urlsplit
p = sync_playwright().start()
browser = p.chromium.connect_over_cdp(
    "ws://127.0.0.1:PORT/devtools/browser", timeout=120000
)
app_origin = "APP_ORIGIN"
matches = [tab for ctx in browser.contexts for tab in ctx.pages
           if urlsplit(tab.url)[:2] == urlsplit(app_origin)[:2]]
page = matches[0] if len(matches) == 1 else None
print("Matching app tabs:", len(matches))
```

4. Ask the user to approve the browser's connection prompt. The HTTP discovery request to `http://127.0.0.1:PORT/json/version` can return 404 in this mode; the direct WebSocket endpoint above worked with Chrome 156, Edge, and Python Playwright 1.65 on macOS. If the WebSocket connection fails, recheck the displayed endpoint and approval rather than changing browser policies or guessing other endpoints.
5. If there are no matches, ask the user to open the app tab. If there are multiple, ask which to use before inspecting page contents. Inspect only the agreed tab; do not dump other tabs, cookies, credentials, storage state, or personal browsing data. Confirm connection by reading `page.title()` and reporting the agreed origin. Do not claim a connection merely because a browser window opened.
6. Keep the interactive process alive and send subsequent Playwright expressions to that same shell. Use `page.get_by_role(...)`, `page.screenshot(...)`, and `page.locator("body").aria_snapshot()` as appropriate. Let the user handle authentication; verify completion on the app origin with an exact selector such as `page.get_by_role("button", name="Sign out", exact=True)`, not a loose text match on an identity-provider page. Obtain approval before consequential submissions.
7. When finished, call `p.stop()` to disconnect the client without closing the user's browser. Do not call `browser.close()` or close the existing context. Recommend disabling remote debugging afterwards. After a browser restart, recheck the setting, endpoint, and connection approval; persistence of the checkbox has not been verified.

Complete when the agreed app tab has been inspected successfully, the user knows whether the connection remains live, and any requested interactions are verified.

### Authentication and compatibility boundaries

- A fresh Playwright profile has separate localStorage and sign-in state even on the same origin. `channel="chrome"` selects the binary, not the user's managed profile. The same applies to `msedge`.
- If a fresh profile hits conditional access (for example error 530003, device unregistered), stop retrying authentication. Use an approved connection to the working managed browser or involve IT. Do not recommend copying a personal profile, exporting session cookies, granting Full Disk Access, or weakening device policies as a solution; device compliance is not guaranteed to transfer.
- If no approved connection is available, use isolated browser tests with mocks and leave real-account verification to the user in their normal browser.
- The bundled runner's `axtree` action still calls the removed `page.accessibility.snapshot()` API and failed with Playwright 1.65. For a current live session, use `page.locator("body").aria_snapshot()` (ARIA snapshot text, not the old JSON schema). Report the runner limitation rather than promising that action works.

## Dependencies

```bash
pip install -r requirements.txt
playwright install chromium
```

If you already have Google Chrome installed and want to avoid downloading Chromium:

```bash
python scripts/browser.py --scenario scenario.json --channel chrome
```

## Quick start

1. Write a JSON scenario file (see format below).
2. Run it from the skill directory (or with the full path to `scripts/browser.py` on your OS):

```bash
python scripts/browser.py --scenario scenario.json
```

3. The script prints a JSON result with one entry per step.

## Scenario format

```json
{
  "browser": "chromium",
  "headless": true,
  "channel": "chromium",
  "viewport": [1280, 720],
  "timeout": 30000,
  "record_har_path": "output.har",
  "steps": [
    { "action": "navigate", "url": "https://example.com", "wait_until": "networkidle" },
    { "action": "click", "selector": "text=Sign in" },
    { "action": "fill", "selector": "#email", "text": "user@example.com" },
    { "action": "fill", "selector": "#password", "text": "secret" },
    { "action": "click", "selector": "role=button[name='Sign in']" },
    { "action": "wait_for_selector", "selector": ".dashboard" },
    { "action": "screenshot", "path": "dashboard.png", "full_page": true },
    { "action": "axtree", "path": "dashboard-ax.json" }
  ]
}
```

## Supported steps

| Action | Required keys | Optional keys |
|---|---|---|
| `navigate` | `url` | `wait_until` (default `networkidle`) |
| `click` | `selector` | — |
| `fill` / `type` | `selector`, `text` | — |
| `press` | `key` | — |
| `screenshot` | `path` | `full_page` (default `false`) |
| `pdf` | `path` | — |
| `axtree` | `path` | — |
| `evaluate` | `script` | — |
| `wait_for_selector` | `selector` | `state` (`visible`/`hidden`/`attached`/`detached`), `timeout` |
| `wait_for_text` | `text` | `timeout` |
| `set_viewport` | `width`, `height` | — |

## Selector tips

Playwright selector strings support multiple engines:

- CSS: `#submit`, `.btn-primary`
- Text: `text=Submit`, `text=/Submit/i`
- Role: `role=button[name="Submit"]`, `role=link[name="Next"]`
- XPath: `xpath=//button[@id='submit']`

## Cross-platform notes

- The script is pure Python and uses `playwright.sync_api`, which works on Windows, macOS, and Linux.
- `headless: true` is the default; use `headless: false` only on machines with a display.
- The script closes the browser and context cleanly and writes a HAR file when `record_har_path` is set.

## Workflow

1. Identify the goal: navigate, capture, audit, or automate.
2. Compose the scenario JSON with one step per action.
3. Run `scripts/browser.py --scenario <file>`.
4. Inspect the returned JSON and any artifacts on disk.
5. If the scenario fails, add `wait_for_selector` or `wait_for_text` steps before the failing action.
