---
name: report-remediation-planner
description: "Synthesises multi-finding reports into a complete, prioritised remediation plan with common workstreams, dependency order, ownership boundaries, duplicate handling, and stable-ID coverage accounting. Use when asked to analyse an audit, scan, assessment, or report containing multiple findings; group issues by common threads; create a programme of fixes; or decide what to tackle first. Not for: implementing fixes, investigating one bug, validating findings against a repository, or summarising a report without a remediation plan."
argument-hint: "<report path, pasted findings, or report URL>"
model: opus
---

# Report Remediation Planner

Input: `$ARGUMENTS`

Turn a report containing multiple findings into an auditable programme of work. Plan only; do not edit production code, open tickets, or claim repository facts that were not verified.

## Complexity contract

- If the input has fewer than two distinct findings, stop and handle it as a normal single-issue task instead of using this workflow.
- For up to 20 findings, work inline. For a larger report, isolate extraction or independent sections with the host's subagent mechanism when available, then reconcile all results centrally.
- If the source cannot be read or findings cannot be identified reliably, ask for the missing report or clarification rather than inferring content.
- If repository access is absent, produce a report-backed plan and label code ownership, reachability, effort, and implementation details as validation questions.

## 1. Resolve scope and source truth

1. Read project instructions when a repository is in scope.
2. Resolve the input as a file, URL, or inline text and read the complete report, including appendices and existing remediation notes.
3. Record the source revision/date, stated scope, severity scheme, and whether the report contains proposed fixes, linked changes, disputed findings, or confidence labels.
4. Treat report assertions as reported claims, not independently verified repository facts.

Complete when the source boundary and evidence status are explicit.

## 2. Build the finding ledger

Parse every finding into a ledger with these fields:

| Field | Rule |
|---|---|
| Stable ID | Preserve the report's ID. If absent, assign `R-001`, `R-002`, etc. without replacing source numbering. |
| Title | Keep a concise source-faithful title. |
| Severity and confidence | Preserve source values; write `Unstated` when absent. |
| Category | Preserve source categories without treating them as the final grouping. |
| Locations or component | Record only supplied locations; otherwise `Unknown`. |
| Impact and failure mode | Extract the harmed outcome and how it fails. |
| Proposed remediation | Preserve source proposals separately from your synthesis. |
| Verification state | `Report claim`, `Linked fix to verify`, `Disputed`, `Unverified`, or another source-supported state. |

Reconcile the parsed count against every source summary. Explain discrepancies; do not silently trust either count. For very large reports, show a compact ledger or put the full ledger in a requested output file, but retain it during analysis.

Complete when every source finding has one ledger row and count discrepancies are resolved or called out.

## 3. Resolve duplicates and relationships

Compare findings by affected behavior, location, cause, and required change. Record relationships without deleting ledger rows:

- **Probable duplicate** — the same defect and remediation scope; nominate one canonical item and retain all aliases.
- **Overlap** — shared implementation work but independently closable impacts or acceptance criteria.
- **Dependency** — one remediation enables or blocks another.
- **Sibling pattern** — the same defect class in separate components that may share a standard or helper.
- **Conflict** — proposed fixes or requirements are incompatible and need a decision.

Do not call similar symptoms duplicates when they require separate production changes or validation. Put uncertain relationships in the validation backlog.

Complete when every suspected duplicate or cross-finding relationship has an explicit disposition.

## 4. Form implementation workstreams

Assign every finding to exactly one **primary workstream**. Add secondary relationships where useful, but never use them to inflate coverage.

Group by shared remediation mechanism and change boundary, considering:

1. common root cause or policy;
2. shared abstraction, component, owner, or deployment unit;
3. reusable tests, dashboards, migration, or rollout;
4. independent closability and blast radius.

Do not merely reproduce severity levels, scanner categories, or teams. Split a broad theme when changes cannot be reviewed, deployed, or verified coherently. Merge narrow themes when one shared fix and acceptance suite closes them together.

For each workstream specify:

- primary finding IDs and duplicate aliases;
- common thread and report-backed evidence;
- objective and concrete remediation shape;
- likely code/component and accountable owner boundary, or `To validate`;
- prerequisites, dependents, and conflicts;
- acceptance criteria mapped to the included findings;
- validation, rollout, observability, and rollback considerations;
- unresolved questions and assumptions.

Complete when all ledger rows have exactly one primary workstream and each workstream is independently actionable.

## 5. Prioritise and sequence

Prioritise by evidence-adjusted risk, not source severity alone. Consider:

- active credential, privacy, safety, financial, integrity, or compliance exposure;
- misleading success signals and silent loss before ordinary visibility gaps;
- reach, likelihood, confidence, and user impact;
- containment value and time sensitivity;
- foundational fixes that close or enable many findings;
- dependency order, blast radius, reversibility, and validation cost;
- already-fixed, dead, duplicate, or uncertain claims that need verification before scheduling.

Use these phases when applicable:

0. **Verify and contain** — unverified severe claims, sensitive exposure, linked fixes, dead-code or reachability questions.
1. **Define foundations** — shared contracts, policies, instrumentation, test harnesses, or migration prerequisites.
2. **Fix highest-risk paths** — confirmed harmful behavior and misleading outcomes.
3. **Roll out sibling patterns** — repeat the proven fix across bounded components.
4. **Complete lower-risk gaps** — remaining independently valuable findings.
5. **Validate closure** — regression tests, operational evidence, rescan, and ledger reconciliation.

Foundations do not automatically outrank urgent containment. Show which work can run in parallel and which must wait. Use relative size or uncertainty only when evidence supports it; do not invent dates.

Complete when every workstream has a phase, rationale, prerequisites, and closure gate.

## 6. Run the coverage gate

Before reporting, verify mechanically where possible and otherwise check explicitly:

- source finding count = ledger row count;
- every complete stable ID appears in the coverage matrix; never abbreviate IDs in the auditable coverage artifact;
- every ledger row has exactly one primary workstream;
- duplicate aliases remain accounted for but are not double-counted as implementation scope;
- every workstream has finding-mapped acceptance criteria;
- severity/confidence changes are explained rather than silently rewritten;
- assumptions and repository-validation questions are separate from report-backed facts;
- the phase totals reconcile to the full ledger.

If any check fails, repair the plan before presenting it. Never state “all findings covered” without showing auditable accounting.

Complete when every gate passes or the report lists the exact unresolved reconciliation error.

## 7. Report

Use this order:

1. **Executive summary** — scope, counts, top risks, and recommended first moves.
2. **Evidence boundary** — what came from the report and what still needs repository or operational validation.
3. **Programme roadmap** — phases, workstreams, dependencies, parallel tracks, and closure gates.
4. **Workstream plans** — the fields required in Step 4.
5. **Duplicate and relationship register** — canonical IDs, aliases, overlaps, dependencies, and conflicts.
6. **Coverage matrix** — one row per stable ID with severity, primary workstream, phase, disposition, and acceptance-criterion reference.
7. **Validation backlog** — ranked questions that can change priority, scope, or ownership.
8. **Accounting** — reconciled totals by severity, phase, and workstream.

Keep executive sections concise while preserving row-level accounting. If the human requested a file, write the plan there; otherwise print it. Offer repository validation or ticket decomposition as a separate next step rather than performing it implicitly.

Complete when a reader can trace every source finding to one planned workstream, phase, acceptance criterion, and closure decision.
