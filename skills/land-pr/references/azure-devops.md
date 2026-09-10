# Azure DevOps — Platform-Specific Steps

Read this file when Phase 1 (in `SKILL.md`) determines `platform = ado`.

Use `scripts/snapshot.py ado` as the authoritative read path. It executes the supported Azure CLI
commands with API version 7.1 and emits only decision fields. Do not list MCP tools, inspect CLI help,
change Azure defaults, try alternate URL encodings, or substitute broad `az rest` responses.

## Resolving a bare PR number (Phase 1)

`az repos pr show --id <number> -o json` is the single metadata source. It returns repository and
project IDs, source/target refs, commits, merge status, and reviewers. The snapshot script uses those
IDs for every subsequent command.

## Phase 2/3: Checkout and sync

Get `sourceRefName` from `az repos pr show`, fetch only that ref into a remote-tracking ref, then
switch the invocation checkout with `git switch` as specified by `land-pr` Phase 2. Do not create
or enter another worktree or clone. Bringing the branch up to date is handled by `land-pr` Phase 3.

## Conflict detection (Phase 3)

`az repos pr show --id <id> -o json` returns `mergeStatus` in the `PullRequestAsyncStatus`
enum. The PR reports actual merge conflicts when `mergeStatus` is `"conflicts"`.

## Phase 4: Fetch full review state

The snapshot already contains metadata, active/pending text threads, policy classifications,
reviewers, latest iteration, and changed paths. Reuse it. If the script failed after metadata,
use these exact fallbacks once with IDs from that metadata:

- Threads: `az devops invoke --area git --resource pullRequestThreads --route-parameters project=<project-id> repositoryId=<repo-id> pullRequestId=<id> --api-version 7.1 -o json`
- Policies: `az repos pr policy list --id <id> -o json`
- Iterations: `az devops invoke --area git --resource pullRequestIterations --route-parameters project=<project-id> repositoryId=<repo-id> pullRequestId=<id> --api-version 7.1 -o json`
- Latest changes: use `pullRequestIterationChanges` with the same route plus `iterationId=<latest>`.

Project only active/pending text threads and policy decision fields before returning output to the
model. Generate a local diff only after an actionable item proves it necessary.

## Phase 5: Replying to and resolving threads

- Reply on an existing thread:
  ```
  az rest --method post \
    --url ".../pullRequests/{id}/threads/{threadId}/comments?api-version=7.1" \
    --body '{"content":"..."}'
  ```
- Resolve a thread by setting its status to `fixed` (the vote/UI equivalent of "Resolved"):
  ```
  az rest --method patch \
    --url ".../pullRequests/{id}/threads/{threadId}?api-version=7.1" \
    --body '{"status":"fixed"}'
  ```
  Use `"wontFix"` instead if you're explicitly declining a suggestion — but per `SKILL.md`
  Phase 5, only do that for a disagreement you've replied to and flagged as a blocker, never
  silently.

## Phase 6: CI investigation and requeue

Apply the required-reviewer approval gate in `SKILL.md` before retrying or freshly queueing an expired build.

- Get the `buildId` for a failing/expired build policy from its `policyEvaluations` `context`.
- Retry (rerun failed jobs of) the same build:
  ```
  az rest --method post --url ".../_apis/build/builds/{buildId}?retry=true&api-version=7.1"
  ```
- If the build has no retryable state (fully expired, or the definition needs a fresh queue),
  queue a brand-new build against the PR's source branch instead:
  ```
  az pipelines build queue --definition-id <defId> --branch <sourceRefName> --org <org> --project <project>
  ```
  Find `<defId>` from the same `policyEvaluations` context or `az pipelines build show --id <buildId>`.
- Retrieve logs only for a completed unsuccessful build, selecting the failing task rather than
  the entire build. Before staging output, apply `SKILL.md`'s per-check 400-line/40-KiB redacted
  excerpt cap. `az pipelines build show --id <buildId>` provides status and the log/UI metadata.

## Approval state

`az repos pr show --id <id> -o json` → `reviewers[]`. Vote values: `10` = Approved,
`5` = Approved with suggestions, `0` = No vote, `-5` = Waiting for author, `-10` = Rejected.

Per `SKILL.md` Phase 7, only `10` counts as a full approval — `5` must be treated as not yet
approved. Identify which reviewer(s) are required from `isRequired` on each entry, or from the
branch policy configuration, or from the user's stated required reviewer/group.

Check whether the branch policy has "reset code reviewer votes when there are new changes"
enabled — if so, a push in Phase 5/6 already reset every vote to `0`, and reviewers must
re-review from scratch.
