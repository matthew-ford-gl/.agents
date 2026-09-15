---
name: phased-plan-executor
description: "Executes an executor-ready phased remediation plan in one of two controlled modes: one worktree-isolated phase that stops before integration, or an approved multi-phase programme that uses disposable workstream contexts and opens bounded PRs. Use when asked to execute a numbered quality-audit phase, run the next remediation phase, or work an entire READY quality-audit report across multiple PRs. Not for: producing a plan, merging PRs, or general feature delivery."
argument-hint: "<plan file path> <phase number | all>"
model: opus # cross-workstream reconciliation and programme dependency decisions need strong judgment
---
# Phased Plan Executor

Input: `$ARGUMENTS` — one executor-ready plan and either a phase number or `all`.

## Modes and authority

- **PHASE mode** (`<phase number>`): execute exactly one phase in isolated worktrees, reconcile it,
  then stop. Never merge, push to a shared branch, or open a PR.
- **PROGRAMME mode** (`all`): present one programme approval gate, then autonomously implement
  dependency-safe workstream batches, normally push task branches, and open bounded PRs. Never merge,
  force-push, perform destructive actions, or change the accepted programme scope.

Do not infer PROGRAMME mode from vague wording; it grants broader side effects and requires explicit
`all` plus approval.

## Complexity contract

- Proceed only when `Executor readiness` says `READY` and the ledger, roadmap, workstream sections,
  coverage matrix, and accounting reconcile. Stop with exact missing or duplicate IDs otherwise.
- Use one fresh worker context per workstream. Keep the coordinator context to programme state and
  compact results; never accumulate source, complete diffs, full logs, or reviewer transcripts.
- In PROGRAMME mode, default to at most four concurrent workers. Serialize overlapping files,
  components, tests, migrations, deployment units, and hard dependencies.
- Open one PR per independently reviewable workstream. Combine workstreams only when they share one
  remediation mechanism, code boundary, validation suite, and rollback unit.
- Stop a workstream when the same failure fingerprint survives two materially distinct fixes. Other
  independent work may continue when the plan permits it.

Complete when the mode, authority, cost bounds, and fallback behaviour are explicit.

## 1. Read and validate the plan

1. Read the full plan, including readiness, accounting, roadmap, relationship register, coverage
   matrix, and every selected workstream section.
2. Reconcile the declared finding total with explicit ledger and coverage rows. Confirm every finding
   belongs to exactly one primary workstream and every workstream has a phase, remediation shape,
   code boundary, acceptance criteria, tests, prerequisites, and closure gate.
3. Verify prerequisites against actual repository and PR state, not plan labels alone.
4. Load naming-convention notes from completed earlier phases. Workers must reuse existing names for
   the same concept.

In PHASE mode, select every workstream in the requested phase. In PROGRAMME mode, retain the complete
dependency graph but load detailed workstream content only when selecting its batch.

Complete when plan accounting agrees and selected work is explicit, or the run has stopped with a
named contract failure.

## 2. Establish state and approval

For PHASE mode, continue directly to Step 3 under its standing boundary.

For PROGRAMME mode:

1. Resolve `context_root` in order: `CONTEXT_STORAGE_PATH`; repository
   `.devin/agent-context.json`; `~/.config/devin/agent-context.json`; writable host temporary
   directory; ignored repository `.tmp`. Resolve and probe the selected path.
2. Create or load `<context_root>/<safe-repo-name>/quality-remediation-<plan-id>.json`. Store only
   plan revision, workstream/finding status, prerequisites, PRs, commits, gate verdicts, conventions,
   and compact blockers. Store no source, diffs, logs, credentials, or reviewer transcripts.
3. Present phases, dependency order, PR grouping, maximum concurrency, forced serialization, local
   validation/review gates, authorized side effects, and escalation conditions. STOP for approval.

Approval covers every in-scope workstream and later phase whose prerequisites become satisfied. Ask
again only when requirements, architecture, user-visible behaviour, risk acceptance, rollout policy,
or PR grouping must change; when safety, permissions, credentials, or destructive action are
involved; or when the repeated-fingerprint rule is exhausted.

Complete when PHASE mode is bounded, or PROGRAMME mode has an accepted programme and durable compact
checkpoint.

## 3. Select one dependency-safe batch

PHASE mode selects all mutually independent workstreams in its requested phase and stops if a hard
prerequisite is unmet. PROGRAMME mode rebuilds state from the plan, checkpoint, Git, and PR host on
each iteration, then selects pending workstreams whose prerequisites are satisfied.

Exclude workstreams that overlap files, components, tests, migrations, or deployment units with
another selected item. In PROGRAMME mode cap the batch at four workers. If no item is selectable,
report completion or the exact open-PR prerequisite, dependency cycle, or blocker. Never wait or poll
remote state in the current context.

Complete when one bounded independent batch is selected or the programme has a terminal state.

## 4. Dispatch disposable workstream workers

Dispatch one fresh, worktree-isolated worker per selected workstream using the host-native mechanism
and `subagent-dispatch` guidance. Give each worker only:

- complete finding rows, remediation shape, code boundary, acceptance criteria, tests, closure gate,
  and prerequisite evidence for its workstream;
- earlier naming conventions;
- absolute paths to applicable repository instructions, standards, and source files;
- a private temporary context directory;
- the authority boundary for the selected mode.

Require every worker to:

1. Verify findings against current reachable code; return stale or false findings with evidence.
2. Implement one bounded vertical correction at a time and run targeted tests.
3. Derive the complete pre-push suite from repository instructions and live CI definitions.
4. Run that suite on the final tree. Retain only failure-bearing excerpts capped at 400 lines and
   40 KiB per check.
5. Run `qa-gatekeeper` in implementation mode and the applicable Orchestrator diff-stage reviewers.
   Pass artifact paths rather than inline contents.
6. Correct actionable failures and MUST-FIX findings in the smallest implicated scope, rerun affected
   checks/reviewers, then finish with one full final suite.
7. Stop only for a human-decision, safety, permission, or external blocker, or when one fingerprint
   survives two materially distinct fixes.
8. Commit the green result. In PROGRAMME mode normally push and open its approved PR; in PHASE mode
   do not push or open a PR.

Each worker returns only finding status, changed paths, commit, optional PR URL, gate verdicts, new
conventions, blocker fingerprint, and temporary artifact paths. Never reuse its context for another
workstream.

Complete when every selected worker returns one compact result within its mode's authority.

## 5. Reconcile and persist

1. Build a finding-to-status table and resolve cross-worker naming or file collisions. Prefer an
   earlier convention and record one merge order where integration is later required.
2. In PHASE mode, append any new conventions beside the plan for the next phase.
3. In PROGRAMME mode, update the compact checkpoint with `PR OPEN`, `CLOSED AS STALE`, or `BLOCKED`,
   direct evidence, commit, PR, gate verdicts, and conventions.
4. Shed worker source, diffs, logs, and reviewer transcripts from active context. Retain diagnostics
   by path only.
5. Never poll or merge open PRs. Continue to Step 3 only while another batch is independent of them;
   otherwise stop with exact merge prerequisites for the next batch.

Complete when every selected finding has a disposition, conventions and dependencies are durable,
and a fresh invocation can resume without conversation history.

## 6. Report and stop

In PHASE mode report phase/workstreams, per-finding status, naming decisions, overlap resolutions,
proposed merge order, and conventions for the next phase. Confirm nothing was pushed or opened.

In PROGRAMME mode report plan revision; completed, open, pending, stale, and blocked workstreams;
finding coverage; PR URLs and gate verdicts; conventions; next unblocked batch or merge prerequisite;
and checkpoint path. Never report completion while a finding lacks an explicit disposition.

Complete when the human can review each result independently and no merge or unauthorized side
effect has occurred.

## Integration with sibling skills

| Counterpart | Hand-off |
|---|---|
| `quality-audit` | Produces the `READY` plan consumed in either mode. |
| `subagent-dispatch` | Supplies host-specific isolated dispatch mechanics. |
| `resolving-merge-conflicts` | Resolves conflicts after separately approved integration begins. |
| `land-pr` | Handles evidenced remote-only CI or review feedback for an already-open PR. |
