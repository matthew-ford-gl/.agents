---
name: architecture-audit
description: "Audit a codebase or named subsystem for high-value architectural improvements, prioritising proven change hotspots, module depth, ownership, coupling, test seams, and evolution risk. Produces evidence-backed candidates without implementing them. Use when a human asks for an architecture review, wants to know where structural risk or high-leverage refactors are, or wants a subsystem surveyed for coupling, ownership, or test-seam problems. Not for: line-level SOLID/naming/complexity checks across a diff or path (use quality-audit), synthesising an existing multi-finding report into a remediation plan (use report-remediation-planner), or full planning-to-execution with domain modelling and ticket decomposition (use plan-task)."
argument-hint: "<optional subsystem, pain point, or path>"
model: opus  # synthesizes four parallel specialists' findings into a ranked architectural judgment call, not a lookup or transcription task
---

# Architecture Audit

Scope: $ARGUMENTS

This is a survey, not an implementation workflow. Recommend changes only where current evidence shows recurring friction or material risk.

## 1. Load constraints and choose scope

Read repository instructions, domain context, relevant ADRs, architecture documentation, and tests. If the human supplied a subsystem or pain point, use it. Otherwise inspect a meaningful span of Git history to identify frequently changed areas and let those hotspots set the scope.

Do not re-litigate an accepted ADR without concrete evidence that its recorded trade-off has materially changed.

Complete this phase when the scope is fixed to a named subsystem, pain point, or evidence-backed hotspot, and any binding ADRs or constraints are identified.

## 2. Investigate in parallel

Launch these agents concurrently and pass actual relevant file content plus loaded context:

- `architect` — boundaries, responsibility, data ownership, coupling, interface depth, and evolution risk
- `historian` — change hotspots, recurring fixes, reverted approaches, and direct matches to documented failures
- `quality-auditor` — complexity and design smells that make the hotspot hard to understand or change
- `qa-gatekeeper` — current public test seams, missing behavioural coverage, and architecture that obstructs reliable testing

Use each identifier as the `subagent_type` (or platform equivalent) and launch all four in the same turn. Follow the `subagent-dispatch` skill for dispatch mechanics, platform mapping, and the fallback to use when a named profile is unavailable.

Require every finding to cite files, lines, history, tests, or ADR evidence. Absence of evidence is not a finding.

Complete this phase when all four agents have returned, and every finding carries a file, line, history, test, or ADR citation.

## 3. Test each candidate

For each proposed improvement, establish:

- **Observed friction** — repeated changes, scattered knowledge, leaky ownership, shallow interfaces, duplicated policy, or an unstable seam
- **Production reachability** — the affected path is live rather than dead or superseded
- **Depth test** — the proposed module hides materially more complexity than its interface exposes
- **Deletion test** — removing the current abstraction would concentrate complexity rather than merely move names around
- **Locality and leverage** — the change puts related knowledge together and lets one interface govern multiple behaviours
- **Test impact** — the public seam becomes clearer or important behaviour becomes easier to exercise
- **ADR compatibility** — aligned, neutral, or a justified request to revisit a recorded decision

Reject speculative abstractions supported by only one hypothetical future use. Two real consumers may justify a shared seam; one does not by itself.

Complete this phase when every candidate has been checked against all seven tests and any candidate resting on a single hypothetical consumer is discarded.

## 4. Rank and report

Present no more than five candidates, ordered by evidence-adjusted value. For each include:

- Recommendation strength: `Strong`, `Worth exploring`, or `Speculative`
- Files and production path
- Evidence and observed cost
- Current responsibility and ownership problem
- Proposed architectural direction, without pretending an untested interface is final
- Expected locality, leverage, testability, and operational benefits
- Migration and rollback concerns
- Conflicting ADRs or unresolved questions
- Smallest safe validation experiment

End with a top recommendation and a `No change` option. If the evidence does not justify architectural work, say so explicitly rather than manufacturing candidates.

Do not edit production code, create ADRs, or open tickets. Offer `/plan-task` for the selected candidate; that workflow can model the domain, record architectural decisions, and decompose accepted work into tickets.
