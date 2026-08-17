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

## Phase 0: Load Project Context

Before interpreting the task, load the project-specific context so the whole pipeline
uses the right branch rules, validation gates, and domain standards:

1. Read the repository root `AGENTS.md` and any nearer `AGENTS.md` files for the paths you
   will touch. Treat repository instructions as mandatory throughout planning and execution.
2. If `.claude/CLAUDE.md` exists in the repo root, read it.
3. If `.context/index.md` exists, scan it for keywords matching the task domain and load
   every matched standard, playbook, and convention file into your context.

Pass all loaded context to every agent you spawn in later phases.

---

## Phase A: Understand the Task

Read `$ARGUMENTS` to extract:
- What needs to be built or changed
- Acceptance criteria (explicit or inferred)
- Affected files, services, or components
- Any constraints (deadline, backward compatibility, must-not-break)

---

## Spawning mechanism

Detect which runtime you are in and use its native mechanism for parallel agents —
"Task"/"subagent" naming below is descriptive, not a literal tool name in every host.

- **Claude Code**: spawn each agent as a `Task` tool call with `subagent_type` set to the
  named persona.
- **Devin CLI**: spawn each agent with the `run_subagent` tool, `profile: "<name>"`,
  `is_background: true` for every agent launched in the same phase, then collect each with
  `read_subagent` (`block: true`) once all have been launched in that phase.
  - **Profile fallback**: if a named profile is rejected as unrecognized (i.e. the agent
    has an AGENT.md but no matching Devin CLI built-in profile), retry the same agent
    using `profile: "subagent_general"` instead. Read the agent's AGENT.md file (using the
    standard path resolution) and pass its full content as the `task` prompt, prefixed with
    the original instructions you would have given. This ensures the agent still runs with
    the correct persona — only the runtime profile differs.
  - **Halt on failure**: if an agent fails to start even after the fallback attempt, STOP
    and tell the human which agent(s) could not run and why. Do not continue with a partial
    set — a missing discussion persona degrades the quality of the debate.
- **Other hosts**: use whatever native parallel-subagent primitive is available.

## Phase B: Parallel Analysis (3 agents simultaneously)

Launch THREE agents in parallel, using the Spawning mechanism above:

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

Launch SIX discussion personas in parallel, using the Spawning mechanism above, each
receiving the full implementation plan and all three analyst outputs:

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

1. Resolve the Director's file by checking, in order, and using the first that exists:
   `.devin/agents/director/AGENT.md` → `.claude/agents/director.md` →
   `~/.agents/agents/director/AGENT.md` → `~/.claude/agents/director.md`. Read it for the DECISION.md schema
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

Invoke the Orchestrator using the Spawning mechanism above, with profile/subagent type
`orchestrator`.

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

---

## Phase J: Verify the Handoff Report — do not take it on faith

When the Orchestrator returns (this applies whether it ran in the foreground or as a
background subagent via `run_subagent` and was collected with `read_subagent`), check its final report against the Orchestrator's
own contract (step 10 of `orchestrator/AGENT.md`) before presenting anything to the human.

The report must explicitly state, at minimum:
- Every plan-stage reviewer that ran and its verdict — including `security-analyst` by name.
- Every diff-stage reviewer that ran and its verdict.
- Any reviewer that could not run (e.g. unrecognized profile) and why.
- CI/test gate status and the PR URL.

If any of the above is missing or vague (e.g. a generic "all checks passed" with no
per-reviewer breakdown), **do not assume it was fine and do not silently fill the gap
yourself.** If the Orchestrator ran as a resumable session, send a follow-up asking it to
report the missing verdicts explicitly. If the session is no longer resumable, say so plainly
to the human and re-run the missing review(s) directly (e.g. spawn `security-analyst` against
the actual PR diff) rather than presenting the plan as fully verified.

Only proceed to reporting results to the human once the reviewer verdicts are accounted for.
