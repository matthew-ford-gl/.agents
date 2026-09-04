# GitHub — Platform-Specific Steps

Read this file when Phase 1 (in `SKILL.md`) determines `platform = github` — the PR URL
matches `github.com/{owner}/{repo}/pull/{number}`.

## Phase 2: Fetch PR Details

1. Call `pull_request_read` (method: `get`) via MCP server `devin/github-mcp-server` to get
   the PR title, description/body, and linked issue references.
2. Parse the PR body for issue references (`#123`, `Fixes #123`, `Closes #123`,
   `https://github.com/{owner}/{repo}/issues/{n}`).
3. Call `pull_request_read` (method: `get_diff`) to get the full diff.
4. Call `pull_request_read` (method: `get_files`) to get the list of changed files.

## Phase 3: Fetch Requirements Context

For each linked issue number found in Phase 2:
- Call `issue_read` (method: `get`) via `devin/github-mcp-server` to get the issue title,
  body, labels, and state.
- If the issue body references other issues or specs, follow one level deep.

## Phase 7: Post Comments

Use `pull_request_review_write` (method: `create`) to create a pending review, then
`add_comment_to_pending_review` for each finding that has a specific file:line location,
then `pull_request_review_write` (method: `submit_pending`) with event `COMMENT` (if PASS)
or `REQUEST_CHANGES` (if FAIL). For findings without a specific line, include them in the
review body summary.
