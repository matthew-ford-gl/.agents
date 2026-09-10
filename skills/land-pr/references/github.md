# GitHub — Platform-Specific Steps

Read this file when Phase 1 (in `SKILL.md`) determines `platform = github`.

Prefer MCP server `devin/github-mcp-server` when available; `gh`/`gh api` commands below are
the CLI fallback and are what to reach for directly in Claude Code.

## Resolving a bare PR number (Phase 1)

`gh pr view <number> --json url,headRefName,baseRefName,title,body,reviews,statusCheckRollup,mergeable,mergeStateStatus,files`
to get the full identifiers, metadata, review states, and check rollup in one call. Reuse this
single output across Phases 1-4 instead of calling `gh pr view` repeatedly.

## Phase 2/3: Checkout and sync

- Reuse the invocation checkout. Read `headRefName` from PR metadata, fetch only the required
  remote ref, and switch the current checkout with `git switch` as specified by `land-pr` Phase 2.
  Do not use `gh pr checkout`; the branch switch must happen directly in the invocation checkout.
- Syncing is handled by `land-pr` Phase 3 of `SKILL.md`.

## Conflict detection (Phase 3)

The `mergeable` and `mergeStateStatus` fields from the `gh pr view` JSON above indicate
actual merge conflicts. The PR reports conflicts when `mergeStateStatus == "DIRTY"` or
`mergeable == "CONFLICTING"`.

## Phase 4: Fetch full review state

- Reuse the `gh pr view` output from Phase 1 for metadata, review states, and check rollup.
  Do not fetch it a second time.
- Fetch `gh pr diff <number>` only when an actionable thread or completed failing check requires code inspection.
- Review threads with resolved status are **not** exposed by REST; use GraphQL, then keep only
  unresolved threads unless the checkpoint shows a previously resolved thread may have new comments:
  ```
  gh api graphql -f query='
    query($owner:String!,$repo:String!,$num:Int!){
      repository(owner:$owner,name:$repo){
        pullRequest(number:$num){
          reviewThreads(first:100){
            nodes{ id isResolved comments(first:10){ nodes{ id body author{login} } pageInfo{ hasNextPage endCursor } } }
          }
        }
      }
    }' -f owner=<owner> -f repo=<repo> -F num=<number>
  ```
- Required reviewers/branch protection: `gh api repos/{owner}/{repo}/branches/{branch}/protection`
  (needs the actual base branch name from Phase 1).
- CI check runs: `gh pr checks <number>`. Capture the current snapshot once; do not add `--watch`
  and do not query queued or running checks again during the invocation.

## Phase 5: Replying to and resolving threads

- Reply to a specific review comment: `gh api repos/{owner}/{repo}/pulls/{num}/comments/{comment_id}/replies -f body="..."`.
- General (non-inline) PR comment: `gh pr comment <number> --body "..."`.
- Resolve a review thread (GitHub only exposes this via GraphQL):
  ```
  gh api graphql -f query='mutation($id:ID!){ resolveReviewThread(input:{threadId:$id}){ thread{ isResolved } } }' -f id=<threadId>
  ```

## Phase 6: CI investigation and requeue

Apply the required-reviewer approval gate in `SKILL.md` before using either rerun command for an expired build.

- List runs for the branch: `gh run list --branch <branch> --json databaseId,status,conclusion,name`.
- Logs for a completed failed run: `gh run view <run-id> --log-failed`. Before staging them,
  apply `SKILL.md`'s per-check 400-line/40-KiB redacted excerpt cap; never retain whole-run output.
- Rerun only failed jobs of a completed failed/expired run: `gh run rerun <run-id> --failed`.
  If the whole run needs a fresh attempt: `gh run rerun <run-id>`.
- Never create an empty commit or re-push merely for a queued/running check. Record that state
  from the single snapshot and stop.

## Approval state

- `gh pr view <number> --json reviews` — each entry has `state` (`APPROVED`, `CHANGES_REQUESTED`,
  `COMMENTED`, `DISMISSED`). GitHub has no partial-approval state, so `APPROVED` from every
  required reviewer (per branch protection) is sufficient.
- Note whether branch protection has "Dismiss stale reviews on push" enabled — if so, a push in
  Phase 5/6 already invalidated prior approvals; re-check `reviews` after any push.
