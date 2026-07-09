---
name: plan-task
description: Full planning-to-execution pipeline. Runs 3 parallel analysts, a 6-persona structured debate, and a binding decision. Presents the decision for acceptance, then hands off to the Orchestrator to implement. One command from problem to PR.
argument-hint: "<task description or task file path>"
model: opus
---
You are orchestrating the full planning and execution pipeline for a development task.

Input: `$ARGUMENTS` — a task description, a path to a task file, or the name/ID of a task in the current project.

## What This Command Does

Runs three parallel planning analysts → synthesises an initial implementation plan → runs a 6-persona structured debate (2 rounds) → Director writes a binding DECISION.md → plan is refined → you accept or re-discuss → Orchestrator implements, reviews, and raises a PR.

---

## Phase A: Understand the Task

Read `$ARGUMENTS` to extract:
- What needs to be built or changed
- Acceptance criteria (explicit or inferred)
- Affected files, services, or components
- Any constraints (deadline, backward compatibility, must-not-break)

---

## Phase B: Parallel Analysis (3 agents simultaneously)

Launch THREE agents in parallel:

**Agent 1 — Risk & Compatibility Analyst**: Analyse backward compatibility and change risk.
- What existing behaviour could break? What consumers depend on the changed interface?
- What migration or deprecation path is needed? What is the rollback approach?
- Output: `{task-slug}-compatibility.md` — risk level (LOW/MEDIUM/HIGH), breaking changes, rollback path.

**Agent 2 — Test Strategy Analyst**: Design the test-first strategy.
- Map every acceptance criterion to at least one named, classified, TDD-ordered test.
- Output: `{task-slug}-test-strategy.md` — Test-First Strategy table.

**Agent 3 — User & Business Impact Analyst**: Assess user-facing and business impact.
- What changes for the user? Blast radius if wrong? Leading monitoring signals post-deploy?
- Output: `{task-slug}-impact.md` — impact scope, user segments, monitoring signals.

**Launch all three simultaneously.**

---

## Phase C: Initial Implementation Plan (inline)

Synthesise the three analyst outputs into an implementation plan. Do not spawn a subagent.

```markdown
# Implementation Plan — {task name}

## Summary
{2–3 sentences on what this change does and why}

## Approach
{Step-by-step implementation sequence}

## Test-First Order
{Reproduce the Test Strategy Analyst's table here verbatim}

## Risks
{Top 3 risks and mitigations from the Risk Analyst}

## Monitoring
{Post-deploy signals from the Impact Analyst}
```

Save to `{task-slug}-implementation.md`.

---

## Phase D: Discussion Round 1 — Initial Positions (6 agents simultaneously)

Launch SIX discussion personas in parallel, each receiving the full implementation plan
and all three analyst outputs:

- **Guardian** (subagent: `guardian`) → Save to `{task-slug}-R1-guardian.md`
- **Craftsman** (subagent: `craftsman`) → Save to `{task-slug}-R1-craftsman.md`
- **Pragmatist** (subagent: `pragmatist`) → Save to `{task-slug}-R1-pragmatist.md`
- **Architect** (subagent: `architect`) → Save to `{task-slug}-R1-architect.md`
- **User Advocate** (subagent: `user-advocate`) → Save to `{task-slug}-R1-user-advocate.md`
- **Historian** (subagent: `historian`) → Save to `{task-slug}-R1-historian.md`

**Launch all 6 simultaneously.**

---

## Phase E: Discussion Round 2 — Challenges (6 agents simultaneously)

Each agent receives the original plan AND all six Round 1 positions. Task: produce a
Round 2 response — challenge, support, or refine based on the full picture.

Save to `{task-slug}-R2-{persona}.md` for each.

**Launch all 6 simultaneously.**

---

## Phase F: Binding Decision (Director, inline)

Execute the Director binding decision inline — do not spawn a subagent.

1. Read `~/.claude/agents/director.md` for the DECISION.md schema
2. All 12 discussion outputs (R1 + R2) are already in context
3. Synthesise into a binding DECISION.md:
   - Verdict: `PROCEED` | `PROCEED WITH MODIFICATIONS` | `DEFER` | `REJECT`
   - Rationale referencing specific debate evidence
   - Modifications required (if any)
   - Test Strategy table (verbatim from the Craftsman's final table)
   - Rollout plan
   - Success criteria
   - Rollback conditions
   - Deferred items
4. Save to `{task-slug}-DECISION.md`

---

## Phase G: Refine the Plan (inline)

Apply the DECISION.md modifications to the implementation plan:
1. Incorporate all required modifications
2. Replace the test strategy section with the Craftsman's final Test-First Strategy table
3. Add rollout and rollback conditions from the decision
4. Overwrite `{task-slug}-implementation.md` with the refined plan

---

## Phase H: Acceptance Gate — STOP

Present the decision clearly to the human:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PLANNING COMPLETE — {task name}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Verdict: {PROCEED | PROCEED WITH MODIFICATIONS | DEFER | REJECT}

{If PROCEED WITH MODIFICATIONS, list each modification as a bullet}

Key risks identified:
  {2–3 most significant risks from the debate}

Test strategy: {n} tests across {layers} — see {task-slug}-DECISION.md for full table

Deferred: {anything explicitly out of scope}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Options:
  [A] Accept — hand off to Orchestrator to implement
  [R] Re-discuss — describe what you want reconsidered
  [S] Stop here — take the plan and implement separately
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

Wait for human response before proceeding.

- **Re-discuss**: note the concern, stop. The human can run `/review-plans {task-slug}-implementation.md` for a quick adversarial check, or describe what to reconsider.
- **Stop**: report artifact locations and exit.
- **Accept**: proceed to Phase I.

---

## Phase I: Orchestrator Handoff

Invoke the Orchestrator using the Agent tool with subagent type `orchestrator`.

Pass the following in the prompt:

```
PRE-APPROVED PLAN — skip step 3 and the human approval STOP.

The following plan has been through a full 6-persona debate and has been accepted by the
human. Treat it as the output of your step 3. Begin at step 4 (fan out plan-stage reviewers)
and proceed through to PR.

TASK:
{original $ARGUMENTS}

REFINED IMPLEMENTATION PLAN:
{full contents of {task-slug}-implementation.md}

BINDING DECISION:
{full contents of {task-slug}-DECISION.md}

COMPATIBILITY ANALYSIS:
{full contents of {task-slug}-compatibility.md}

TEST STRATEGY:
{full contents of {task-slug}-test-strategy.md}

IMPACT ANALYSIS:
{full contents of {task-slug}-impact.md}
```
