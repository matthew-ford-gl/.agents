# plan-task Templates

Exact templates for `plan-task` phases that produce structured artifacts. SKILL.md tells you
when to load each section below — load only the one you need for the phase you are on.

## Phase C — Implementation Plan template

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

## Decision Records
{Whether this is an ADR candidate, the decision that may need recording, and why; otherwise `None`}
```

## Phase H — Acceptance Gate presentation template

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PLANNING COMPLETE — {task name}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Verdict: {PROCEED | PROCEED WITH MODIFICATIONS | DEFER | REJECT}

{If PROCEED WITH MODIFICATIONS, list each modification as a bullet}

Key risks identified:
  {2–3 most significant risks from the debate}

Test strategy: {n} tests across {layers} — see {task-slug}-DECISION.md for full table
Tickets: {n} tracer-bullet tickets — see {task-slug}-tickets.md
ADR: {required and decision summary | not required}

Deferred: {anything explicitly out of scope}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Options:
  [A] Accept — hand off to Orchestrator to implement
  [R] Re-discuss — describe what you want reconsidered
  [S] Stop here — take the plan and implement separately
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## Phase J — Orchestrator handoff prompt template

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

TRACER-BULLET TICKETS:
{full contents of {task-slug}-tickets.md}

DOMAIN MODEL:
{domain-modeller output and exact updated files, or `No active model change`}

ARCHITECTURE DECISION RECORD:
{new ADR path and full contents, or `Not required`}
```
