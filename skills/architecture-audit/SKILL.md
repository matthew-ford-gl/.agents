---
name: architecture-audit
description: Audit a codebase or named subsystem for high-value architectural improvements, prioritising proven change hotspots, module depth, ownership, coupling, test seams, and evolution risk. Produces evidence-backed candidates without implementing them.
argument-hint: "<optional subsystem, pain point, or path>"
model: opus
---

# Architecture Audit

Scope: $ARGUMENTS

This is a survey, not an implementation workflow. Recommend changes only where current evidence shows recurring friction or material risk.

## 1. Load constraints and choose scope

Read repository instructions, domain context, relevant ADRs, architecture documentation, and tests. If the human supplied a subsystem or pain point, use it. Otherwise inspect a meaningful span of Git history to identify frequently changed areas and let those hotspots set the scope.

Do not re-litigate an accepted ADR without concrete evidence that its recorded trade-off has materially changed.

## 2. Investigate in parallel

Launch these agents concurrently and pass actual relevant file content plus loaded context:

- `architect` — boundaries, responsibility, data ownership, coupling, interface depth, and evolution risk
- `historian` — change hotspots, recurring fixes, reverted approaches, and direct matches to documented failures
- `quality-auditor` — complexity and design smells that make the hotspot hard to understand or change
- `qa-gatekeeper` — current public test seams, missing behavioural coverage, and architecture that obstructs reliable testing

Use each identifier as the Claude `subagent_type` or Devin `run_subagent` profile. Launch all four
before collecting results. If a custom profile is unavailable, load its AGENT.md with
project-before-user precedence and pass the full persona to an unnamed/general Task in Claude
Code or `profile: "subagent_general"` in Devin CLI.

Require every finding to cite files, lines, history, tests, or ADR evidence. Absence of evidence is not a finding.

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
