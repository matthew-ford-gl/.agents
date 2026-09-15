---
name: quality-audit
description: "Runs a parallel code-quality audit and writes an executor-ready phased remediation plan with a complete finding ledger, actionable workstreams, dependency gates, and stable-ID coverage accounting. Use when asked to audit code quality, review SOLID/complexity/smells, run a quality pass, or identify and sequence quality improvements across a path, diff, or repository. Not for: architecture design review, security review, PR requirements compliance, or implementing fixes."
argument-hint: "[path | glob | diff | (empty = whole repo)] [output file]"
model: opus
---

# Quality Audit

Task: `$ARGUMENTS`

Audit a target in parallel, consolidate every finding once, and write one self-contained plan that `phased-plan-executor` can execute directly. Read-only: do not modify production code, implement fixes, or open tickets.

## Complexity contract

- Stop if the target resolves to no files or the `quality-auditor` agent cannot be resolved.
- For a small target, one auditor pass is the fast path. Otherwise chunk by coherent module and run up to eight passes per wave.
- Keep the complete finding ledger in the main workflow. Subagents may inspect chunks, but no subagent may own final extraction, IDs, coverage, or plan synthesis.
- If output would be too large for the console, write the complete artifact to a file rather than abbreviating findings. Never replace rows with ranges such as `QA-001–QA-163`.
- If planning cannot be completed, preserve the full audit and report the exact failed gate. Do not emit a partial plan as executor-ready.

Complete when the cost, fallback, and non-applicability branches are resolved.

## 1. Resolve instructions, agent, and target

1. Read repository instructions and the code-quality standard from `.context/index.md` or `.context/standards/code-quality.md` when present.
2. Resolve `quality-auditor` using the first existing path: `.devin/agents/quality-auditor/AGENT.md`, `.claude/agents/quality-auditor.md`, `~/.agents/agents/quality-auditor/AGENT.md`, `~/.claude/agents/quality-auditor.md`. Read it; stop with the searched paths if none exists.
3. Parse the target:
   - `diff`: use files changed from the current branch's merge base; fall back to staged files when appropriate.
   - path or glob: resolve it and expand directories while respecting `.gitignore`.
   - empty: prefer `git ls-files`; otherwise glob from the repository root.
4. Exclude generated, vendored, binary, build-output, lock, and VCS paths. Record every included file in a scan manifest.
5. Resolve the output path. Use the requested path or default to `CODE-QUALITY-REMEDIATION.md` in the repository root.

Complete when the repository boundary, standards, auditor definition, non-empty scan manifest, and output path are fixed.

## 2. Chunk and audit every file

Group related files together, targeting about 30 KB or 15 files per chunk. Give an oversized file its own chunk. Run at most eight chunks concurrently per wave.

Dispatch one `quality-auditor` pass per chunk using the host's native subagent mechanism. Give each pass:

- the chunk ID and exact file manifest;
- the files' contents, not paths alone;
- the loaded code-quality standard;
- the requirement to inspect all four dimensions for every assigned file and return its per-dimension zero counts.

If no parallel mechanism exists, run the same passes sequentially and disclose that fact. After each wave, record one completion row per chunk: manifest, pass status, finding count, and all four dimension totals.

Complete when every manifest file belongs to exactly one completed chunk and every chunk reports all four dimensions.

## 3. Build the authoritative finding ledger

Consolidate chunk results centrally. Merge only findings that identify the same defect and remediation scope; retain source-chunk aliases. Assign each distinct finding one stable ID in deterministic severity/path/line order: `QA-001`, `QA-002`, and so on.

Create one ledger row per stable ID with these fields:

| Field | Required content |
|---|---|
| ID | Full `QA-*` ID; never a range or abbreviated list |
| Title | Concise defect name |
| Severity | Critical, Major, or Minor |
| Dimension / rule | Source dimension and rule |
| Location | File and line or smallest supplied range |
| Evidence | Source-faithful description of the observed code |
| Impact / failure mode | Why the issue matters |
| Proposed remediation | Concrete change shape, kept separate from evidence |
| Source chunk | Chunk ID and any merged aliases |
| Verification state | `Audited finding`, `Probable duplicate of <ID>`, or an explicit uncertainty |

Reconcile all of these independently:

- scan manifest files = union of chunk manifests;
- sum of chunk raw findings = distinct ledger rows + merged duplicate aliases;
- severity totals = ledger row count;
- dimension totals = ledger row count;
- declared finding total = number of explicit full-ID ledger rows.

Complete when every raw finding is represented by a ledger row or named duplicate alias and all counts reconcile.

## 4. Form executor-sized workstreams

Assign every ledger ID to exactly one primary workstream. Group by shared remediation mechanism and overlapping code boundary, not by severity alone. Split work that cannot be implemented, reviewed, or tested coherently; combine findings only when one bounded change and acceptance suite can close them together.

For each workstream provide:

- stable workstream ID and title;
- phase number;
- complete primary finding-ID list and duplicate aliases;
- common thread and evidence;
- objective and concrete remediation shape;
- exact code boundary: files/components expected to change, or `To validate` with a validation step;
- prerequisites, dependents, conflicts, and parallel-safety notes;
- acceptance criteria individually referenced as `AC-<workstream>-<n>`, each mapped to one or more finding IDs;
- required tests and validation commands, using repository-supported commands only;
- rollout, observability, rollback, unresolved questions, and assumptions where applicable;
- closure gate that can be checked from repository or PR state.

Use phases only as needed: `0 Verify`, `1 Foundations`, `2 Highest-risk fixes`, `3 Sibling rollout`, `4 Remaining fixes`, `5 Closure validation`. Foundations do not outrank urgent containment. State which workstreams can run in parallel.

Complete when every finding has one primary workstream, every workstream is independently actionable, and every finding maps to at least one acceptance criterion.

## 5. Write the executor contract

Write the output file in this exact top-level order:

1. `# Code Quality Remediation Plan`
2. `## Audit metadata` — target, revision, date, standards, files scanned, chunks, and declared finding total.
3. `## Executive summary`
4. `## Scan coverage` — full file manifest or an unambiguous generated manifest section, plus chunk completion table and per-dimension counts.
5. `## Finding ledger` — one explicit row per full stable ID with all Step 3 fields.
6. `## Programme roadmap` — one row per workstream with phase, findings, prerequisites, parallel track, and closure gate.
7. `## Dependency and relationship register` — duplicate aliases, overlaps, dependencies, conflicts, and dispositions.
8. `## Workstream plans` — one complete subsection per workstream with every Step 4 field.
9. `## Coverage matrix` — one explicit row per stable ID with severity, primary workstream, phase, disposition, and acceptance-criterion references.
10. `## Validation backlog`
11. `## Accounting` — reconciled totals by severity, dimension, phase, and workstream.
12. `## Executor readiness` — the gate results below and either `READY` or `NOT READY: <exact failures>`.

The roadmap, workstream plans, and coverage matrix are independent views and must agree. Do not rely on console text or another report for omitted details.

Complete when the file is self-contained and all required sections exist in order.

## 6. Run the executor-readiness gate

Before claiming `READY`, check the written file rather than working memory:

- declared finding total = explicit ledger row count = explicit coverage-matrix row count;
- every ID is unique, complete, and appears in exactly one primary workstream;
- every roadmap workstream has one matching full workstream section and the same phase;
- every coverage row references existing acceptance criteria in its primary workstream;
- every workstream has a code boundary, remediation shape, prerequisites, tests, and closure gate;
- duplicate aliases remain traceable without double-counting implementation scope;
- phase totals and workstream totals equal the declared finding total;
- scan coverage proves every target file and every audit dimension was processed;
- no section says `see above`, uses an ID range, or substitutes a summary for row-level accounting.

Repair the artifact and rerun the gate until it passes. If a source limitation prevents repair, mark `NOT READY` and list the exact missing IDs or fields.

Complete when every check is recorded as passing in `## Executor readiness`, or the artifact clearly identifies why execution is blocked.

## 7. Report

Tell the human the output path, finding/workstream/phase counts, readiness status, and any limitations. For zero findings, still write metadata, scan coverage, empty ledger/roadmap/matrix, reconciled zero accounting, and `READY — no execution required`. For one finding, create one workstream and one executable phase rather than using a separate format.

Complete when the human can pass the written file and either a phase number or `all` directly to
`phased-plan-executor` without another planning step.

## Integration with sibling skills

| Counterpart | Hand-off |
|---|---|
| `phased-plan-executor` | Executes one numbered phase or an approved multi-PR programme from this skill's `READY` output file. |
| `investigate-repo` | Validates uncertain reachability or repository claims before a gated phase runs. |
| `subagent-dispatch` | Supplies host-specific dispatch mechanics for chunk auditors. |
