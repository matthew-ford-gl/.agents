---
name: retrospective
description: Post-task retrospective that extracts reusable learnings from what just happened and routes them to the right knowledge files. Distinct from /learn (which is manual) — retrospective actively reconstructs the session from artifacts and proposes specific file updates.
argument-hint: "[task name, PR URL, or bug ID]"
model: sonnet
---
You are running a post-task retrospective to capture reusable knowledge before context is lost.

Input: `$ARGUMENTS` (optional) — task name, PR URL, bug ID, or any identifier that helps locate the artifacts from the work just completed.

## What This Command Does

Reconstructs what happened from available evidence (git log, PR, discussion files, ROOT-CAUSE.md, DECISION.md, test results), identifies learnings that will help future work, and routes each one to the most specific knowledge file that owns it.

Run this after completing a significant task, fixing a non-trivial bug, or finishing any work that produced surprising findings.

---

## Step 0: Load Project Context

Before reconstructing the session, load the project-specific context:
1. Read the repository root `AGENTS.md` and any nearer `AGENTS.md` files for the paths involved.
   Treat repository instructions as mandatory.
2. If `.claude/CLAUDE.md` exists in the repo root, read it.
3. If `.context/index.md` exists, scan it for keywords matching the work's domain and load
   every matched standard, playbook, and convention file into your context.

## Step 1: Reconstruct What Happened

Gather evidence from the current session:

```bash
# Recent commits
git log --oneline -10

# Files changed
git diff --stat HEAD~1 HEAD   # or against base branch
```

Also look for:
- `*-DECISION.md` files from `/plan-task` debates
- `bugs/*/ROOT-CAUSE.md` from `/analyse-bug`
- `*-critic.md` or `*-feasibility.md` from `/review-plans`
- Any `VERIFY-FIX-VERDICT.md` from `/verify-fix`
- Test results and build output if still in context

If `$ARGUMENTS` includes a PR URL, fetch the PR description and comments.

---

## Step 2: Identify What Was Surprising

For each artifact found, extract:

1. **What was planned vs. what actually happened** — where did the implementation diverge from the plan, and why?
2. **What was harder than expected** — where did work stall, require a loop, or surface unexpected complexity?
3. **What the tests caught** — did tests fail in ways that revealed a design flaw? Did a test that was expected to pass initially fail?
4. **What a reviewer (human or agent) caught** — what did BLOCKED feedback prevent that would have shipped broken?
5. **What the root cause turned out to be** — for bugs, was the initial hypothesis wrong? What evidence changed the investigation?
6. **What would have helped** — what did you wish you had known at the start?

Discard anything that was routine, went as expected, and would not be useful to a future engineer encountering the same codebase.

---

## Step 3: Classify and Route Each Learning

Apply the routing taxonomy from `/learn` — route to the most specific applicable file:

| Bucket | Target | Use when |
|--------|--------|----------|
| `INCIDENT` | `bugs/{id}/learnings.md` | Came from a specific bug investigation |
| `FEATURE` | `docs/features/{feature}/notes.md` | About a feature's behaviour or edge cases |
| `SERVICE` | `docs/services/{service}/notes.md` | About a specific component's behaviour |
| `PROJECT` | `CLAUDE.md` (project-level) | Pipeline, conventions, or setup that applies within this repo |
| `GLOBAL` | `~/.claude/CLAUDE.md` | Tool patterns or approaches that apply across all projects |

Before proposing any write:
- Check if the learning is already documented (grep the target file)
- Confirm the learning is a fact, not a hypothesis

---

## Step 4: Propose Updates

Present each proposed update before writing:

```
[SERVICE → docs/services/payments/notes.md]
  Add: "Stripe webhook signature verification must use the raw request body,
        not the parsed JSON — parsing first causes signature mismatch"
  Evidence: commit abc1234, test failure in PaymentWebhookTest

[PROJECT → CLAUDE.md]
  Add: "Run docker-compose down -v before re-running integration tests —
        leftover volumes cause false test failures"
  Evidence: wasted ~45 mins on this during the session

[GLOBAL → ~/.claude/CLAUDE.md]
  Skip — nothing learned today applies across all projects
```

---

## Step 5: Apply Updates

For each approved update:
1. Read the target file (create it if it doesn't exist)
2. Grep for key terms to confirm no duplicate
3. Append to the most relevant section
4. Keep each entry to 1–3 sentences with a reference (commit hash, bug ID, or date)

---

## Step 6: Propose Process Improvements

After routing learnings, check if any finding suggests an improvement to the workflow itself:

- Did a reviewer catch something that the plan stage should have caught earlier? → Suggest adding a check to the orchestrator
- Did the tests miss a case that caused a production issue? → Suggest adding that test pattern to `qa-gatekeeper`'s standards
- Did a persona debate surface a concern that turned out to be the critical insight? → Note it (no file update needed, just acknowledge)
- Did the plan-task debate miss something obvious? → Suggest whether a new persona or reviewer would have caught it

Present these as suggestions, not automatic updates — the human decides whether to act on them.

---

## Step 7: Summary

```
Retrospective Complete

Learnings captured: {n}
  [INCIDENT]  {n items}
  [SERVICE]   {n items}
  [PROJECT]   {n items}
  [GLOBAL]    {n items}

Skipped (already documented): {n}
Skipped (too speculative):     {n}

Process suggestions:
  - {any workflow improvements identified}
```
