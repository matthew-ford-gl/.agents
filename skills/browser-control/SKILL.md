---
name: browser-control
description: Control a live Chromium/Chrome browser with Playwright to navigate, interact, capture screenshots, export PDFs, extract accessibility trees, record HAR files, and run browser scenarios. Use when automating a web page, testing a UI flow, taking a page screenshot, running Lighthouse/accessibility checks, or capturing network traffic. Not for static HTML files on disk, build failures, or backend-only debugging.
---

# browser-control

Control a live browser via Playwright and run scripted scenarios. Output is JSON; large artifacts (screenshots, PDFs, HAR, AX tree) are written to disk paths you provide.

## Dependencies

```bash
pip install playwright
playwright install chromium
```

If you already have Google Chrome installed and want to avoid downloading Chromium:

```bash
python scripts/browser.py --scenario scenario.json --channel chrome
```

## Quick start

1. Write a JSON scenario file (see format below).
2. Run it:

```bash
python ~/.agents/skills/browser-control/scripts/browser.py --scenario scenario.json
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
