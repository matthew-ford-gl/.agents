---
name: update-ado-pr
description: "Updates the title, Markdown description, draft state, reviewers, or linked work items of an existing Azure DevOps pull request by using Azure CLI safely. Use when explicitly asked to edit, revise, or add metadata to an ADO PR. Not for: creating, reviewing, abandoning, completing, merging, or enabling auto-complete on pull requests."
argument-hint: "<PR ID> [title/description/draft/reviewers/work items]"
model: swe
---

# Update Azure DevOps PR

Task: `$ARGUMENTS`

Invocation authorizes only the previewed metadata changes to one existing Azure DevOps pull request. It does not authorize changing status, enabling auto-complete, bypassing policies, altering merge settings, pushing branches, or merging.

## Phase 1: Resolve and inspect the PR

1. Read repository instructions and run `git remote get-url origin` plus `az repos pr show --id <id> --org <org-url> --output json`.
2. Resolve the PR ID from `$ARGUMENTS`; ask if it is absent or ambiguous. Confirm the origin and PR belong to Azure DevOps and resolve the organization URL from the remote or configured defaults.
3. Record the current title, description, draft state, reviewers, linked work items, status, source, target, repository, and URL.
4. Stop if the PR is not active. Route requests to create, abandon, complete, merge, enable auto-complete, bypass policy, or alter merge behavior to a more appropriate workflow.

Complete when one active PR and its current metadata are explicit.

## Phase 2: Build the requested patch

1. Translate only explicitly requested changes into a patch. Do not rewrite unchanged content for style alone.
2. For a description update, write the exact proposed Markdown to a temporary UTF-8 file outside the repository. Preserve meaningful existing sections unless the user asked to replace them.
3. Resolve reviewers to identities accepted by Azure DevOps. Mark them required only when explicitly requested.
4. Link only work-item IDs supplied by the user or authoritative task context; never infer IDs from unrelated numbers.
5. Show the before/after values and additions. Ask for confirmation if content, draft state, reviewer identity, required status, or work-item IDs were inferred.

Complete when at least one concrete change exists and the preview has no placeholders or unsupported claims.

## Phase 3: Validate and execute

Resolve Python 3 and run the bundled wrapper without `--execute`:

```text
<python> <skill-dir>/scripts/update_ado_pr.py --org <org-url> --id <pr-id> [--title <title>] [--description-file <file>] [--draft true|false] [--reviewer <identity> ...] [--required-reviewer <identity> ...] [--work-item <id> ...]
```

Inspect the JSON preview. Proceed only when every command targets the same organization and PR, the first command is `az repos pr update` when core metadata changes, and no command contains status, auto-complete, bypass-policy, merge, squash, or source-branch deletion options. Then append `--execute` and rerun it.

The wrapper applies commands sequentially. If a later reviewer or work-item command fails, stop and report both the successful earlier changes and the failed command; do not claim rollback or retry with broader permissions. On authentication failure, ask the user to authenticate.

Complete when all previewed commands succeed or an exact partial-update boundary is reported.

## Phase 4: Verify and report

Query the PR again with `az repos pr show`, plus reviewer and linked-work-item list commands when those changed. Compare the returned metadata with the preview, report the PR ID and URL and each verified change, then remove temporary files created by this invocation.

Complete when every requested change is verified or any mismatch is explicitly reported.
