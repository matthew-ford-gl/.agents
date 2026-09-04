---
name: ui-review
description: "Captures screenshots, analyses, and fixes UX issues route-by-route against a ui-review.json config. Use when iterating on touch-target/clipping/critical-action problems across routes. Not for: WCAG audits (use web-accessibility) or performance profiling (use web-performance)."
argument-hint: "[route | all]"
model: opus  # per-screenshot UX judgment calls and multi-attempt fix decisions need stronger reasoning than mechanical dispatch
---
You are an iterative UI review orchestrator.

Input: `$ARGUMENTS` — a route name to jump to, `all` to restart from the beginning, or empty to resume / start fresh.

## What This Command Does

Captures screenshots of each configured route, analyses them for touch-screen UX issues (missing content, clipped elements, small touch targets, layout problems), fixes any issues found, re-captures to verify, and advances to the next route. Loops until every route is clean or 3 fix attempts are exhausted per route.

Requires a `.claude/ui-review.json` config file in the repo root.

**Disclosure: this workflow runs autonomously across multiple destructive and
side-effecting actions with no human STOP points in between.** Once started, it will,
without pausing for per-step approval: delete existing screenshot directories (Step 0),
start background services on local ports (Step 3), and repeatedly edit source files
across up to 3 fix attempts per route (Step 6B). Only invoke this skill when you intend
to consent to that up front.

---

## Phase 0: Load Project Context

Before reading the UI-review config, load the project-specific context:
1. Read the repository root `AGENTS.md` and any nearer `AGENTS.md` files for the routes you
   will review. Treat repository instructions as mandatory.
2. If `.claude/CLAUDE.md` exists in the repo root, read it.
3. If `.context/index.md` exists, scan it for keywords matching the UI/accessibility domain and
   load every matched standard, playbook, and convention file into your context.

## Configuration

Read `.claude/ui-review.json` from the repo root. If it is absent, stop and print:

```
❌  No .claude/ui-review.json found. Create one to configure this command.
    See the ui-review.json schema below for required fields.
```

### Config schema

```jsonc
{
  // Working directory for Playwright (relative to repo root)
  "appDir": "src/web/my-app",

  // Where screenshots land, relative to appDir
  "screenshotsDir": "screenshots",

  // State file path, relative to appDir
  "stateFile": ".ux-fix-state.json",

  // Playwright project name for capture runs
  "playwrightProject": "visual-capture",

  // Optional: env var names passed to Playwright — omit either to skip that env var
  "tierEnvVar": "UX_TIER",     // passed with the "tier" value below
  "routeEnvVar": "UX_ROUTES",  // passed with the current route name

  // Optional: tier value (only used when tierEnvVar is set)
  "tier": "1",

  // Source directory for editable files, relative to appDir
  "sourceDir": "src",

  // Optional: quality gate commands (defaults shown)
  "lintCommand": "npm run lint",
  "testCommand": "npm run test",

  // Ordered list of routes to review
  "routes": [
    {
      // Route name — passed to routeEnvVar and used as the screenshot filename stem
      "name": "login",

      // Plain-English description of what a healthy render looks like
      "expectedContent": "PIN pad (0–9, backspace, clear), Sign On button",

      // Actions that must be visible without scrolling — each triggers FAIL if absent
      "criticalActions": ["Sign On"],

      // Service keys (from "services" map) required before capturing this route
      "requiresServices": []
    }
  ],

  // Named prerequisite services — only define those you need
  "services": {
    "example-service": {
      "port": 3001,
      "startCommand": "npm run dev",
      // Working directory for startCommand, relative to repo root
      "workingDir": "src/web/example-service",
      // Seconds to wait after starting before capturing
      "startupDelay": 4
    }
  }
}
```

---

## Step 0: Parse Arguments

- `all` → delete `{appDir}/{stateFile}` if it exists; delete all files in `{appDir}/{screenshotsDir}/` if the directory exists; proceed as if no state file.
- Route name → write (or overwrite) the state file: `"current"` = route name, `"attempt"` = 1, keep `"completed"` if the file already existed, otherwise set it to `[]`.
- Empty and **no state file exists** → delete all files in `{appDir}/{screenshotsDir}/` if the directory exists; proceed as a fresh run.
- Empty and state file exists → read existing state and resume (do not clear screenshots).

**Screenshot cleanup** — use the shell appropriate for the platform. See
`references/platform-commands.md` → "Screenshot cleanup (Step 0)" for the PowerShell/Bash
command pair.

---

## Step 1: State File

**Path:** `{appDir}/{stateFile}` (both values from config)

```json
{
  "completed": [],
  "current":   "{first route name from config}",
  "attempt":   1
}
```

- `completed` — routes confirmed clean; never remove entries.
- `current` — route being processed this iteration.
- `attempt` — fix attempts on the current route; resets to `1` on advance.

Read the file at the start of every iteration. If absent, initialise with the defaults above (using `config.routes[0].name`) and write it before proceeding.

---

## Step 2: Exit Check

If `completed` contains every route name from `config.routes`, print:

```
✅  All routes clean. UI review complete.
```

Stop. Do not schedule another wakeup.

---

## Step 3: Prerequisite Services

Look up the current route in `config.routes`. For each key in `requiresServices`, look it up in `config.services` and ensure it is running on its configured port before capturing.

See `references/platform-commands.md` → "Prerequisite services (Step 3)" for the
PowerShell/Bash command pair that checks the port and starts the service if needed.

---

## Step 4: Capture

From `{appDir}`, run Playwright. Include only the env vars whose config keys are present — skip `tierEnvVar` / `routeEnvVar` entirely if they are not defined in config.

See `references/platform-commands.md` → "Capture (Step 4)" for the PowerShell/Bash
command pair and where screenshots land.

---

## Step 5: Analyse

Glob for `{screenshotsDir}/{current}--*.png` inside `{appDir}`, then read every matching PNG with the Read tool. Read them all before drawing any conclusions.

Look up the current route in `config.routes`. Use `expectedContent` as the FAIL condition for check 1 and `criticalActions` for check 7.

### Assessment checklist (apply to every screenshot)

| # | Check | Severity if failed |
|---|---|---|
| 1 | Expected content present (per `expectedContent` in config) | FAIL |
| 2 | Every interactive element ≥ 44 px in both dimensions | WARN |
| 3 | Body text readable at arm's length (≥ 14 px equivalent on device) | WARN |
| 4 | Nothing clipped at viewport edges | WARN |
| 5 | Keypad / numpad comfortable for the orientation (if present) | WARN |
| 6 | Layout adapts between portrait and landscape (only if both orientations were captured) | WARN |
| 7 | All `criticalActions` visible without scrolling | FAIL |
| 8 | No excessive whitespace where larger targets or more content would help | WARN |

### Severity definitions

| Severity | Meaning |
|---|---|
| **FAIL** | Content missing, page blank, input unreachable, critical action hidden |
| **WARN** | Touch target borderline, minor clipping, wasted space, small text |
| **PASS** | No issues |

---

## Step 6: Decide

### A — All PASS

1. Add `{current}` to `"completed"`.
2. **If there is a next route:** set `"current"` to it, set `"attempt"` to `1`, write the updated state file. Print: `✅  {route} — all viewports pass. Advancing to {next}.` Schedule next iteration (self-pace).
3. **If this was the last route:** write the updated state file. Proceed immediately to Step 2 — the exit check will print the completion message and stop without scheduling another wakeup.

### B — Issues found, attempt ≤ 3

1. Print an issue table:

   ```
   Viewport | FAIL/WARN | Issue | Recommended fix
   ```

2. Fix every issue by editing source files under `{appDir}/{sourceDir}/`. Fix **all** issues before proceeding — do not leave any partially fixed.

3. Run the quality gates from `{appDir}` using `lintCommand` and `testCommand` from config (defaulting to `npm run lint` and `npm run test`):

   ```bash
   {lintCommand} && {testCommand}
   ```

   If either fails, fix those failures before continuing.

4. Increment `"attempt"` by 1. Write the updated state file.
5. Print: `🔧  {route} attempt {n} — fixes applied. Re-capturing to verify…`
6. Schedule next iteration (self-pace) — re-enters at Step 4 to capture and verify.

### C — Issues remain, attempt > 3

1. Print: `⚠️  {route} — could not fully resolve after 3 fix attempts. Logging and advancing.`
2. Print the full remaining issue list for manual review.
3. Set `"current"` to the next route (if this was the last route, skip to Step 2 which will trigger the exit check); set `"attempt"` to `1`.
4. Write the updated state file.
5. Schedule next iteration (self-pace).
