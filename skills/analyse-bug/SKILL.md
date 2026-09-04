---
name: analyse-bug
description: "Root cause analysis pipeline for a bug. Runs structured investigation phases — intake, correlation, hypothesis ranking, evidence classification, multi-persona discussion — and writes a ROOT-CAUSE.md only when the primary hypothesis reaches live-data confirmation. Use when a bug ticket, symptom, or regression needs root-causing before a fix. Not for: greenfield feature design, or pure investigate-repo lookups with no fix intent."
argument-hint: "<bug description, ticket ID, or symptom>"
model: opus  # multi-persona debate and evidence-weighted root-cause synthesis need stronger reasoning than routine tasks
---
You are running a structured root cause analysis pipeline for a bug.

Input: `$ARGUMENTS` — a bug description, ticket or issue ID, or symptom to investigate.

## Philosophy

Never write ROOT-CAUSE.md from code reading alone. Every hypothesis must be confirmed with live data (logs, DB queries, metrics) before it becomes a conclusion. If you cannot get live data, ask for it explicitly — stop and wait rather than speculate.

---

## Phase 0: Context Loading

Before touching any code, load project context and check for existing knowledge:
- Read the repository root `AGENTS.md` and any nearer `AGENTS.md` files for the affected paths.
  Treat repository instructions as mandatory throughout the investigation.
- If `.claude/CLAUDE.md` exists in the repo root, read it.
- If `.context/index.md` exists, scan it for keywords matching the bug domain and load every
  matched standard, playbook, and convention file into your context.
- Look for any `docs/` or `bugs/` directory with documented past incidents
- Look for `known-bugs.md`, `known-issues.md`, or similar files in the affected service's directory
- Check `git log --oneline -20` to understand recent changes that may have introduced the bug

If a prior documented incident matches this symptom, confirm it applies before re-investigating from scratch.

Pass all loaded project context to any agents you spawn.

---

## Phase 1: Intake

Understand the bug fully from `$ARGUMENTS`:

Extract and record:
- **Symptom**: what the user or system experienced
- **First occurrence**: when did this start? Was there a deployment or change near that time?
- **Blast radius**: how many users/requests/records are affected?
  - Affects everyone → likely a code bug
  - Affects specific users or configs → likely a config or data bug
  - Started after a specific date → likely tied to a deployment or config change
- **Reproduction steps**: what sequence of actions triggers the bug?
- **Error messages**: exact error text, status codes, stack traces

---

## Phase 2: Correlation

Before investigating the code, correlate the symptom with observable system state:

1. Check logs for the error signature and first occurrence timestamp
2. Check if the error rate is: increasing / stable / isolated
3. Check git for deployments near the first error timestamp:
   ```bash
   git log --oneline --since="{first_error_date - 7d}" --until="{first_error_date + 1d}"
   ```
4. If a DB value is wrong: run a targeted `git log` on the file that **writes** that field, not just reads it:
   ```bash
   git log --oneline --since="{first_error_date - 14d}" -- {path/to/writer}
   ```
   A recent commit touching the write path near the first error date is a strong signal.

---

## Phase 3: Investigation

Trace the request flow from symptom back to root cause.

**Mandatory investigation rules before forming hypotheses**:

**Rule A — When a stored value is wrong (null, 0, or unexpected)**: always audit the WRITE path, not just the read path.
- Find every code location that writes the broken field
- Check for conditionals (`if flag / if enabled / if visible`) that silently skip writing it
- Check if that conditional was recently added (`git log -- {file_that_writes_field}`)

**Rule B — When a feature flag or config value is in the code path**: always query its live state. Do not assume it is the default. Read the config, env var, or DB row that controls it.

**Rule C — When the reporter says "we changed the setting but it had no effect"**: stop asking for logs. This means the write path is broken — the value is not being persisted from the UI or API. Immediately:
1. Verify the value actually changed in storage (not just in the UI)
2. If not: find the save handler and trace what conditions must be true for the field to be written
3. If yes but no effect: the read path is ignoring it — trace from the reader back to its source

**At the end of Phase 3, produce a ranked hypothesis list.** For each hypothesis:
- Describe the mechanism (what code path or config value causes the symptom)
- Assign an evidence classification (see below)
- Write the specific live-data query that would confirm or eliminate it

Save this ranked hypothesis list to `bugs/{id}/hypotheses.md` (see Output Artifacts).
This is the single artifact for hypothesis tracking — Phase 3b and 3c update it in place
rather than creating additional files.

---

## Evidence Classification (assign to every hypothesis)

| Level | Name | Definition | Max confidence before ROOT-CAUSE.md |
|-------|------|------------|--------------------------------------|
| 1 | `CODE_ONLY` | Found in code/git reading alone. No live data. | **60% — do NOT write ROOT-CAUSE.md yet** |
| 2 | `DB_CONFIRMED` | Matched against a live DB query or config value | **75%** |
| 3 | `LOG_CONFIRMED` | Matched against actual log payloads (request/response bodies, field values) | **80% — minimum to write ROOT-CAUSE.md** |
| 4 | `MULTI_SOURCE` | Confirmed by 2+ independent live sources | **95%** |

**If the primary hypothesis is `CODE_ONLY`, do NOT write ROOT-CAUSE.md. Go to Phase 3b.**

---

## Phase 3b: Evidence Request (when primary hypothesis is CODE_ONLY)

Load the template at `assets/templates/evidence-checklist.md` and fill it in, ordering
items by elimination power. Append the filled-in checklist to `bugs/{id}/hypotheses.md`
(see Output Artifacts) rather than creating a separate file.

**Stop and wait for data. Do not speculate further or write ROOT-CAUSE.md.**

---

## Phase 3c: Evidence Integration (when live data is provided)

When data is provided:
1. Re-classify hypotheses using the Evidence Classification table
2. Eliminate hypotheses ruled out by the new data
3. Upgrade confidence of confirmed hypotheses
4. If primary hypothesis reaches `LOG_CONFIRMED` (80%+) → proceed to Phase 4
5. If not → output a shorter evidence request for the remaining gap

Iterate until either:
- Primary hypothesis reaches 80%+ confidence with live data, OR
- The reporter explicitly says "publish anyway"

---

## Phase 4: Multi-Persona Discussion

With confirmed hypotheses, run a brief structured debate from four lenses (inline — no subagents needed):

**Guardian lens**: How many users are affected, how long, what is the severity? Is this a data integrity issue?
**Craftsman lens**: Is this a code bug or a structural gap? What test would have caught this?
**Director lens**: Is the fix a config change, a code change, or a process change? What is the risk of the fix itself?
**Historian lens**: Has this pattern appeared before? Is this a REPEAT BUG, PATTERN RECURRENCE, or NEW BUG?

The discussion should be concise — its job is to validate the fix direction, not re-investigate.

---

## Phase 5: ROOT-CAUSE.md

Only write this when the primary hypothesis is `LOG_CONFIRMED` or `MULTI_SOURCE`.

Load the template at `assets/templates/root-cause-template.md`, fill it in, and save it
to `bugs/{id}/ROOT-CAUSE.md`.

---

## Phase 6: Fix Handoff — STOP

Present the ROOT-CAUSE.md summary and offer to proceed to implementation.

Load the template at `assets/templates/stop-box.md`, fill it in, and print it verbatim.

Wait for human response before proceeding.

- **Stop**: report artifact locations and exit.
- **Fix**: proceed to Phase 7.

---

## Phase 7: Orchestrator Handoff

Invoke the Orchestrator using the Agent tool with subagent type `orchestrator`.

Pass the following in the prompt:

```
PRE-APPROVED PLAN — skip step 3 and the human approval STOP.

This is a bug fix. The root cause has been confirmed and the human has accepted the fix
direction. Treat the following as the approved plan and begin at step 4 (fan out
plan-stage reviewers), proceeding through to PR.

BUG: {original $ARGUMENTS}

ROOT CAUSE:
{full contents of ROOT-CAUSE.md}

FIX PLAN:
Implement the fix described in the ROOT-CAUSE.md Fix section.
Add the regression test described in the ROOT-CAUSE.md Regression Test section.
Verify using the query in the ROOT-CAUSE.md Verification section.
```

---

## Phase 7b: Verify the Handoff Report — do not take it on faith

Before chaining automatically into Phase 8, check the Orchestrator's final report (this
applies whether it ran in the foreground or as a background subagent via `run_subagent`, collected with `read_subagent`)
against its own contract (step 10 of `orchestrator/AGENT.md`).

The report must explicitly state, at minimum:
- Every plan-stage reviewer that ran and its verdict — including `security-analyst` by name.
- Every diff-stage reviewer that ran and its verdict.
- Any reviewer that could not run (e.g. unrecognized profile) and why.
- CI/test gate status and the PR URL.

This check matters more here than in `/plan-task`: Phases 8 and 9 below run automatically
with no human in between, so a gap in the Orchestrator's report would otherwise propagate
silently through verification and the retrospective without anyone ever seeing it.

If any of the above is missing or vague, **do not assume it was fine and do not proceed to
Phase 8 automatically.** If the Orchestrator ran as a resumable session, send a follow-up
asking it to report the missing verdicts explicitly. If the session is no longer resumable,
stop, tell the human plainly what is missing, and re-run the missing review(s) directly
(e.g. spawn `security-analyst` against the actual PR diff) before continuing.

Only proceed to Phase 8 once the reviewer verdicts are accounted for.

---

## Phase 8: Fix Verification (automatic)

Once the Orchestrator completes and its report has been verified per Phase 7b, run
`/verify-fix` automatically — do not ask the human.

Invoke it as a subagent or inline using the `verify-fix` command, passing:
- The ROOT-CAUSE.md
- The diff produced by the Orchestrator

If the result is **VERIFIED**: proceed to Phase 9.

If the result is **NEEDS WORK**: present the specific issues and STOP. The fix is incomplete
or has introduced regressions — the human must decide whether to loop the Orchestrator
again or address the gaps manually before the PR is merged.

---

## Phase 9: Retrospective (automatic)

Once the fix is verified (or if stopping at Phase 6 without implementing), run
`/retrospective` automatically — do not ask the human.

Pass the bug ID or description as context so it can locate the investigation artifacts
(ROOT-CAUSE.md, hypotheses.md, the diff, and the verify-fix verdict).

---

## Output Artifacts

Save to `bugs/{id}/` (or create a timestamped folder if no ID):
- `intake.md` — symptom, blast radius, reproduction steps (written after Phase 1)
- `hypotheses.md` — ranked hypothesis list with evidence classification, written after Phase 3;
  updated in place with the evidence checklist (Phase 3b) and re-classified hypotheses
  (Phase 3c) as new data arrives
- `ROOT-CAUSE.md` — written only after the primary hypothesis reaches `LOG_CONFIRMED` or `MULTI_SOURCE`
