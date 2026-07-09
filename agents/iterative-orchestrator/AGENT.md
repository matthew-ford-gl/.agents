---
name: iterative-orchestrator
description: Autonomous per-route UI fix loop. Captures screenshots, analyses visual and UX issues, plans and implements fixes through specialist reviewers, re-captures to verify, and raises a single PR when all routes are clean.
model: opus
---

# Iterative Orchestrator Workflow

A self-contained variant of the Orchestrator that drives a per-route iteration loop and
a visual gate, running the **full quality pipeline inline** for each route's fix instead
of delegating it. Same sub-agents, same step shape as the Orchestrator, reorganised so a
single agent owns capture -> vision analysis -> plan+review -> implement -> build/test ->
qa-gatekeeper -> code-review -> commit -> visual re-verify, looped over routes, one PR
at the end.

Use this when you want the loop and the quality pipeline owned by one agent. The current
Orchestrator is untouched; the cost is that the quality-step logic now lives in two files
and must be kept in sync by hand.

Defaults to Tier 1 devices only.

```
/iterative-orchestrator               # start / resume from state file
/iterative-orchestrator payment       # jump straight to the payment route
/iterative-orchestrator all           # wipe state and restart from login
```

---

## Agents

Plan-stage reviewers (run in parallel against the proposed plan):
- senior-engineer
- qa-gatekeeper
- security-analyst

Diff-stage reviewers (run against the actual diff after tests pass):
- qa-gatekeeper (implementation-review mode)
- code-reviewer

## Path resolution

For each agent, check Test-Path ".claude/agents/<name>.md". If true use that file, else use "~/.claude/agents/<name>.md".

## Loop safety

The loop is autonomous: there are no human STOP points. Wherever the Orchestrator would
STOP for approval or on BLOCKED, this workflow instead records a **failed attempt** for the
current route and continues. Internal correction loops (build/lint/test -> qa-gatekeeper ->
code-reviewer) are bounded at **3 cycles** per attempt; exceeding the bound ends the attempt.
A route that exhausts 5 attempts is logged and skipped (path C).

---

## State file

**Path:** `src/web/epos-launcher/.ux-fix-state.json`

```json
{
  "completed": [],
  "current":   "login",
  "attempt":   1,
  "branch":    "ux/auto-review-20260625-1430"
}
```

- `completed` — routes confirmed clean; never remove entries.
- `current`   — route being processed this iteration.
- `attempt`   — fix attempts on the current route; reset to `1` on advance.
- `branch`    — the single branch all fixes commit onto for this run.

Route order:

```
login → mainbar → payment → engineers →
reservations → transaction-history → release-notes
```

---

## Run setup (once per run) — mirrors Orchestrator steps 0 and 2

Run these once when a run starts (fresh state, or `all`), not per route.

**S0. Sync context.** Run: `pwsh -Command "Sync-AgentContext -TargetRepo (Get-Location)"`.
Pulls the latest standards and playbooks from the central clone. If it fails, warn and
continue -- the existing `.context/` files are still usable.

**S1. Parse arguments and init state.**
- `all` → delete `.ux-fix-state.json` if present, then proceed as fresh.
- route name → write/overwrite state so `"current"` is that route and `"attempt"` is `1`;
  keep `"completed"` and `"branch"` if the file existed, else `"completed"` = `[]`.
- empty → read existing state, or create defaults.

**S2. Branch.** On a fresh run, create the run branch and store it in state:

```powershell
$branch = "ux/auto-review-$(Get-Date -Format 'yyyyMMdd-HHmm')"
git checkout -b $branch
```

On resume, checkout `"branch"` from state. Every route's fixes commit onto this one branch.

**S3. Load standards.** If `.context/index.md` exists, scan it for keywords matching the
UI / UX / frontend domain. Load every matched standard and playbook file into context now
and keep it for the whole run -- it is passed to all sub-agents on every route.

---

## Loop (per iteration)

Read the state file at the start of every iteration.

### L1 — Exit check — mirrors Orchestrator step 9

If `completed` contains all 7 routes, raise the single PR for the run:

- Detect remote type. Ensure the branch is pushed.
- Commit any pending changes; skip the commit if the tree is clean (commits already landed per route).
- Raise the PR. Description must contain:
  - Summary paragraph (this was an automated Tier 1 visual-UX pass)
  - Per-route before/after issue counts and viewports covered
  - Main files changed and why
  - Review & Testing Checklist for a human
  - Notes: screenshots committed, any route that hit path C, test execution status
- Print: `✅  All routes clean. Iterative review complete. PR raised: <url>`
- Stop. Do not schedule another wakeup.

### L2 — Pre-capture: MockSiteHub

`reservations` and `transaction-history` need MockSiteHub on port 3001 or they render blank.

```powershell
$up = (Test-NetConnection localhost -Port 3001 -WarningAction SilentlyContinue).TcpTestSucceeded
if (-not $up) {
    Start-Process npm -ArgumentList 'run','dev' `
        -WorkingDirectory (Resolve-Path 'src/web/mock-sitehub') -NoNewWindow
    Start-Sleep -Seconds 4
}
```

### L3 — Capture — current route only

```powershell
$env:UX_TIER = "1"; $env:UX_ROUTES = "<current>"; npx playwright test --project=visual-capture
```

Screenshots land in `src/web/epos-launcher/screenshots/<route>--<viewport>.png`.

### L4 — Analyse

Read **every** PNG matching `screenshots/<current>--*.png` with the Read tool before
drawing conclusions.

#### Expected populated content — FAIL if absent

| Route | Expected content |
|---|---|
| `login` | PIN pad (0–9, ⌫, ✕), "Sign On" button |
| `mainbar` | Product tile grid; check panel with Lager, Ale, Burger; course headers; non-zero total |
| `payment` | Cash numpad with £5/£10/£20/£50 presets; Card, Room, Split Bill, Voucher tiles all enabled |
| `engineers` | 6-digit code pad, "Verify" button (PIN `123456` is seeded) |
| `reservations` | Cards for John Smith 18:00 and Jane Doe 19:30 |
| `transaction-history` | Transaction rows with amounts and clerk names; **no** WAN-unavailable banner |
| `release-notes` | Version cards v2.5.0 and v2.4.1 with bullet lists |

#### Checklist (every screenshot)

| # | Check | Severity |
|---|---|---|
| 1 | Populated content present | FAIL |
| 2 | Every interactive element ≥ 44 px in both dimensions | WARN |
| 3 | Body text readable at arm's length (≥ 14 px equivalent) | WARN |
| 4 | Nothing clipped at viewport edges | WARN |
| 5 | Keypad / numpad comfortable for the orientation | WARN |
| 6 | Layout adapts between portrait and landscape | WARN |
| 7 | Critical actions (Pay, Sign On, Verify, Back) visible without scrolling | FAIL |
| 8 | No excessive whitespace where larger targets / more content would help | WARN |

Severity: **FAIL** = content missing / blank / input unreachable / critical action hidden.
**WARN** = borderline target, minor clipping, wasted space, small text. **PASS** = clean.

### L5 — Decide

**A — All PASS.** Add `<current>` to `completed`; set `current` to next route; `attempt` = 1;
write state. Print `✅  <route> — all Tier 1 viewports pass. Advancing to <next>.` Schedule next.

**B — Issues found, attempt ≤ 5.** Print the issue table
(`Viewport | FAIL/WARN | Issue | Recommended fix`), then run the **Per-route fix workflow**
below. On its completion:
- It committed a fix → **re-capture (L3) and re-analyse (L4)** the same route. This is the
  visual gate. Clean → path A. Still failing → `attempt`++, write state, loop back to B.
- It ended in a failed attempt (BLOCKED, loop bound exceeded, or build/test undefined) →
  print the reason, do not re-capture, `attempt`++, write state, loop back to B.
Print `🔧  <route> attempt <n> — fixes applied. Re-capturing to verify…` and schedule next.

**C — attempt > 5.** Print `⚠️  <route> — could not fully resolve after 5 attempts. Logging and advancing.`
Print the remaining issues and any BLOCKED reasons. Set `current` to next route; `attempt` = 1;
write state. Schedule next.

---

## Per-route fix workflow — mirrors Orchestrator steps 1, 3–8

Runs inside L5 path B against the current route. No human STOP; the run-setup context (S3)
is passed to every sub-agent.

**F1 (step 1).** Read the route's source: `src/pages/<Route>Page.tsx`,
`src/components/TopNavBar.tsx`, `src/index.css`. Understand scope.

**F3 (step 3).** Derive the plan directly from the L4 issue table -- this is the approved
scope, no approval STOP:
- target files: the three above
- constraints: 44px minimum touch targets (both dimensions); use the custom Tailwind variants
  below, do not hand-roll media queries; portrait and landscape layouts must diverge;
  critical actions stay visible without scrolling

Custom Tailwind variants (defined in `src/index.css`):

| Variant | Breakpoint |
|---|---|
| `wide:` | `@media (min-width: 568px)` |
| `tablet:` | `@media (min-width: 768px)` |
| `desktop:` | `@media (min-width: 1024px)` |
| `landscape:` | `@media (orientation: landscape) and (max-height: 500px)` |
| `tablet-landscape:` | `@media (orientation: landscape) and (min-height: 501px) and (min-width: 768px)` |

**F4 (step 4).** Fan out the three plan-stage reviewers as parallel Tasks, passing the plan,
actual file contents (not paths), and the loaded standards.

**F5 (step 5).** Consolidate feedback. Any BLOCKED → end this attempt as a failed attempt
(return to L5 path B). Do not STOP.

**F6 (step 6).** Implement the fixes, addressing all reviewer feedback.

**F7a (step 7a). Reproduce the full CI gate locally.** The CI file is the
single source of truth; never consult a copied list of gates. Resolve in order:

1. If CLAUDE.md names a single local-CI command (e.g. `npm run verify`,
   `make verify`), run that — it is assumed to call the same commands CI calls.
2. Otherwise, locate the CI definition — `.github/workflows/*.yml`,
   `azure-pipelines.yml`, `.gitlab-ci.yml`, `bitbucket-pipelines.yml`. Read
   every job. Extract and run every shell command in CI order. This covers all
   gate types implicitly: build, lint, format, dead-code / unused-dependency
   checks, type-checks, unit tests, E2E — whatever CI actually runs.

If a gate cannot run locally (e.g. E2E needs services), start the services if
you can; otherwise record which gate was not run and why in the final PR notes —
never silently skip. Fix any failure and re-run before continuing.

If no CI file exists and CLAUDE.md names no command, end this attempt as a
failed attempt with reason "no CI definition found".

**F7b (step 7b).** Generate the diff (`git diff` against the base branch). Collect all test
files touched or created. Run `qa-gatekeeper` in implementation-review mode, passing the plan,
the diff, all test file contents, and the loaded standards, with this assessment context:

> This change originates from a visual / touch-UX review and its rendered correctness is
> verified by Playwright visual re-capture in this same loop. Assess whether the actual diff
> warrants adding or extending tests: layout / styling-only changes typically do not, but any
> change to component logic, state, or computed values does. Existing tests must still pass.

If BLOCKED, address the gaps and loop back to F7a, subject to the 3-cycle bound. Exceeding the
bound ends this attempt as a failed attempt.

**F8 (step 8).** Run `code-reviewer` as a Task, passing the plan, the diff, and the loaded
standards. If it returns BLOCKED or lists MUST-FIX items, address them and loop back to F7a,
subject to the 3-cycle bound. Should-fix and nit items are recorded for the final PR notes
but do not block.

**F-commit.** Commit the fix onto the run branch with a message naming the route and attempt.
Do not push per commit (push happens once at L1) unless your remote requires it. Return to L5
so the visual gate can re-verify.
