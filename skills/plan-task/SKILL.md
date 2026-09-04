---
name: plan-task
description: "Orchestrates the full planning-to-execution pipeline — active domain modelling, 3 parallel analysts, a 6-persona debate, a binding Director decision, ADR capture, and tracer-bullet ticket decomposition — before handing off to Orchestrator for implementation and PR. Use when a task needs full strategic vetting before code changes, e.g. cross-cutting features, architecturally significant changes, or anything where an unexamined approach is costly to get wrong. Not for: single-file fixes, typo/copy changes, or mechanical well-understood work — invoke `orchestrator` directly for those."
argument-hint: "<task description or task file path>"
model: opus
---
You are orchestrating the full planning and execution pipeline for a development task.

Input: `$ARGUMENTS` — a task description, a path to a task file, or the name/ID of a task in the current project.

## What This Command Does

Loads and sharpens the domain model when the task changes domain meaning → runs three parallel planning analysts → synthesises an initial implementation plan → runs a 6-persona structured debate (2 rounds) → Director writes a binding DECISION.md → refines the plan and decomposes it into tracer-bullet tickets → you accept or re-discuss → drafts any required ADR → Orchestrator implements, reviews, and raises a PR.

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

Derive `{task-slug}` once as a stable lowercase kebab-case summary of the task and reuse it for every artifact.

Read `$ARGUMENTS` to extract:
- What needs to be built or changed
- Acceptance criteria (explicit or inferred)
- Affected files, services, or components
- Any constraints (deadline, backward compatibility, must-not-break)
- Whether the task introduces or changes domain terms, identities, invariants, lifecycle rules,
  ownership, persisted meaning, or bounded-context boundaries → `RUN_DOMAIN_MODELLER`
- Whether the likely decision adds a component, external integration, protocol/data shape,
  deployment topology, or deliberate departure from an established pattern → `ADR_CANDIDATE`

If `RUN_DOMAIN_MODELLER` is set, launch `domain-modeller` through the Spawning mechanism
before planning. Pass the task and all loaded context, and ask it to challenge the changed
model with discriminating scenarios. Capture its complete required output as
`{task-slug}-domain-model.md` and load every knowledge file it updated. It may update an
established glossary or decision record as its contract permits. If it needs
domain-owner clarification, STOP and obtain it before Phase B. Pass its full output and any
updated domain files to every later agent. If the task only uses existing vocabulary without
changing the model, do not launch it.

Record `ADR_CANDIDATE` as provisional. The Director determines whether the accepted decision
actually requires an ADR; do not draft one before the acceptance gate.

---

## Spawning mechanism

**Agent path resolution** (referenced later in this skill too): for any agent `<name>`,
resolve its file by checking, in order, and using the first that exists:
`.devin/agents/<name>/AGENT.md` → `.claude/agents/<name>.md` →
`~/.agents/agents/<name>/AGENT.md` → `~/.claude/agents/<name>.md`.

For runtime detection and how to launch parallel agents (Claude Code `Task` calls, Devin
CLI `run_subagent` with profile-fallback and halt-on-failure, or another host's native
primitive), resolve `orchestrator`'s file with the pattern above and follow its own
"Spawning mechanism" section rather than a restatement here. If the host exposes the
`subagent-dispatch` skill, its dispatch guidance applies equally to every parallel-launch
step below.

The one addition specific to this pipeline: the three Phase B analysts have no AGENT.md, so
launch them as an unnamed/general Task (Claude Code) or with `profile: "subagent_general"`
(Devin CLI) rather than a named `subagent_type`/profile. Named discussion personas (guardian,
craftsman, pragmatist, architect, user-advocate, historian, director) use their own name.

## Phase B: Parallel Analysis (3 agents simultaneously)

Launch THREE generic agents in parallel, using the runtime branch in the Spawning mechanism
above: unnamed/general Tasks in Claude Code and `profile: "subagent_general"` in Devin CLI.
These are task-scoped analyst prompts, not named custom personas and do not require AGENT.md files:

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
Load `references/templates.md` (section "Phase C — Implementation Plan template") for the
exact structure and fill it from the three analyst outputs.

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

1. Resolve the Director's file using the agent path-resolution pattern in the "Spawning
   mechanism" section above, substituting `director` for `<name>`. Read it for the
   DECISION.md schema.
2. All 12 discussion outputs (R1 + R2) are already in context
3. Apply the Director's complete decision framework exactly as its own AGENT.md defines it —
   including its binding Safety Veto rule and decision-making framework. This skill executes
   that framework inline instead of spawning a Director subagent; it does not re-derive,
   downgrade, or override any part of it.
4. Synthesise into a binding DECISION.md:
   - Verdict: `PROCEED` | `PROCEED WITH MODIFICATIONS` | `DEFER` | `REJECT`
   - Rationale referencing specific debate evidence
   - Modifications required (if any)
   - Test Strategy table (verbatim from the Craftsman's final table)
   - Rollout plan
   - Success criteria
   - Rollback conditions
   - Deferred items
   - Architecture Decision Record: `Required: YES` or `Required: NO`, with the specific durable decision and rationale when `YES`
5. Save to `{task-slug}-DECISION.md`

---

## Phase G: Refine the Plan (inline)

Apply the DECISION.md modifications to the implementation plan:
1. Incorporate all required modifications
2. Replace the test strategy section with the Craftsman's final Test-First Strategy table
3. Add rollout and rollback conditions from the decision
4. Overwrite `{task-slug}-implementation.md` with the refined plan

### Decompose into tracer-bullet tickets

Write `{task-slug}-tickets.md` from the refined plan. Each ticket must deliver one vertically
integrated, independently verifiable increment rather than a horizontal layer. Include:

- Ticket title and user- or operator-visible outcome
- Acceptance criteria covered
- Public test seam and red-green order
- Expected files or subsystem, without prescribing unsupported implementation details
- Blocking ticket IDs; use `none` when independent
- Rollback or migration constraint when applicable
- Definition of done with a runnable verification result

Order tickets as a dependency graph and identify the first tracer bullet. Every implementation
step and acceptance criterion must map to at least one ticket, with no duplicated ownership.
Keep deferred work out of the active graph under a separate `Deferred` heading. Do not publish
tickets to an external tracker before human acceptance.

---

## Phase H: Acceptance Gate — STOP

Load `references/templates.md` (section "Phase H — Acceptance Gate presentation template"),
fill it in, and present the decision clearly to the human.

Wait for human response before proceeding.

- **Re-discuss**: note the concern, stop. The human can run `/review-plans {task-slug}-implementation.md` for a quick adversarial check, or describe what to reconsider.
- **Stop**: report artifact locations and exit.
- **Accept**: proceed to Phase I.

---

## Phase I: Record the Accepted Architectural Decision

If DECISION.md says `Required: YES` under `Architecture Decision Record`, use the host's
Skill mechanism to invoke `adr-drafter`; if the host cannot invoke skills from a skill, resolve
its SKILL.md using project-before-user precedence and follow it inline. Pass the accepted
decision, alternatives and trade-offs from the debate, affected code and contracts, and any
superseded ADR. The human's acceptance authorises drafting the new ADR but not silently
rewriting an existing one. If the drafter identifies unresolved facts that would require
inventing part of the decision, STOP and ask the human.

If DECISION.md says `Required: NO` under `Architecture Decision Record`, do not invoke the skill. Domain glossary and decision
files already updated by `domain-modeller` remain inputs to implementation but are not a
substitute for an ADR when the Director required one.

---

## Phase J: Orchestrator Handoff

Invoke the Orchestrator using the Spawning mechanism above, with profile/subagent type
`orchestrator`.

Load `references/templates.md` (section "Phase J — Orchestrator handoff prompt template"),
fill in every placeholder from the artifacts produced in earlier phases, and pass the result
as the prompt.

The Orchestrator must execute tickets in dependency order and invoke the `tdd` skill for each
implementation slice. Ticket boundaries guide sequencing but do not permit separate PRs unless
the accepted plan explicitly requires them.

---

## Phase K: Verify the Handoff Report — do not take it on faith

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
