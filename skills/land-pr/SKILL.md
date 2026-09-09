---
name: land-pr
description: "Takes a PR number or URL (GitHub or Azure DevOps), brings the branch up to date with the default branch, resolves every open review thread with a code fix or reply, investigates and fixes failing CI checks, requeues expired or stale builds, and repeats until every thread is resolved, CI is green, and the required reviewer's vote is a full approval — not 'approved with suggestions'. Stops short of merging. Use when asked to get a PR ready to merge, babysit a PR, drive PR feedback and CI failures to zero, or land/finish a PR end-to-end. Not for: opening a brand-new PR (use ship), a one-off static compliance review with no fix loop (use review-pr), or merging/completing the PR itself (always left to the user)."
argument-hint: "<PR number or URL (GitHub or Azure DevOps)>"
disable-model-invocation: true
model: sonnet  # coordinator role only — classifies state and drives phase transitions; actual fix-authoring is dispatched to pr-fixer (sonnet, write-capable) and gated by code-reviewer
---

# Land PR

Task: $ARGUMENTS

This is a user-invoked workflow because it commits, pushes, replies to and resolves PR review
threads, and requeues CI builds. Explicit invocation authorizes all of that on the PR's own
branch. It never authorizes force-pushing the default branch, rewriting history other
collaborators may have already based work on without confirmation, or merging/completing the
PR — that last step always belongs to the user.

Repeat Phases 4-8 each time you're invoked (this skill is idempotent: it re-reads current state
rather than assuming anything from a previous pass, but uses the checkpoint file from Phase 0b
to skip already-resolved items and avoid retrying the same failed approaches). A maximum of 4
passes are allowed per PR before escalating to a human via a handoff document. For long
unattended monitoring beyond a single pass, tell the user to wrap this skill with `/loop`,
e.g. `/loop 10m /land-pr <PR>`, rather than sleeping inside one invocation for hours.

## Role split

You (the coordinator) own state: fetching review/CI status, classifying threads and check
failures, deciding what happens next, and every commit/push/reply/resolve/requeue action.
You never author a code fix yourself — Phases 5 and 6 dispatch `pr-fixer` for that, then gate
its output through `code-reviewer` and your local validation gate before anything is committed
or pushed. This keeps exactly one writer touching the branch at a time and keeps a bad fix from
ever reaching a live thread reply or a pushed commit.

**Path resolution** — for `orchestrator`, `pr-fixer`, `code-reviewer`, and the
`test-failure-triager` skill, resolve in order: `.devin/agents/<name>/AGENT.md` →
`.claude/agents/<name>.md` → `~/.agents/agents/<name>/AGENT.md` →
`~/.claude/agents/<name>.md` (agents); for the skill,
`.devin/skills/test-failure-triager/SKILL.md` → `.claude/skills/test-failure-triager/SKILL.md` →
`~/.agents/skills/test-failure-triager/SKILL.md` → `~/.claude/skills/test-failure-triager/SKILL.md`.

**Spawning `pr-fixer` / `code-reviewer`** — same runtime-native mechanism `orchestrator`
documents for its reviewers (Claude Code: `Task`/`Agent` with `subagent_type` set to the
agent's `name`; Devin CLI: `run_subagent` with `profile: "<name>"`, falling back to
`subagent_general` with the resolved `AGENT.md` content as the prompt if the profile is
unrecognized). Pass paths under `context_dir`, not inline content. Tell each agent to read
the applicable files at the start and include only its instructions and paths in the dispatch
prompt.

**Context workspace** — read and apply `orchestrator`'s **Context workspace** section as the
single source of truth for root configuration, access probing, repository naming, session-ID
fallback, and path safety. If a caller provides `session_context`, reuse it; otherwise resolve
one for this invocation. Set `context_dir = <session_context>/land-pr` and pass absolute paths
to subagents. Complete when `session_context` and `context_dir` are absolute, session-scoped,
and readable by the coordinator and subagents.

**`test-failure-triager` is invoked as a skill, not a subagent** — it has no `model:` field,
so it runs inline in your own context rather than as a separate dispatch. Use it, don't
re-derive its classification rules; copying them here would drift from the source.

**Commit verification** — after every `git commit` in Phases 3, 5, or 6, run
`git log -1 --stat` before pushing and confirm the expected files actually appear in it. A
pre-commit hook can fail silently on a broken local toolchain and leave `HEAD` pointing at a
stale or empty commit; pushing that would land a broken change with no code to show for it.
If the commit doesn't contain what you expect, stop and fix the toolchain issue rather than
retrying the push.

---

## Phase 0: Load project context

1. Read the repository root `AGENTS.md` and any nearer `AGENTS.md` for paths the PR touches. Treat repository instructions as mandatory.
2. If `.claude/CLAUDE.md` (or repo-root `CLAUDE.md`) exists, read it — including branch/merge policy (rebase vs merge commit, force-push rules) and commit-attribution convention.
3. If `.context/index.md` exists, load any entries matching the PR's domain.

Complete when applicable instruction files are loaded.

---

## Phase 0b: Pass tracking

Check for an existing checkpoint file at `.tmp/land-pr-checkpoint.json` in the repository
root.

If found, read it and extract:
- `pass_number`: increment by 1 for this pass.
- `pr`: verify it matches the current PR argument (discard the checkpoint if different PR).
- `resolved_threads`: thread IDs already resolved in previous passes — do not re-process
  these in Phase 5 unless they have new unresolved comments.
- `green_checks`: check names that were green at end of previous pass — still re-verify
  in Phase 4 but don't investigate them in Phase 6 unless they're now failing.
- `failed_fixes`: record of fixes attempted that didn't resolve their target — try a
  different approach or escalate.
- `context_files_loaded`: which project context files were loaded (skip re-reading
  if checkpoint exists and files haven't changed).

If not found, or if reading fails (corrupted/malformed), this is pass 1. Create the
checkpoint structure in memory.

**Max-pass cap**: if `pass_number` > 4, do NOT proceed with another fix attempt.
Instead:
1. Write a final handoff document to `.tmp/land-pr-handoff.md` containing:
   - PR URL and current state summary
   - Threads still unresolved (with comment history summary)
   - CI checks still failing (with last error summary)
   - What was tried on each failing item across all passes
   - Suggested next steps for a human
2. Report the handoff path to the user:
   "Max attempts (4 passes) reached. Handoff written to `.tmp/land-pr-handoff.md`.
   Review the outstanding items and either fix manually or reset the checkpoint
   with `Remove-Item .tmp/land-pr-checkpoint.json` to allow further automated attempts."
3. Stop.

Complete when `pass_number` is set and is <= 4, or the handoff has been written and the
skill has stopped.

---

## Phase 1: Resolve the PR and platform

Parse `$ARGUMENTS`:

- **Full GitHub URL** (`github.com/{owner}/{repo}/pull/{number}`): extract `owner`, `repo`, `pullNumber`. `platform = github`.
- **Full Azure DevOps URL** (`dev.azure.com/{org}/{project}/_git/{repo}/pullrequest/{id}` or `{org}.visualstudio.com/{project}/_git/{repo}/pullrequest/{id}`): extract `org`, `project`, `repo`, `pullRequestId`. `platform = ado`.
- **Bare PR number**: run `git remote get-url origin` to detect the platform from the remote URL, then resolve the rest of the identifiers via that platform's CLI (`gh pr view <number>` or `az repos pr show --id <number>`; see the matching reference file).

If the input matches neither form and no origin remote resolves it, stop and tell the user the PR could not be identified.

Complete when `platform` and every identifier needed for later phases are set.

---

## Phase 2: Sync the local branch safely

This phase operates **in place**, in whichever folder this skill was invoked from — including
a git worktree folder. Switch that folder's checked-out branch to the PR's source branch; never
`git clone` a fresh copy of the repo and never create a new worktree (e.g. `git worktree add`,
`EnterWorktree`) to work in instead. A worktree folder is reused across PRs by changing which
branch it has checked out, not by spinning up another folder per PR.

Record the repository root, current branch, and worktree status. Require a clean index and worktree — no uncommitted changes, no untracked paths that a checkout could overwrite. If dirty, stop and ask the user to commit or stash first; never stash or discard automatically.

Check out the PR's source branch locally (`gh pr checkout <number>`, or for ADO fetch the source branch named in `az repos pr show` and check it out). Stop if the checkout would overwrite local work.

If git refuses the checkout because the branch is already checked out in another worktree
(`fatal: '<branch>' is already checked out at '<path>'`), that other worktree is a separate
in-progress checkout — do not force it or delete that worktree. Tell the user about the
conflicting worktree path and ask how they want to proceed rather than guessing.

Complete when the PR's source branch is checked out locally, in this same folder, with a clean worktree.

---

## Phase 3: Bring the branch up to date with the default branch

`merge-default-branch` has `disable-model-invocation: true` and cannot be invoked via the Skill tool from here — this phase performs the same steps directly instead, staying within the authorization already granted by this skill's own user invocation (fetch, merge, push on the PR's own branch).

1. Discover the remote default branch (remote's symbolic `HEAD` — do not assume `main`/`master`) and fetch it without pruning or touching unrelated refs.
2. Merge `<remote>/<default>` into the current branch using the repository's documented merge policy. Do not rebase, squash, or use a blanket `ours`/`theirs` strategy.
3. If Git reports conflicts, invoke the `resolving-merge-conflicts` skill with the target branch, fetched source ref, and this skill's existing authorization to complete the merge commit. Return here only after it reports zero unresolved paths or a blocker.
4. If already up to date, continue without an empty commit. Otherwise complete the merge commit with normal hooks and message conventions.
5. Run the repository's required validation (from `AGENTS.md`/CI) on the integrated result; fix only failures caused by the integration.
6. Push the current branch normally (no force). Stop on a non-fast-forward rejection and ask the user how to reconcile it.

If repository policy (`AGENTS.md`/`CONTRIBUTING`/`CLAUDE.md`) mandates rebase or linear history instead of a merge commit, rebase onto the default branch instead. A rebase rewrites commits already pushed on this PR branch, so **stop and ask the user before force-pushing** the rebased branch — this is the one force-push this skill may ever need, and it needs explicit per-use confirmation regardless of how this skill was invoked.

Complete when the branch contains the latest default-branch commits and the result (merge or rebase) is pushed.

---

## Phase 4: Fetch full review state

Read `references/github.md` or `references/azure-devops.md` (matching `platform`) and follow its Phase 4 steps to fetch:

- PR metadata, diff, and changed files.
- Every review comment thread, with its resolved/unresolved status and full comment history.
- Every CI/build check or policy, with status (passed / failed / pending / expired / running) and a way to reach its logs.
- Every reviewer's current review state or vote, and which reviewers/policies are required.

Complete when all four are captured for the current state of the PR (not a cached view from an earlier pass).

Before a `pr-fixer` or `code-reviewer` dispatch in Phases 5-6, create or refresh the applicable
context under `<context_dir>/`:

1. `diff.patch` — the current full diff.
2. `threads/<thread-id>.md` — one file per actionable thread, containing its full comment history.
3. `ci-logs/<check-name>.log` — one file per failing check, containing its pulled logs.
4. `standards/` — one file per standard or playbook loaded in Phase 0.

Use filesystem-safe thread IDs and check names. If the repository-local fallback is selected,
ensure `.tmp/` is ignored by Git, checking effective rules before adding a non-duplicate entry.
Refresh changed evidence before every dispatch so agents never review stale state. Pass only
applicable paths to each agent rather than making every agent load every file.

---

## Phase 5: Resolve every open comment thread

Before classifying threads, consult the checkpoint (from Phase 0b) if one exists:

- **`resolved_threads`**: check each against the current thread state. If a previously-resolved
  thread is still resolved, skip it entirely. If a previously-resolved thread has new unresolved
  comments, process only the new comments.
- **`failed_fixes`** for a thread: do NOT retry the same approach — the dispatch to `pr-fixer`
  must include the previous attempt(s) and their outcomes so it tries something categorically
  different. After 2 different approaches on the same thread across passes, classify it as a
  human-decision blocker.

For each thread that is not already resolved, **classify** it: a concrete actionable
code-change request, a question/discussion, a nit, or a point you disagree with.

- **Question/nit** you can satisfy by inspection with no code change: answer, reply, resolve
  directly — no need to involve `pr-fixer` for a reply-only thread.
- **Disagreement or genuinely ambiguous request**: reply with your reasoning, but **do not
  resolve the thread** — leave it open and record it as a human-decision blocker for the
  final report. Never resolve a thread you're not confident is actually addressed.
- **Actionable** (needs a code change): batch every actionable thread from this pass and
  run the fix-review loop below once for the whole batch.

**Fix-review loop** (actionable threads):

1. Dispatch `pr-fixer` with paths to `diff.patch`, every actionable thread file in the
   batch, applicable source files, and applicable staged standards. It returns working-tree
   changes plus a drafted reply per thread — it does not commit, push, reply, or resolve.
2. Run the project's build/lint/test commands (from `AGENTS.md` or standard tooling) against
   the working tree.
3. Dispatch `code-reviewer` against the resulting diff.
4. If `code-reviewer` returns BLOCKED or lists Must-fix items: re-dispatch `pr-fixer` with
   its feedback as the priority item, and repeat from step 2. Track attempts for this batch;
   after 3 failed loop attempts, stop, leave the working tree as-is, and record every thread
   still unaddressed as a blocker with what was tried.
5. Once the gate passes and `code-reviewer` returns APPROVED (or only nits): commit using the
   attribution convention below, reply on each addressed thread with `pr-fixer`'s drafted
   text (summarising what changed and referencing the commit), and resolve it.

Commit-attribution convention: if the repository's or user's global instructions specify one, use it exactly. Otherwise use a generic `Generated with [tool name]` line with a matching `Co-Authored-By:` for your own host/runtime — never hardcode another runtime's convention.

Push commits normally (no force) to the PR branch once the batch is committed.

Complete when every thread is either resolved-with-a-reply or explicitly recorded as a human-decision blocker, and any resulting commits are pushed.

**Context shedding**: before proceeding to Phase 6, discard the full thread comment histories
from your active context. Retain only: the list of thread IDs with their resolution status
(resolved/blocked/new-comments), and for any threads dispatched to `pr-fixer`, retain only
the commit hash of the fix. The full comment text is in `<context_dir>/threads/` if needed
by a future dispatch.

---

## Phase 6: Investigate and fix CI

Before investigating checks, consult the checkpoint (from Phase 0b) if one exists:

- **`green_checks`**: still verify their current status from Phase 4 output, but don't
  investigate them unless they've regressed to failing.
- **`failed_fixes`** for a check: include the previous attempt details in the `pr-fixer`
  dispatch so it tries a categorically different approach. After 2 different approaches on
  the same check across passes, classify it as a human-decision blocker (not just "after 3
  failed loop attempts within one pass").

For every required check/policy that is not green:

- **Expired or stale** (timed out waiting to run, or a merge-policy build that expired):
  requeue it directly using the matching reference file's commands — no fix authoring needed.
- **Pending/running**: poll with backoff (e.g. every 1-2 minutes) for up to roughly 10-15
  minutes this pass. If it's still not finished after that, stop polling and report it as
  "in progress" rather than blocking the session further — recommend `/loop` for continued
  unattended checking.
- **Failed**: pull its logs, then invoke the `test-failure-triager` skill (see Path
  resolution above) with those logs and the diff to classify it — production bug, test bug,
  flake, or infrastructure/environment issue — using actual evidence, not a guess.
  - **Flake**: re-run/requeue it directly; no fix authoring.
  - **Production bug / test bug / fixable infra or config issue**: batch it with every other
    fixable failing check from this pass and run the same fix-review loop as Phase 5 —
    dispatch `pr-fixer` with paths to the staged logs and classification for the batch, run
    the local gate, refresh `diff.patch`, dispatch `code-reviewer` with the applicable paths,
    and loop on BLOCKED. Track attempts per distinct check; after 3
    failed loop attempts on the same check, stop trying it and record it as a blocker with
    what was tried and why it didn't resolve.
  - Once the gate and `code-reviewer` both pass: commit (attribution convention above), push,
    and re-run the affected remote check(s) to confirm.

Complete when every required check is green, or every non-green check is explicitly classified as in-progress or a blocker with reasoning.

---

## Phase 7: Verify full approval

Re-fetch current reviewer state (a push in Phase 5/6 may have reset prior votes — check the platform's actual reset-on-push behaviour rather than assuming).

- **GitHub**: every required reviewer's review state must be `APPROVED`.
- **Azure DevOps**: every required reviewer's vote must be exactly `10` (Approved). A vote of `5` ("Approved with suggestions") does **not** satisfy this — treat it the same as no approval and keep the PR open for that reviewer. Identify the required reviewer(s)/group from the PR's branch policy or the user's stated required reviewer, rather than assuming a name.

If new comments appeared since Phase 4 (a reviewer responded while you were fixing CI), loop back to Phase 5 for those threads before re-evaluating approval.

Complete when every required reviewer/policy shows a full approval, or the exact reviewer(s)/vote(s) still outstanding are identified.

---

## Phase 8: Verdict and next step

Determine the overall state:

- **READY TO MERGE**: branch up to date, every thread resolved, every required check green, every required reviewer at full approval. Report this and stop — do not merge or complete the PR yourself; hand it to the user.
- **BLOCKED — action needed from you**: something in Phases 5-6 is still fixable by you (untried fix, unaddressed thread). Keep working through it in this same pass.
- **BLOCKED — waiting on others**: everything actionable is done; you're waiting on CI to finish or a reviewer to look again. Report the specific wait and tell the user to either re-invoke this skill later or wrap it with `/loop <interval> /land-pr <PR>` for periodic unattended re-checks.
- **BLOCKED — human decision needed**: one or more disagreement/ambiguous threads, or a CI failure that exceeded the retry cap. List each with your reasoning so the user can decide.

Before reporting the verdict, write the checkpoint file to `.tmp/land-pr-checkpoint.json`:

```json
{
  "pr": "<PR URL or number>",
  "pass_number": <current pass number>,
  "timestamp": "<ISO 8601>",
  "resolved_threads": ["<thread IDs resolved so far>"],
  "green_checks": ["<check names currently green>"],
  "failed_fixes": [
    {
      "target": "<thread ID or check name>",
      "pass": <pass number>,
      "approach": "<one-line description of what was tried>",
      "result": "<why it didn't work>"
    }
  ],
  "outstanding_threads": ["<thread IDs still unresolved>"],
  "outstanding_checks": ["<check names still failing>"],
  "context_files_loaded": ["<paths of project context files loaded in Phase 0>"]
}
```

This file serves double duty:
- Cross-session state for `/loop` re-invocations (context window starts fresh).
- Pass counter for the max-pass cap.

Complete when one of these four states is reported with concrete evidence for each open item.

---

## Phase 9: Report

Present:

```
LAND PR — {PR title}
{PR URL}

Verdict: {READY TO MERGE / BLOCKED}
Pass:        {current pass number}/4

Branch:      {up to date / N commits behind default, now merged/rebased}
Threads:     {resolved}/{total} resolved
CI:          {passing checks}/{required checks} green
Approval:    {required reviewer(s)} — {state/vote}

Outstanding:
- {each blocker, with why and, if applicable, what you tried}

Next step: {merge yourself when ready / re-run this skill / wrap with /loop / decide on the listed items}
```

After reporting the verdict:

- If the verdict is **READY TO MERGE**: delete `.tmp/land-pr-checkpoint.json` and
  `.tmp/land-pr-context/` (if it exists) in addition to `context_dir`. These are no longer
  needed once the PR is merge-ready.
- If the verdict is **BLOCKED**: do NOT delete the checkpoint — it is needed for the next pass.

Delete only the resolved `context_dir` if it exists; never remove `session_context` or
`context_root`. Use the absolute path with
`Remove-Item -LiteralPath $context_dir -Recurse -Force` in PowerShell or
`rm -rf -- "$context_dir"` in bash, and do not fail if it is already absent.
