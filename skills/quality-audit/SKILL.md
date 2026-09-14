---
name: quality-audit
description: "Runs a parallel code quality audit and turns its findings into a prioritised, phased remediation plan with coverage accounting. Use when asked to audit code quality, review for SOLID/complexity/smells, run a quality pass, or identify and sequence quality improvements across a path, diff, or repo. Not for: architecture-level design review (use architecture-audit), security review, PR requirements compliance, or implementing fixes."
argument-hint: "[path | glob | diff | (empty = whole repo)]"
model: sonnet  # sonnet is sufficient for mechanical per-chunk pattern-matching (SOLID/naming/complexity/smells); no need for opus-level reasoning
---

You are running a code quality audit. Task: `$ARGUMENTS`

## What This Command Does

The target file set is split into chunks, and the same `quality-auditor` persona runs on each chunk in parallel — each pass checks all four dimensions (SOLID, Naming & Clean Code, Complexity, Code Smells & Duplication) but only for the files in its chunk. Findings are consolidated into one severity-ranked report, then handed to `report-remediation-planner` to produce a prioritised, phased programme with complete finding coverage. Read-only: no production files are modified.

---

## Step 1: Resolve the Agent

Resolve `quality-auditor`'s file by checking, in order, and using the first that exists:
`.devin/agents/quality-auditor/AGENT.md` → `.claude/agents/quality-auditor.md` →
`~/.agents/agents/quality-auditor/AGENT.md` → `~/.claude/agents/quality-auditor.md`. Read it.

If none exist, stop and tell the human the `quality-auditor` agent is missing.

## Step 2: Load Standards

If `.context/index.md` or `.context/standards/code-quality.md` exists in the repo root, read the code-quality standard now. Pass its content (not the path) to every auditor pass in Step 4 so severity is calibrated against the project's actual thresholds rather than the auditor's defaults.

## Step 3: Resolve the Target File Set and Chunk It

Parse `$ARGUMENTS`:

- **`diff`** — run `git diff --name-only` against the merge base of the current branch (fall back to staged changes via `git diff --name-only --cached` if the working tree is clean). Read the current contents of each changed file.
- **A path or glob** — resolve it. If it's a directory, expand to the files inside it (respecting `.gitignore`).
- **Empty** — audit the whole repo. Prefer `git ls-files` (respects `.gitignore` automatically) if inside a git repo; otherwise glob from the repo root. Exclude `node_modules`, `dist`, `build`, `vendor`, `.git`, lockfiles, and other generated/binary paths regardless of source.

If the resolved file set is empty, stop and tell the human — do not run the auditors on nothing.

**Chunk the file list** — group related files together (same directory/module first) rather than splitting arbitrarily, so each auditor pass sees coherent context:

- Target **~30KB of source or 15 files per chunk**, whichever limit is hit first.
- A single file larger than the per-chunk budget gets its own chunk rather than being split mid-file.
- Cap concurrent passes at **8 chunks per wave**. If there are more than 8 chunks, run 8 at a time, waiting for each wave to complete before starting the next — do not exceed the cap just to finish in one wave.

Read each chunk's file contents only when it is about to be dispatched, not all up front, if the target set is large enough that holding everything in memory at once defeats the purpose of chunking.

## Step 4: Fan Out (parallel passes per chunk)

For each wave, launch one `quality-auditor` pass per chunk in parallel, using the spawning mechanism native to your runtime:

- **Devin CLI**: `run_subagent` with `profile: "quality-auditor"`, `is_background: true` for every chunk in the wave, then `read_subagent` (`block: true`) once all of that wave's passes are launched. If the profile is rejected as unrecognized, tell the human immediately and stop — every subsequent chunk would fail the same way.
- **Claude Code**: spawn each as a `Task` tool call with `subagent_type: "quality-auditor"`.
- **Other hosts**: use the native parallel-subagent primitive. If none exists, say explicitly that chunks are being run sequentially inline rather than presenting it as parallel passes.

Give every pass: the file contents (not paths) for its assigned chunk only, and the code-quality standard content from Step 2 (if loaded). Each pass covers all four dimensions for its chunk — there is no per-dimension instruction to vary; the only thing that differs between calls is which files are in the chunk.

## Step 5: Consolidate

Collect every chunk's report across all waves. Merge duplicates without dropping aliases, assign each distinct finding a stable ID (`QA-001`, `QA-002`, etc.), and sort by severity (Critical → Major → Minor), then by file path. Preserve each finding's location, dimension/rule, issue, proposed fix, and source chunk. Sum the per-dimension counts across chunks.

Complete when every distinct finding has one stable ID and the severity and dimension totals reconcile to the consolidated list.

## Step 6: Report

Print to the console — do not write a report file:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CODE QUALITY AUDIT — {target}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Files scanned: {n}

Critical ({n}):
  {stable ID} — {file}:{line} — {issue} [{dimension}/{rule}] → {fix}

Major ({n}):
  {stable ID} — {file}:{line} — {issue} [{dimension}/{rule}] → {fix}

Minor ({n}):
  {stable ID} — {file}:{line} — {issue} [{dimension}/{rule}] → {fix}

By dimension:  SOLID {c}/{m}/{n}   Naming {c}/{m}/{n}   Complexity {c}/{m}/{n}   Smells {c}/{m}/{n}
(critical/major/minor)

Any dimension that could not run: {name it, or omit this line}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

Complete when the human can see the full stable-ID audit and its reconciled totals.

## Step 7: Produce the Phased Remediation Plan

If there are two or more findings, invoke `report-remediation-planner` and pass the complete consolidated audit from Step 6 as its report input. Follow that skill as the authority for finding ledger fields, duplicate accounting, workstreams, phase sequencing, acceptance criteria, coverage gates, and output order. Keep the `QA-*` IDs unchanged so every audit finding remains traceable through the plan.

If the planner skill cannot be resolved, stop after the audit and tell the human that the review succeeded but the phased plan could not be produced; name the missing skill rather than substituting an ad hoc checklist.

If there is exactly one finding, do not invoke the multi-finding planner. Add a single-issue remediation section containing the finding ID, objective, prerequisite, acceptance criterion, and closure check. If there are no findings, state that no remediation plan is needed.

Print the plan directly after the audit unless the human requested an output file; in that case, let `report-remediation-planner` apply its output-file behavior. Do not implement fixes, open tickets, or modify production code.

Complete when every audit finding maps to exactly one phased workstream and acceptance criterion, or the zero/single-finding branch has been reported explicitly.
