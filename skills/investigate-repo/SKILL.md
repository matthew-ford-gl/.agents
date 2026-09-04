---
name: investigate-repo
description: "Investigate a repository question or validate a Markdown list of findings, checking every claim against current code and proving whether the relevant code is reachable rather than dead. Use when asked to answer a 'how does X work' or 'is Y still used' repository question, verify or validate findings from an existing audit/scan/report against the actual codebase, confirm whether flagged code is dead or reachable in production, or check claims before acting on them. Not for: synthesising multiple findings into a prioritised remediation plan or workstreams (use report-remediation-planner), or running a fresh SOLID/naming/complexity/clean-code scan to generate new findings (use quality-audit)."
argument-hint: "<question | markdown | path-to-markdown>"
model: sonnet  # orchestration/dispatch workload (parsing claims, fanning out investigators, reconciling results); the reasoning-heavy work happens in the dispatched repo-investigator subagents, so a lighter model here is sufficient
---

You are running a read-only repository investigation. Input: `$ARGUMENTS`

## Purpose

Answer a repository question with evidence, or validate every distinct claim in supplied Markdown. The workflow does not trust the supplied audit, skip inconvenient findings, modify code, or turn absence of a textual reference into proof of dead code.

## Step 1: Load Project Context

1. Read the repository root `AGENTS.md` and any nearer `AGENTS.md` files relevant to the investigation.
2. If `.claude/CLAUDE.md` exists in the repository root, read it.
3. If `.context/index.md` exists, scan it for terms related to the input and load every matched standard, playbook, and convention.
4. Identify repository-specific verification commands and architecture documentation that may apply.

Treat loaded instructions as mandatory and pass their relevant content to every investigator.

Complete this phase when project-specific instructions, standards, and verification commands relevant to the investigation have been identified and loaded (or confirmed absent).

## Step 2: Resolve the Investigator

Resolve `repo-investigator` by checking, in order, and using the first definition that exists:

`.devin/agents/repo-investigator/AGENT.md` → `.claude/agents/repo-investigator.md` → `~/.agents/agents/repo-investigator/AGENT.md` → `~/.claude/agents/repo-investigator.md`.

Read the resolved definition. If none exists, stop and tell the human that the `repo-investigator` agent is missing.

Complete this phase when the `repo-investigator` definition has been resolved and read, or the human has been told it is missing and the workflow has stopped.

## Step 3: Resolve and Parse the Input

Interpret `$ARGUMENTS` as follows:

- If it names an existing file, read that file as the source document.
- Otherwise, treat it as inline Markdown or a free-form repository question.
- If it is empty, ask the human for a question or Markdown findings list; do not invent a target.

For a source document, preserve any existing finding IDs. Parse tables, headings, numbered lists, and checklist items into atomic claims. Keep explanatory paragraphs with the finding they qualify.

A claim is atomic when one investigator can return one verdict. Split a finding only when it makes independently testable assertions that could receive different verdicts. Do not split one end-to-end data-flow or reachability claim into disconnected fragments.

Before dispatch, print a short manifest containing the number of claims and their IDs or concise titles. If the document is ambiguous enough that parsing choices could change the outcome, ask the human to confirm the manifest. Otherwise continue without blocking.

Complete this phase when every claim has been parsed into an atomic, independently verdict-able unit, the manifest has been printed, and any required human confirmation has been received.

## Step 4: Dispatch Every Claim

Investigate every parsed claim; never sample. Give each investigator:

- exactly one atomic claim, including its original wording and surrounding qualifiers;
- relevant project instructions and standards loaded in Step 1;
- the repository root and current branch or revision;
- any source-document path for provenance;
- an explicit instruction to inspect current repository files directly and return the complete `repo-investigator` response contract: Verdict, Reachability, Confidence, Claim, Evidence, Trace, Dead-code analysis, Verification, and Caveats.

Use the spawning mechanism native to the runtime:

- **Devin CLI**: launch `run_subagent` with `profile: "repo-investigator"` and `is_background: true` for every claim in the wave, then collect every result with `read_subagent` (`block: true`) after the full wave has launched. If the named profile is rejected as unrecognized, retry with `profile: "subagent_general"`; prepend the original claim instructions to the full resolved `repo-investigator` definition from Step 2 and pass that combined content as the `task` prompt. Reiterate in the fallback prompt that only `read`, `grep`, `glob`, and the definition's restricted `exec` commands may be used; `write`, `edit`, and all other state-changing tools remain prohibited even if the fallback profile exposes them.
- **Claude Code**: spawn a `Task` with `subagent_type: "repo-investigator"`.
- **Other hosts**: use the native subagent mechanism. If none exists, investigate claims sequentially inline and say so explicitly.

Run independent claims in parallel, capped at **8 investigators per wave**. Collect all results from a wave before starting the next. If claims overlap heavily or one depends on another's result, run those claims sequentially and pass forward only verified evidence.

If an investigator fails to start even with the fallback, or returns no verdict, retry that claim once with a narrower prompt using the same profile/fallback sequence. If it still fails, report **Insufficient evidence** for that claim and include the failure reason. One failed investigation must not prevent the remaining claims from being checked.

Complete this phase when every manifest claim has a returned investigator result — a verdict, or a documented **Insufficient evidence** fallback after retry.

## Step 5: Validate the Results

Before reporting:

1. Confirm that every manifest item has exactly one result.
2. Confirm that every result contains Verdict, Reachability, Confidence, Claim, Evidence, Trace, Dead-code analysis, Verification, and Caveats. Verdict must be exactly **Confirmed**, **Partially confirmed**, **Not reproducible**, **Dead/unreachable code**, or **Insufficient evidence**; Reachability must be exactly **Production-reachable**, **Conditionally reachable**, **Non-production only**, **Dead/unreachable**, or **Unknown**; Confidence must be exactly **High**, **Medium**, or **Low**. Retry incomplete or out-of-contract results once; if still invalid, retain available evidence, use **Insufficient evidence**, **Unknown**, and the evidence-appropriate confidence.
3. Reject conclusions unsupported by concrete repository evidence and downgrade them to **Insufficient evidence**.
4. Check that the Trace connects the relevant entry point or caller to the behavior, and that Dead-code analysis considers indirect and framework-driven reachability.
5. Check that Verification names commands and outcomes or explicitly states that only static inspection was available, and that Caveats identifies unavailable runtime evidence and verdict-changing conditions.
6. Reconcile contradictory results by inspecting the shared evidence or dispatching one tie-break investigation; do not silently choose one.
7. Preserve uncertainty where runtime configuration, external systems, generated artifacts, or live data are unavailable.

## Step 6: Report

Print the report to the console. Do not create or edit a report file unless the human asks.

```markdown
# Repository Investigation — {question or source document}

**Revision:** {branch and commit}
**Claims checked:** {n}

## Summary

| ID | Verdict | Reachability | Confidence | Short reason |
|---|---|---|---|---|
| {id} | {verdict} | {reachability} | {confidence} | {reason} |

## Findings

{full investigator result for every claim, in source order}

## Overall assessment

- Confirmed: {n}
- Partially confirmed: {n}
- Not reproducible: {n}
- Dead/unreachable code: {n}
- Insufficient evidence: {n}

## Cross-cutting caveats

{Constraints affecting multiple findings, or `None.`}
```

Do not collapse **Dead/unreachable code** into **Not reproducible**: the former means the behavior exists but is not reachable in the relevant runtime; the latter means the current repository does not support the alleged behavior. Do not restate the supplied severity as fact. If recommendations were requested, add them after the evidence-backed verdicts and label them separately.
