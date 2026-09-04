# Azure DevOps — Platform-Specific Steps

Read this file when Phase 1 (in `SKILL.md`) determines `platform = ado`.

Prefer MCP server `azure-devops` when available; `az` / `az rest` commands below are the CLI
fallback and are what to reach for directly in Claude Code. All REST calls need
`api-version=7.1` (or the org's supported version) and org/project/repo scoped to the PR.

## Resolving a bare PR number (Phase 1)

`az repos pr show --id <number> -o json` returns `repository.project.name`, `repository.name`,
`sourceRefName`, `targetRefName`, and the org can be read from the configured `az devops`
defaults or `git remote get-url origin`.

## Phase 2/3: Checkout and sync

No single `az` command checks out a PR branch. Get `sourceRefName` from `az repos pr show`,
then `git fetch origin <sourceRefName>:<local-branch>` and `git checkout <local-branch>`.
Bringing the branch up to date is handled by `merge-default-branch` (Phase 3 of `SKILL.md`).

## Phase 4: Fetch full review state

- `az repos pr show --id <id> -o json` for metadata, `reviewers` (each with `vote` and
  `isRequired`), and `sourceRefName`/`targetRefName`.
- Diff: `az repos pr diff` is not a standard command — use
  `git diff <targetRefName>...<sourceRefName>` locally after fetching both refs.
- Comment threads (not exposed by `az repos pr show`):
  ```
  az rest --method get \
    --url "https://dev.azure.com/{org}/{project}/_apis/git/repositories/{repo}/pullRequests/{id}/threads?api-version=7.1"
  ```
  Each thread has `id`, `status` (`active`, `fixed`, `wontFix`, `closed`, `pending`, `unknown`),
  and a `comments` array. Treat `active`/`pending` as unresolved.
- Build validation / required policies:
  ```
  az rest --method get \
    --url "https://dev.azure.com/{org}/{project}/_apis/git/repositories/{repo}/pullRequests/{id}/policyEvaluations?api-version=7.1"
  ```
  Each evaluation has `status` (`approved`, `running`, `queued`, `rejected`, `broken`,
  `notApplicable`) and, for build policies, a `context` payload containing the `buildId`.

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
- Logs: `az pipelines build show --id <buildId>` for status, or the web UI link in the same
  response, for the failing task's log.

## Phase 7: Approval

`az repos pr show --id <id> -o json` → `reviewers[]`. Vote values: `10` = Approved,
`5` = Approved with suggestions, `0` = No vote, `-5` = Waiting for author, `-10` = Rejected.

Per `SKILL.md` Phase 7, only `10` counts as a full approval — `5` must be treated as not yet
approved. Identify which reviewer(s) are required from `isRequired` on each entry, or from the
branch policy configuration, or from the user's stated required reviewer/group.

Check whether the branch policy has "reset code reviewer votes when there are new changes"
enabled — if so, a push in Phase 5/6 already reset every vote to `0`, and reviewers must
re-review from scratch.
