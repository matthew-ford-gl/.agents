---
name: merge-default-branch
description: "Merges the remote default branch into the current feature branch, delegates reported conflicts for intent-based resolution, validates the integration, and pushes the current branch. Use when asked to update, sync, or bring main/master into the current branch and push it. Not for: rebasing, merging a pull request, updating the default branch itself, or an already-conflicted merge/rebase."
argument-hint: "<optional remote or default-branch override>"
disable-model-invocation: true
---

# Merge Default Branch

Task context: $ARGUMENTS

This is a user-invoked workflow because it fetches remote state, creates a normal merge commit when needed, and pushes. The invocation authorizes completing that merge commit and normally pushing the resulting current branch, but not force-pushing, history rewriting, discarding changes, or changing another branch.

## 1. Establish the target and safe state

Read repository and affected-path instructions, including `AGENTS.md`, other agent-memory or instruction files that apply to the repository or changed paths (for example `CLAUDE.md` or a directory-scoped equivalent), and documented validation commands.

Record the repository root, current branch, `HEAD`, worktree status, remotes, upstream, and any in-progress Git operation. Stop when outside a Git repository, on detached `HEAD`, on the remote default branch itself, or when a merge, rebase, cherry-pick, revert, or bisect is already active. If that active operation has unresolved merge or rebase paths, hand off to `resolving-merge-conflicts` as a separate workflow; never start this workflow around an existing operation.

Require a clean index and worktree, including no untracked paths that the merge could overwrite. Ask the user to commit, stash, or otherwise handle local work. Never stash, discard, reset, abort, or check out over changes automatically.

Completion: the original target branch and `HEAD` are recorded, no other Git operation is active, and the worktree is clean.

## 2. Discover and fetch the default branch

Select the remote from an explicit argument, otherwise the current branch's upstream remote, otherwise `origin` when it exists, otherwise the sole configured remote. Ask when multiple plausible remotes remain.

Discover the remote default branch from the remote's symbolic `HEAD`, using the local remote-HEAD ref, remote metadata, or a symbolic-ref query to the remote. Do not infer it solely from the names `main` or `master`. Apply an explicit branch override only after confirming that branch exists on the selected remote.

Fetch the selected remote without pruning, deleting refs, updating unrelated local branches, or changing the checked-out branch. Stop on authentication, authorization, network, or missing-ref failures.

Completion: `<remote>/<default>` exists as a freshly fetched remote-tracking ref and the checked-out branch still equals the recorded target branch.

## 3. Merge into the current branch

Merge `<remote>/<default>` into the current target branch using the repository's documented merge policy. Do not rebase, squash, use `ours`/`theirs` as a blanket strategy, allow unrelated histories, or bypass hooks unless the user separately approves that exact action.

If Git reports conflicts, invoke `resolving-merge-conflicts` with the target branch, fetched source ref, merge context, and the user's existing authorization to complete this merge commit. Let that skill own hunk-by-hunk intent tracing, ambiguity stops, staging of resolved paths, and conflict verification. Return here only after it reports zero unresolved paths or a blocker. Do not duplicate its resolution heuristics in this skill.

If the merge is already up to date, continue without creating an empty commit. Otherwise complete the merge commit using the repository's normal hooks and message conventions. If Git needs interactive input that the host cannot safely provide, stop and report the required decision.

Completion: Git reports no unresolved index entries, the merge operation is complete, and `<remote>/<default>` is an ancestor of `HEAD`.

## 4. Validate the integrated result

Run the repository-required validation discovered from rules and CI, using narrow relevant checks first and then the required project gate. Fix only failures caused by the integration; report unrelated or pre-existing failures separately. Do not push while a required check is failing or unavailable. To proceed without it, present the exact skipped or failing check and consequence, then obtain explicit user acceptance for that limitation.

Review the final diff and recent graph for accidental changes, generated-file drift, conflict markers in resolved files, and inclusion of unrelated paths. Confirm again that the checked-out branch is the recorded target branch, the worktree is clean, and the source default ref remains an ancestor of `HEAD`.

Completion: required checks pass, or the user explicitly accepts each reported limitation, and the final branch state is internally consistent.

## 5. Push the target branch

Push the recorded current branch to its configured upstream with a normal push. If no upstream exists, present the exact proposed `<remote>/<branch>` destination and ask before setting it. Never push the default branch, tags, all branches, or unrelated refs.

Stop on a non-fast-forward rejection. Report the divergent remote feature branch and ask the user how to reconcile it. Do not force-push, pull-rebase, merge the remote feature branch, or rewrite history without a separate user decision.

Report the target branch, merged source ref and commit, conflict paths and intent decisions when applicable, validation results, resulting commit, and remote push destination.

Completion: the normal push succeeds and the remote target branch points to the resulting local `HEAD`, or the exact blocker is reported with the local merge preserved.
