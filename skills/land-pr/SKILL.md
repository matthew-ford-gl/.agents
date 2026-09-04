---
name: land-pr
description: "Takes a PR number or URL (GitHub or Azure DevOps), brings the branch up to date with the default branch, resolves every open review thread with a code fix or reply, investigates and fixes failing CI checks, requeues expired or stale builds, and repeats until every thread is resolved, CI is green, and the required reviewer's vote is a full approval — not 'approved with suggestions'. Stops short of merging. Use when asked to get a PR ready to merge, babysit a PR, drive PR feedback and CI failures to zero, or land/finish a PR end-to-end. Not for: opening a brand-new PR (use ship), a one-off static compliance review with no fix loop (use review-pr), or merging/completing the PR itself (always left to the user)."
argument-hint: "<PR number or URL (GitHub or Azure DevOps)>"
disable-model-invocation: true
---

# Land PR

Task: $ARGUMENTS

This is a user-invoked workflow because it commits, pushes, replies to and resolves PR review
threads, and requeues CI builds. Explicit invocation authorizes all of that on the PR's own
branch. It never authorizes force-pushing the default branch, rewriting history other
collaborators may have already based work on without confirmation, or merging/completing the
PR — that last step always belongs to the user.

Repeat Phases 4-8 each time you're invoked (this skill is idempotent: it re-reads current state
rather than assuming anything from a previous pass). For long unattended monitoring beyond a
single pass, tell the user to wrap this skill with `/loop`, e.g. `/loop 10m /land-pr <PR>`,
rather than sleeping inside one invocation for hours.

---

## Phase 0: Load project context

1. Read the repository root `AGENTS.md` and any nearer `AGENTS.md` for paths the PR touches. Treat repository instructions as mandatory.
2. If `.claude/CLAUDE.md` (or repo-root `CLAUDE.md`) exists, read it — including branch/merge policy (rebase vs merge commit, force-push rules) and commit-attribution convention.
3. If `.context/index.md` exists, load any entries matching the PR's domain.

Complete when applicable instruction files are loaded.

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

Record the repository root, current branch, and worktree status. Require a clean index and worktree — no uncommitted changes, no untracked paths that a checkout could overwrite. If dirty, stop and ask the user to commit or stash first; never stash or discard automatically.

Check out the PR's source branch locally (`gh pr checkout <number>`, or for ADO fetch the source branch named in `az repos pr show` and check it out). Stop if the checkout would overwrite local work.

Complete when the PR's source branch is checked out locally with a clean worktree.

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

---

## Phase 5: Resolve every open comment thread

For each thread that is not already resolved:

1. **Classify** it: a concrete actionable code-change request, a question/discussion, a nit, or a point you disagree with.
2. **Actionable**: implement the fix. Commit with a message describing the fix (see attribution rule below). Reply on the thread summarising what changed and referencing the commit. Resolve the thread.
3. **Question/nit** you can satisfy by inspection or a trivial change: answer or fix, reply, resolve.
4. **Disagreement or genuinely ambiguous request**: reply with your reasoning, but **do not resolve the thread** — leave it open and record it as a human-decision blocker for the final report. Never resolve a thread you're not confident is actually addressed.

Commit-attribution convention: if the repository's or user's global instructions specify one, use it exactly. Otherwise use a generic `Generated with [tool name]` line with a matching `Co-Authored-By:` for your own host/runtime — never hardcode another runtime's convention.

After all fixable threads are handled, run the project's build/lint/test commands (from `AGENTS.md` or standard tooling) before pushing. Push commits normally (no force) to the PR branch.

Complete when every thread is either resolved-with-a-reply or explicitly recorded as a human-decision blocker, and any resulting commits are pushed.

---

## Phase 6: Investigate and fix CI

For every required check/policy that is not green:

- **Expired or stale** (timed out waiting to run, or a merge-policy build that expired): requeue it using the matching reference file's commands.
- **Failed**: pull its logs. Classify the failure the way `test-failure-triager` classifies test failures — production bug, test bug, flake, or infrastructure/environment issue — using actual evidence (logs, the diff, re-running in isolation), not a guess. Fix the root cause (code, test, or config), commit, and push. Track attempts per distinct check; after 3 failed fix attempts on the same check, stop trying and record it as a blocker with what you tried and why it didn't resolve.
- **Pending/running**: poll with backoff (e.g. every 1-2 minutes) for up to roughly 10-15 minutes this pass. If it's still not finished after that, stop polling and report it as "in progress" rather than blocking the session further — recommend `/loop` for continued unattended checking.

Re-run the changed check(s) after any fix and confirm before moving on.

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

Complete when one of these four states is reported with concrete evidence for each open item.

---

## Phase 9: Report

Present:

```
LAND PR — {PR title}
{PR URL}

Verdict: {READY TO MERGE / BLOCKED}

Branch:      {up to date / N commits behind default, now merged/rebased}
Threads:     {resolved}/{total} resolved
CI:          {passing checks}/{required checks} green
Approval:    {required reviewer(s)} — {state/vote}

Outstanding:
- {each blocker, with why and, if applicable, what you tried}

Next step: {merge yourself when ready / re-run this skill / wrap with /loop / decide on the listed items}
```
