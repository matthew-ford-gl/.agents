---
name: review-plans
description: Run two adversarial agents against an implementation plan — one trying to find fatal flaws, one checking feasibility against the actual codebase. Use before committing to implementation when you want a hostile review, not a constructive one.
argument-hint: "<path to implementation plan or task description>"
model: sonnet
---
You are running an adversarial review of an implementation plan.

Input: `$ARGUMENTS` — path to an implementation plan file, or a description of the proposed approach.

## What This Command Does

Two agents independently attack the plan from different angles. Unlike the debate personas in `/plan-task` which are constructive, these agents are deliberately hostile — their job is to find reasons the plan will fail, not to help it succeed.

---

## Step 1: Load the Plan

Read `$ARGUMENTS`. If it is a file path, read it fully. If it is a description, treat it as the plan.

Also read the relevant source files mentioned in the plan so both agents have codebase context.

---

## Step 2: Run Adversarial Review (2 agents simultaneously)

Launch TWO agents in parallel:

**Agent 1 — Plan Critic**

Prompt:
```
You are a plan critic. Your job is to find every reason this implementation plan will fail.
Be adversarial, not constructive. Do not suggest improvements — find fatal flaws.

Look for:
- Assumptions the plan makes that are not verified against the actual codebase
- Missing steps that will cause the implementation to stall or break
- Logical gaps: steps that assume a prior step succeeded without handling failure
- Scope creep hidden in the plan — things described as "simple" that are not
- Missing error paths: what happens when each step goes wrong?
- Ordering problems: dependencies between steps that the plan gets wrong
- Tests that cannot work as described (wrong layer, wrong scope, missing setup)
- Rollback described as "just revert" when that is not actually safe

For each flaw found, state:
1. What the flaw is
2. What will specifically go wrong as a result
3. How severe: FATAL (blocks completion) / SIGNIFICANT (causes rework) / MINOR (degrades quality)

End with: APPROVED (no fatal flaws) or BLOCKED (one or more fatal flaws found).
```

Save output to `{plan-slug}-critic.md`.

**Agent 2 — Feasibility Checker**

Prompt:
```
You are a feasibility checker. Your job is to verify whether this implementation plan
is achievable given the actual state of the codebase. Read the relevant source files
and check every assumption the plan makes.

Look for:
- Functions, classes, or APIs the plan calls that do not exist or have different signatures
- Files the plan proposes to modify that do not exist or have different structure
- Patterns the plan assumes are already in place (DI containers, base classes, test helpers)
  that are absent
- External dependencies the plan assumes are available (libraries, services, environment vars)
- Test infrastructure the plan assumes exists (factories, fixtures, mocks)
- Permissions or configurations required but not mentioned

For each infeasibility found, state:
1. What the plan assumes
2. What is actually in the codebase
3. Effort to close the gap: TRIVIAL / MODERATE / SIGNIFICANT

End with: APPROVED (plan is feasible as written) or BLOCKED (one or more blocking gaps found).
```

Save output to `{plan-slug}-feasibility.md`.

**Launch both simultaneously.**

---

## Step 3: Consolidate and Report

After both agents complete:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ADVERSARIAL REVIEW — {plan name}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Plan Critic:      {APPROVED / BLOCKED}
Feasibility:      {APPROVED / BLOCKED}

Fatal flaws ({n}):
  - {each FATAL item from the critic}

Blocking feasibility gaps ({n}):
  - {each BLOCKED item from the feasibility checker}

Significant concerns ({n}):
  - {SIGNIFICANT items from both agents}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

If either returns BLOCKED, the plan needs revision before implementation. Present the specific blocking items and stop — do not proceed to implementation.

If both APPROVED, the plan is adversarially clear. Note any significant concerns for awareness and stop — the human decides whether to proceed.
