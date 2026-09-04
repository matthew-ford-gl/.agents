---
name: phased-plan-executor
description: "Executes one phase of an already-written phased remediation plan (such as one produced by report-remediation-planner) by dispatching one parallel, worktree-isolated subagent per workstream in that phase, reconciling naming and file-overlap conflicts across their reports, then stopping for human approval before any merge, push to a shared branch, or new PR. Use when asked to work a specific phase of a phased plan doc, kick off a workstream batch, run the next phase of a remediation programme, or execute (not plan) a numbered phase. Not for: producing the plan itself (use report-remediation-planner), running more than one phase in a single invocation, or merging/pushing without review."
argument-hint: "<plan file path> <phase number>"
model: opus  # cross-agent conflict reconciliation (Step 4) needs stronger judgment than routine dispatch
---

# Phased Plan Executor

Input: `$ARGUMENTS` — a phased plan file path and a phase number.

Execute exactly one phase of an already-written plan by fanning out one subagent per workstream in that phase.

**Standing boundary:** this skill never merges, never pushes to main or any shared branch, and never opens a new PR — those steps always stop for a human, regardless of how small the change looks. Every later reference to "the standing boundary" in this file means exactly this.

## Complexity contract

- If no phase number is given, or more than one phase is requested, stop and ask. Never run multiple phases in one invocation — later phases reuse names and conventions minted by earlier ones, and running them together defeats the sequencing the plan was built for.
- If the plan file has no recognizable phase/workstream structure (no phase-tagged workstreams, no per-workstream findings/remediation-shape/acceptance-criteria fields), stop and report rather than guessing structure.
- If the requested phase has zero workstreams, report that and stop — likely a typo in the phase number.

## 1. Read the plan and locate the phase

1. Read the full plan file. Don't skim — the roadmap, coverage matrix, and workstream sections must agree with each other.
2. From the roadmap and coverage matrix, list every workstream tagged with the requested phase, and every finding ID under each.
3. Reconcile: every workstream claimed for this phase should appear in both the roadmap and the coverage matrix with the same phase number. Call out any mismatch rather than silently trusting one source over the other.

Complete when the phase's full workstream list is fixed and cross-checked against two independent parts of the plan.

## 2. Check the gate before starting

1. From the plan's dependency/relationship register and roadmap, list this phase's prerequisites (which earlier phases, workstreams, or PRs must already be closed) and its own closure gate.
2. Check each prerequisite against actual repository or PR state — merged PRs, existing branches, files on disk — not against the plan's phase labels alone. A phase can be "done" on paper and still unmerged in practice.
3. If a prerequisite is unmet, stop and report exactly what's missing rather than starting the phase anyway. Do not downgrade a hard prerequisite to a soft warning just to keep moving.
4. If an earlier phase left behind a naming-conventions note (metric, event, or span names it minted, written at the end of its own Step 4 below), read it now. Every subagent dispatched in this phase must reuse those names for the same concept rather than mint new ones — this is the single most common way phases collide with each other.

Complete when the gate is confirmed open, or the run has stopped with a named, specific blocker.

## 3. Brief and dispatch one subagent per workstream

For each workstream in the phase, in one message, dispatch a subagent with `isolation: "worktree"`. Consult `subagent-dispatch` for dispatch mechanics — the four-part contract (objective, output, tools, boundaries) applies here as it does to any delegation.

**Sizing.** One workstream is not always one subagent. If a single workstream's findings span multiple independent components with no shared files between them (separate deployment units, separate apps), split that workstream into one subagent per component group instead of overloading one agent with all of it — fully independent, non-overlapping fan-outs tolerate up to about 10 agents. Keep it as one subagent when the workstream is small or its findings already share files. Either way, every subagent in the batch stays independent — none should need another's output before it can finish.

Each brief must carry, verbatim from the plan's own workstream entry:

- the workstream's finding IDs, remediation shape, code boundary, and acceptance criteria;
- any naming conventions carried over from Step 2.4;
- the per-finding branch rule below;
- the standing boundary (stated at the top of this file).

**Per-finding branch rule**, inside every subagent's brief:

- If a finding carries a linked PR: verify that PR's actual source branch via the repository host's PR-query command before touching anything — never assume the currently checked-out branch matches the PR. Check out that branch, patch in place, and push only to that PR's own branch.
- If a finding has no linked PR: branch fresh off main, implement, test against the finding's acceptance criteria, and commit. Do not push.

Each subagent's return must include: per-finding status (closed / patched / residual), any file or component it touched that another workstream in this same batch might also touch, and any new metric/event/span name it introduced. A single-workstream subagent cannot see its siblings, so it can only flag a possible overlap — it cannot resolve one. Resolution happens in Step 4.

Complete when every workstream in the phase has a dispatched subagent, and none of them have been asked to merge, push to main, or open a PR.

## 4. Wait, then reconcile

1. Wait for every subagent in the batch to return before doing anything else.
2. Build one reconciliation table: finding → status → workstream → any naming or file overlap flagged by more than one subagent.
3. Resolve naming collisions yourself. This is the one step no individual subagent could do, since each only sees its own workstream — pick one name per concept, preferring the earlier-phase convention from Step 2.4 when one exists.
4. Propose a merge order for the batch that respects the plan's own dependency register for this phase.
5. If this phase minted any new naming conventions, write them down as a short conventions note — append to the plan file or a sibling note next to it. The next phase's Step 2.4 depends on this note existing.

Complete when every finding in the phase has one status, every cross-agent conflict has one resolution, and a merge order is proposed.

## 5. Report and stop

Present, in this order: phase number and workstreams covered; per-finding status table; naming decisions made; file-overlap conflicts and their resolutions; proposed merge order; conventions carried forward for the next phase.

Then stop. The standing boundary from the top of this file applies here without exception — not even for a one-line change.

Complete when the human has the full batch summary and nothing has been merged, pushed to a shared branch, or opened as a new PR without their approval.

## Integration with sibling skills

| Counterpart | Hand-off |
|---|---|
| `report-remediation-planner` | Produces the phased plan this skill executes. Run it first if no plan exists yet. |
| `subagent-dispatch` | Dispatch mechanics for the per-workstream subagents in Step 3. |
| `resolving-merge-conflicts` | If the proposed merge order in Step 4 surfaces a real conflict once merges are attempted, use this after human approval. |
