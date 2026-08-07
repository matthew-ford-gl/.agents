---
name: verify-fix
description: Verify that a bug fix is complete — confirms the root cause is addressed, checks for partial fixes, and detects regressions introduced by the change. Run after implementing a fix but before raising a PR.
argument-hint: "<ROOT-CAUSE.md path or bug description> [--diff <diff or PR>]"
model: sonnet
---
You are verifying that a bug fix is complete and correct.

Input: `$ARGUMENTS` — path to a ROOT-CAUSE.md (from `/analyse-bug`), or a description of the bug and its fix. Optionally followed by `--diff <path or PR URL>` to provide the actual diff.

## What This Command Does

Three agents independently verify different aspects of the fix. Unlike code review (which checks quality), this checks correctness: does the fix actually solve the problem, is it complete, and has it introduced new problems?

---

## Step 1: Load Context

Read `$ARGUMENTS`. Load:
- The repository root `AGENTS.md` and any nearer `AGENTS.md` files for the affected paths.
  Treat repository instructions as mandatory.
- `.claude/CLAUDE.md` from the repo root, if it exists.
- `.context/index.md` and any matched standards/playbooks for the bug/fix domain, if present.
- The ROOT-CAUSE.md if provided (root cause, fix description, verification query)
- The diff or relevant changed files
- The test files added or modified as part of the fix
- Any existing known-bugs or incident documentation for context

Pass all loaded project context to the agents you spawn.

---

## Step 2: Run Verification (3 agents simultaneously)

Launch THREE agents in parallel, each receiving all loaded context:

**Agent 1 — Root Cause Verifier**

```
You are verifying that a bug fix addresses its stated root cause.

Given the ROOT-CAUSE.md and the diff:
1. Identify the root cause mechanism described in ROOT-CAUSE.md
2. Trace through the diff — find the specific change that addresses that mechanism
3. Verify the fix is complete: does it address all cases where the root cause could trigger,
   or only the specific case that was reported?
4. Run the verification query from ROOT-CAUSE.md against the current code — does it confirm
   the fix?
5. Check: could the same root cause trigger through a different code path not covered by the fix?

Conclude with:
- ROOT_CAUSE_ADDRESSED: YES / PARTIAL / NO
- If PARTIAL or NO: describe exactly what is still exposed
```

**Agent 2 — Gap Detector**

```
You are checking whether a bug fix is fully implemented.

Given the fix description and the diff:
1. Check every file that should have changed based on the root cause — are any missing?
2. Check the test added for the fix — does it actually prove the bug cannot recur?
   (A test that passes even without the fix is not a valid regression test)
3. Are there sibling code paths — same pattern in different files — that have the same
   bug and were not fixed?
4. Was any defensive code, validation, or error handling required but omitted?
5. Does the fix handle the edge cases named in ROOT-CAUSE.md?

Conclude with:
- FIX_COMPLETE: YES / PARTIAL / NO
- If PARTIAL or NO: list the specific gaps
```

**Agent 3 — Regression Detector**

```
You are checking whether a bug fix has introduced new problems.

Given the diff and the test suite:
1. What existing behaviour does the changed code serve beyond the bug being fixed?
2. For each changed function or method: what are its callers? Could any caller be broken
   by the change?
3. Are there tests that now pass differently (or that the diff silently changes expectations
   for) — not just new tests, but existing tests whose behaviour has shifted?
4. Does the fix change any shared state, cache, or data structure in a way that could affect
   unrelated flows?
5. Are there race conditions introduced by the fix in concurrent code paths?

Conclude with:
- REGRESSIONS_FOUND: YES / NO
- If YES: describe each regression and its severity (BREAKING / DEGRADED / LATENT)
```

**Launch all three simultaneously.**

---

## Step 3: Verdict

After all three agents complete:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FIX VERIFICATION — {bug description}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Root cause addressed:  {YES / PARTIAL / NO}
Fix complete:          {YES / PARTIAL / NO}
Regressions found:     {YES / NO}

Overall: {VERIFIED / NEEDS WORK}

Issues requiring action:
  - {each gap, partial fix, or regression}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**VERIFIED**: root cause addressed, fix complete, no regressions. Safe to raise PR.

**NEEDS WORK**: one or more agents found a problem. Present the specific issues. Do not raise a PR until the human confirms the issues are addressed or accepts the risk explicitly.
