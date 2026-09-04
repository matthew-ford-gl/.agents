# Azure DevOps — Platform-Specific Steps

Read this file when Phase 1 (in `SKILL.md`) determines `platform = ado` — the PR URL
matches `dev.azure.com/{org}/{project}/_git/{repo}/pullrequest/{id}` or
`{org}.visualstudio.com/{project}/_git/{repo}/pullrequest/{id}`.

## Phase 2: Fetch PR Details

1. Call `repo_pull_request` (action: `get`, `includeWorkItemRefs: true`,
   `includeChangedFiles: true`) via MCP server `azure-devops` to get the PR title,
   description, linked work item IDs, and changed files.
2. Call `repo_pull_request` (action: `get`) again without extra flags if needed for the
   diff content — or use `az repos pr diff` CLI as a fallback.

## Phase 3: Fetch Requirements Context

For each linked work item ID found in Phase 2:
- Call `wit_work_item` (action: `get`, `expand: Relations`) via `azure-devops` to get
  the work item title, description, acceptance criteria, state, and relations.
- For parent work items (e.g. a Task's parent User Story), follow one level up to get
  the broader context and acceptance criteria.

## Phase 7: Post Comments

Use `repo_pull_request_thread_write` to create a comment thread for each finding with the
appropriate file path and line position. Set thread status to `Active` for CRITICAL/MAJOR
findings and `Closed` for MINOR (nit) findings.
