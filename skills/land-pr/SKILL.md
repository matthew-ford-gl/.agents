---
name: land-pr
description: "Takes a GitHub or Azure DevOps PR, resolves actionable review feedback, fixes completed failing CI, requeues eligible expired builds, and verifies merge readiness in one bounded pass without monitoring running checks. Use when asked to land, finish, or get an existing PR ready to merge. Not for: polling CI, opening a PR, static review without fixes, or merging the PR."
argument-hint: "<PR number or URL (GitHub or Azure DevOps)>"
disable-model-invocation: true
model: sonnet
---

# Land PR

Task: $ARGUMENTS

Invocation authorizes commits, normal pushes, thread replies/resolution, and eligible CI requeues on the PR branch. It does not authorize force-push, history rewriting, or merging. Run one bounded snapshot-based pass. Never wait, watch, sleep, or poll remote state. Await each finite local validation command once; do not abandon it merely because the tool backgrounds it.

## Operating contract

The coordinator owns remote state, classification, validation, commits, pushes, replies, resolutions, requeues, and reporting. `pr-fixer` is the only fix author; `code-reviewer` is read-only. The coordinator must not edit repository files during remediation. Both agents use the invocation checkout, never a clone, worktree, sandbox copy, or dependency copy.

Resolve one Python 3 launcher without installing anything: try `python3`, then `python`, then `py -3`, stopping at the first command whose version is 3.9 or newer. Store the full launcher command as `<python>` and reuse it; do not probe again. While the working directory remains the invocation checkout, run `<python> <land-pr-skill-dir>/scripts/preflight.py "$ARGUMENTS" --create` once. Reuse its compact JSON for repository, platform, cleanliness, agent, context, checkpoint, handoff, and telemetry paths; do not rediscover those values with separate searches or help commands.

Python is optional. If no supported launcher exists or a bundled script cannot run, do not install Python or stop solely for that reason. Resolve the same values with the documented host tools, execute the matching platform reference's exact bounded commands, append equivalent phase fields directly to `telemetry.jsonl` when the host can write it, and record `preflight-fallback`, `snapshot-fallback`, or `telemetry-fallback` in the checkpoint.

Resolve agents in this order: `.devin/agents/<name>/AGENT.md` → `.claude/agents/<name>.md` → `~/.agents/agents/<name>/AGENT.md` → `~/.claude/agents/<name>.md`. Use the paths returned by preflight and the runtime-native dispatch mechanism. If dispatch is unavailable or requires another checkout, stop and report that the ownership gate cannot be satisfied; do not author fixes inline.

Dispatch prompts contain only the task, absolute evidence/source paths, and the instruction to read only applicable files. Do not inline file contents. Reuse the current dependency installation and caches; do not restore/install merely to refresh them.

### Context paths

Resolve `context_root` in order: `CONTEXT_STORAGE_PATH`; `root` in repository `.devin/agent-context.json`; `root` in `~/.config/devin/agent-context.json`; writable host temp directory; `<repo>/.tmp`. Resolve configured relative paths from the config file, probe read/write access, and continue to the next option if a configured root fails. When `.tmp` is used, ensure it is ignored without duplicating a rule.

Reuse a caller-provided `session_context`; otherwise derive `<context_root>/<safe-repo-name>/<session-id-or-one-generated-uuid>`. Set `context_dir = <session_context>/land-pr`, canonicalize it, and verify it is a strict descendant of `session_context` before writing. Set persistent paths outside the session directory:

- `checkpoint_path = <context_root>/<safe-repo-name>/land-pr-checkpoint-<safe-pr-id>.json`
- `handoff_path = <context_root>/<safe-repo-name>/land-pr-handoff-<safe-pr-id>.md`

Read only the checkpoint fields needed to filter previously resolved threads before the remote
snapshot. Defer project context and all other local loading until Phase 2.

### Phase telemetry

After each phase, append one event with `<python> <land-pr-skill-dir>/scripts/telemetry.py <telemetry_path> <phase>` and the observed tool-call, remote-call, byte, retry, reason, and outcome values. Record `fast-path-rejected`, `scope-expanded`, `fallback`, and validation-blocked reasons when applicable. Telemetry is diagnostic only and must not cause an otherwise valid pass to fail.

## Phase 1: Resolve platform and take one remote snapshot

Use the platform returned by preflight and read only the matching platform reference:

- GitHub: `references/github.md`
- Azure DevOps: `references/azure-devops.md`

Run `<python> <land-pr-skill-dir>/scripts/snapshot.py <platform> "$ARGUMENTS" --output <context_dir>/snapshot.json` once. Reuse its compact JSON for identifiers, title, source/base branch, commits, conflict state, changed-file names, unresolved thread histories, checks/policies, and reviewer states. Follow the matching reference only for data the script explicitly marks unresolved; do not use CLI help, retry alternate API versions, fetch broad raw payloads, a diff, or CI logs. If the script fails, use the reference's exact fallback commands once and record the fallback and error in telemetry.

Classify each check from this snapshot only:

- completed successful → green
- queued/running/pending → waiting; never query it again this invocation
- completed unsuccessful → actionable failure
- expired/stale → requeue candidate

Classify each unresolved thread as reply-only, actionable code change, or human-decision blocker. Do not resolve disagreements or genuinely ambiguous requests.

### Remote-only fast path

If there are no conflicts, no actionable threads, no completed unsuccessful checks, and no expired/stale checks eligible for requeue:

1. Reply to and resolve any reply-only threads that inspection fully answers.
2. Report current threads, checks, approvals, and exact waiting/blocking items.
3. Write the checkpoint and stop without reading project source/context, checking out the branch, generating a diff, fetching logs, dispatching agents, or running local validation.

This fast path includes all-green PRs and PRs whose only incomplete checks are queued/running.

Complete when the remote snapshot is classified and either the fast path has stopped or local work is proven necessary.

## Phase 2: Load local context and checkpoint only when work is necessary

Require a clean index/worktree with no untracked paths that checkout could overwrite. If dirty, stop and ask the user to commit or stash; never alter their work. Read repository/nearby `AGENTS.md`, repository `.claude/CLAUDE.md` or `CLAUDE.md`, and matching `.context/index.md` entries only for changed files implicated by actionable items.

Read the checkpoint when present. Discard it if it names another PR. Track:

- `pass_number`: prior invocations that attempted a fix, conflict sync, or requeue
- `resolved_threads`, `green_checks`, and `context_files_loaded`
- `failed_fixes`: target, approach, and result

Increment `pass_number` once immediately before this invocation's first fix, conflict sync, or requeue. Read-only invocations do not increment it. If that would exceed 4, write the current state, attempts, and suggested human actions to `handoff_path`, report it, and stop. After two distinct failed approaches for one target across passes, make it a human-decision blocker.

Fetch only the source branch and switch this checkout using `git switch`; do not use a platform checkout command. If another worktree owns the branch, report its path and ask the user. Do not force or delete it.

Complete when relevant instructions are loaded, pass state is valid, and the clean invocation checkout is on the PR branch.

## Phase 3: Resolve reported conflicts

Only when the Phase 1 snapshot reports actual conflicts, fetch the remote default branch and integrate it according to repository policy. Invoke `resolving-merge-conflicts` for conflict resolution. Never use blanket `ours`/`theirs`. If policy requires rebase, ask before the required force-push. For a merge, run applicable integration validation, commit when needed, verify with `git log -1 --stat`, and push normally. Stop on non-fast-forward rejection.

Do not update a merely-behind branch. Complete when no conflicts were reported or reported conflicts are resolved and pushed.

## Phase 4: Build one remediation batch

Combine all actionable thread fixes and completed unsuccessful checks into one batch. Reply-only threads may be handled directly; preserve human-decision blockers unresolved.

For each completed unsuccessful check, inspect the failed-task output and classify it directly from evidence as:

- fixable code/test/config failure
- likely flake
- external infrastructure/environment failure
- insufficient evidence

Requeue a likely flake once. Do not author changes for external or insufficient-evidence failures; report them as blockers. Do not use a separate triage skill or agent.

Stage only current evidence under `<context_dir>/current-batch/`:

- `remediation.md`: identifiers, acceptance criteria, direct classifications, prior failed approaches, and required drafted thread replies
- `diff.patch`: diff scoped to implicated files
- `threads/<safe-id>.md`: full history for actionable threads only
- `ci-logs/<safe-name>.log`: failure-bearing excerpt only
- `standards/`: applicable project standards only

CI log excerpts have a hard cap of 400 lines and 40 KiB per check after secret redaction. Prefer the failing step plus up to 100 lines before and after it; otherwise retain bounded head/tail sections. Record truncation, original size, and selected ranges in `remediation.md`. Never stage whole-run logs when failed-task logs exist.

Pass source files by absolute checkout path; do not copy them. Complete when one minimal batch contains every fixable item.

## Phase 5: One fix, review, and correction cycle

Skip this phase when the combined batch has no fixable items.

1. Record the pre-fix changed paths, then dispatch `pr-fixer` once with `remediation.md`, scoped diff, actionable evidence, applicable standards, and source paths. It edits the working tree and drafts thread replies but does not validate, commit, push, reply, or resolve.
2. Compare post-fix paths with the implicated paths and actionable-item count. If the fixer touched any unimplicated path or more than `max(5, 3 × actionable items)` files, require a path-by-path scope justification in its result, record `scope-expanded` in telemetry, and stop before validation when any path remains unjustified.
3. Run targeted validation covering changed code and reproduced failures only.
4. Regenerate the scoped diff and dispatch `code-reviewer` with `remediation.md`, the diff, applicable standards, validation result, and any scope-expansion justification.
5. If BLOCKED, allow exactly one correction: dispatch `pr-fixer` with the review findings, then rerun targeted validation and `code-reviewer` once. If still BLOCKED, preserve the working tree and report the findings as blockers; do not loop again.
6. When approved, run the repository's full required validation exactly once on the final working-tree state. Start it as one finite foreground command. If the tool backgrounds it, call the process-output tool once with a timeout long enough for the command to finish; this is awaiting local work, not polling remote state. If it remains in progress after that one await, preserve its process identifier and report `BLOCKED — waiting`, leaving remediation in progress. If it fails, do not return to the correction loop; report the failure with evidence unless the failure is an immediately correctable command/environment issue that does not alter code.
7. Commit all approved batch changes together using repository attribution conventions. Verify expected files with `git log -1 --stat`, then push normally once.
8. Reply to and resolve each addressed thread using the final drafted replies and commit hash. Leave unaddressed/ambiguous threads open.

Do not validate the same working-tree state twice. Remote CI is the final full-gate confirmation after the push. Complete when the consolidated batch is pushed and resolved, a completed validation failure is recorded, or an explicitly identified local validation process remains in progress.

## Phase 6: Handle expired checks and record post-push state

Requeue an expired/stale check at most once and only when every required reviewer is fully approved (`APPROVED` on GitHub; vote `10` on Azure DevOps). If approval is missing, report who is required and do not requeue. Record the new run/build identifier and immediate status, then do not query it again.

A fix push normally triggers affected checks; do not manually trigger them unless platform evidence shows it did not. Never fetch or re-query queued/running checks. Re-fetch reviewer state only after a push when platform policy may reset approvals.

Complete when each check is green, waiting from the single snapshot/new identifier, or a reasoned blocker.

## Phase 7: Checkpoint and report

Write the checkpoint before reporting:

```json
{
  "pr": "<URL or number>",
  "pass_number": 0,
  "timestamp": "<ISO 8601>",
  "resolved_threads": [],
  "green_checks": [],
  "failed_fixes": [{"target":"", "pass":0, "approach":"", "result":""}],
  "outstanding_threads": [],
  "outstanding_checks": [],
  "context_files_loaded": [],
  "telemetry_path": "<absolute path or null>",
  "telemetry_fallbacks": [],
  "phase_metrics": {"snapshot":{"tool_calls":0,"remote_calls":0,"retries":0,"reason":"","outcome":""}}
}
```

Report title/URL, verdict, pass, branch/conflict state, resolved threads, green/total required checks, approvals, blockers/waits, and next action.

- `READY TO MERGE`: no conflicts, all threads resolved, all required checks green, and all required reviewers fully approved. Stop; never merge.
- `BLOCKED — waiting`: only running/queued CI or reviewers remain.
- `BLOCKED — human decision`: ambiguity, disagreement, insufficient evidence, external failure, exhausted approaches, or failed reviewer gate.
- `BLOCKED — actionable`: continue only if an unprocessed actionable item remains in this same bounded pass.

Retain `context_dir` for diagnostics and report its path when it was created. On READY, remove only checkpoint/handoff files. Otherwise retain them. Complete when the verdict cites concrete evidence for every open item.
