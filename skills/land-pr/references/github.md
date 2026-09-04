# GitHub — Platform-Specific Steps

Read this file when Phase 1 (in `SKILL.md`) determines `platform = github`.

Prefer MCP server `devin/github-mcp-server` when available; `gh`/`gh api` commands below are
the CLI fallback and are what to reach for directly in Claude Code.

## Resolving a bare PR number (Phase 1)

`gh pr view <number> --json url,headRefName,baseRefName` to get the full identifiers.

## Phase 2/3: Checkout and sync

- `gh pr checkout <number>` checks out the PR's head branch locally.
- Bringing the branch up to date is handled by `merge-default-branch` (Phase 3 of `SKILL.md`).

## Phase 4: Fetch full review state

- `gh pr view <number> --json title,body,url,reviews,statusCheckRollup,mergeable,files` for
  metadata, review states, and check rollup.
- `gh pr diff <number>` for the full diff.
- Review threads with resolved status are **not** exposed by REST; use GraphQL:
  ```
  gh api graphql -f query='
    query($owner:String!,$repo:String!,$num:Int!){
      repository(owner:$owner,name:$repo){
        pullRequest(number:$num){
          reviewThreads(first:100){
            nodes{ id isResolved comments(first:50){ nodes{ id body author{login} } } }
          }
        }
      }
    }' -f owner=<owner> -f repo=<repo> -F num=<number>
  ```
- Required reviewers/branch protection: `gh api repos/{owner}/{repo}/branches/{branch}/protection`
  (needs the actual base branch name from Phase 1).
- CI check runs: `gh pr checks <number>` (add `--watch` to block until all finish, useful for
  the bounded poll in Phase 6).

## Phase 5: Replying to and resolving threads

- Reply to a specific review comment: `gh api repos/{owner}/{repo}/pulls/{num}/comments/{comment_id}/replies -f body="..."`.
- General (non-inline) PR comment: `gh pr comment <number> --body "..."`.
- Resolve a review thread (GitHub only exposes this via GraphQL):
  ```
  gh api graphql -f query='mutation($id:ID!){ resolveReviewThread(input:{threadId:$id}){ thread{ isResolved } } }' -f id=<threadId>
  ```

## Phase 6: CI investigation and requeue

- List runs for the branch: `gh run list --branch <branch> --json databaseId,status,conclusion,name`.
- Logs for a failed run: `gh run view <run-id> --log-failed`.
- Rerun only the failed jobs of a run (covers both "failed" and "expired/timed out" runs):
  `gh run rerun <run-id> --failed`. If the whole run needs a fresh attempt: `gh run rerun <run-id>`.
- If a check has no rerunnable run at all (e.g. never triggered / stuck queued), an empty
  commit or a re-push is the fallback: `git commit --allow-empty -m "chore: retrigger checks"`.

## Phase 7: Approval

- `gh pr view <number> --json reviews` — each entry has `state` (`APPROVED`, `CHANGES_REQUESTED`,
  `COMMENTED`, `DISMISSED`). GitHub has no partial-approval state, so `APPROVED` from every
  required reviewer (per branch protection) is sufficient.
- Note whether branch protection has "Dismiss stale reviews on push" enabled — if so, a push in
  Phase 5/6 already invalidated prior approvals; re-check `reviews` after any push.
