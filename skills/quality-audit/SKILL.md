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
- For a small target, one auditor pass is the fast path. Otherwise use the persistent session harness and run up to eight passes per wave until every chunk is accepted.
- Persist manifests, worker returns, reconciliation state, and the final plan under the artifact root; keep bulky worker output out of the main context.
- Keep final extraction, stable IDs, coverage, and plan synthesis in the orchestrator. Subagents inspect only their assigned chunks and return self-contained results.
- Never stop merely because the audit requires many chunks or waves. If the host interrupts a run, preserve the session as resumable work rather than manufacturing a `NOT READY` remediation plan from uninspected files.
- If planning cannot be completed because of an actual source or worker failure, preserve the session and report the exact blocker. Do not emit a partial plan as executor-ready.

Complete when the cost, fallback, and non-applicability branches are resolved.

## 1. Resolve instructions, agent, and target

1. Read repository instructions and the code-quality standard from `.context/index.md` or `.context/standards/code-quality.md` when present.
2. Resolve `quality-auditor` using the first existing path: `.devin/agents/quality-auditor/AGENT.md`, `.claude/agents/quality-auditor.md`, `~/.agents/agents/quality-auditor/AGENT.md`, `~/.claude/agents/quality-auditor.md`. Read it; stop with the searched paths if none exists.
3. Parse the target:
   - `diff`: use files changed from the current branch's merge base; fall back to staged files when appropriate.
   - path or glob: resolve it and expand directories while respecting `.gitignore`.
   - empty: prefer `git ls-files`; otherwise glob from the repository root.
4. Exclude generated, vendored, binary, build-output, lock, and VCS paths. Record every included repository-relative path in a JSON scan manifest.
5. Resolve the artifact root from `DEVIN_ARTIFACTS_DIR` when set, otherwise `~/artifacts`. Store this audit beneath `<artifact-root>/quality-audit/`; never put session state in the audited repository.
6. Create or resume the session with `python <skill-dir>/scripts/audit_session.py init --repo <repo> --target <target> --revision <revision> --standard <standard> --manifest <manifest> [--artifact-root <root>] [--session <stable-name>]`. Let the script generate `<target-slug>-<short-revision>-<UTC timestamp>` unless an established session name exists. Reuse a named session only when its input fingerprint matches.
7. Use `<session>/CODE-QUALITY-REMEDIATION.md` as the output path. Treat `<session>/state.json` as authoritative orchestration state, `<session>/results/` as accepted worker evidence, and `<session>/retries/` as rejected evidence.

Complete when the repository boundary, standards, auditor definition, non-empty scan manifest, artifact root, and matching persistent session are fixed.

## 2. Chunk, validate, audit, and reconcile

### 2a. Build and validate chunks

The session harness deterministically groups the sorted manifest with a **hard cap of 15 files and 30 KB of source per chunk**. An oversized single file gets its own disclosed chunk. Read `<session>/state.json` and verify every initial chunk meets both limits or is a single-file exception before dispatch.

Use the persisted chunk IDs and exact manifests; do not rebuild or renumber chunks in conversational memory.

### 2b. Dispatch auditors

Run `python <skill-dir>/scripts/audit_session.py next-wave --session <session> --limit 8` and dispatch exactly the returned pending chunks concurrently using the host's native subagent mechanism. Give each pass:

- the session and chunk ID plus exact file manifest;
- the files' contents, not paths alone;
- the loaded code-quality standard;
- the requirement to inspect all four dimensions for every assigned file, return per-dimension zero counts, and echo back the complete list of files actually inspected.

Write each complete return to a temporary file, then record it before starting another wave. If no parallel mechanism exists, run the passes sequentially. Absence of parallelism changes throughput, not audit completeness.

### 2c. Post-wave reconciliation

For every returned chunk, run `python <skill-dir>/scripts/audit_session.py record --session <session> --chunk <chunk-id> --result <return-file>`. The harness checks the exact ordered file echo, all four dimension summaries, and `INCOMPLETE`; it stores accepted evidence under `results/`, stores rejected evidence under `retries/`, and halves rejected multi-file chunks into new pending child chunks.

After recording the wave, run `python <skill-dir>/scripts/audit_session.py status --session <session>`. Continue requesting and dispatching waves while pending chunks remain. A rejected single-file chunk becomes a `blocked` session because it cannot be split further; report that concrete worker failure rather than calling the incomplete audit a remediation plan.

Do not proceed to Step 3 until status is `ready-for-synthesis`. An interruption or context boundary leaves the state resumable: the next invocation reads the session and continues with `next-wave`; it does not regenerate completed work.

Complete when every manifest file belongs to exactly one accepted leaf chunk, every accepted result matches its dispatched manifest and reports all four dimensions, and the persisted status is `ready-for-synthesis`.

## 3. Build the authoritative finding ledger

Read every accepted worker artifact from `<session>/results/` and consolidate centrally; do not rely on remembered returns. Merge only findings that identify the same defect and remediation scope; retain source-chunk aliases. Assign each distinct finding one stable ID in deterministic severity/path/line order: `QA-001`, `QA-002`, and so on.

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
2. `## Audit metadata` — session path, target, revision, date, standards, files scanned, accepted leaf chunks, retries, and declared finding total.
3. `## Executive summary`
4. `## Scan coverage` — full file manifest or an unambiguous generated manifest section, chunk completion table (including pre-dispatch size validation and post-wave reconciliation results), and per-dimension counts.
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
- persisted session status was `ready-for-synthesis` before plan generation;
- scan coverage proves every target file belongs to exactly one accepted leaf chunk and every audit dimension was processed;
- every accepted leaf chunk in the completion table shows a matched dispatched-vs-echoed file list (no sampling), with rejected parents traceable to their accepted children;
- no section says `see above`, uses an ID range, or substitutes a summary for row-level accounting.

Repair the artifact and rerun the gate until it passes. If a source limitation prevents repair, mark `NOT READY` and list the exact missing IDs or fields.

Complete when every check is recorded as passing in `## Executor readiness`, or the artifact clearly identifies why execution is blocked.

## 7. Report

Tell the human the session and output paths, finding/workstream/phase counts, readiness status, and any limitations. For zero findings, still write metadata, scan coverage, empty ledger/roadmap/matrix, reconciled zero accounting, and `READY — no execution required`. For one finding, create one workstream and one executable phase rather than using a separate format.

If execution is interrupted while chunks remain, report `PAUSED — resumable`, the session path, accepted/pending/blocked counts from `status`, and the exact resume command. Do not write or present `CODE-QUALITY-REMEDIATION.md` until synthesis can run; session state and worker evidence are the checkpoint.

Complete when the human can pass the written file and either a phase number or `all` directly to `phased-plan-executor`, or can resume a paused audit from the reported session without repeating accepted work.

## Integration with sibling skills

| Counterpart | Hand-off |
|---|---|
| `phased-plan-executor` | Executes one numbered phase or an approved multi-PR programme from this skill's `READY` output file. |
| `investigate-repo` | Validates uncertain reachability or repository claims before a gated phase runs. |
| `subagent-dispatch` | Supplies host-specific dispatch mechanics for chunk auditors. |
