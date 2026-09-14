---
name: create-ado-pr
description: "Creates a well-formed Azure DevOps pull request with reviewed title, Markdown description, source/target branches, and repository coordinates by using Azure CLI safely. Use when explicitly asked to create, open, or raise a new PR in Azure DevOps. Not for: GitHub PRs, reviewing or updating an existing PR, pushing branches, completing or merging PRs."
argument-hint: "[source branch] [target branch] [optional title/work items]"
---

# Create Azure DevOps PR

Task: `$ARGUMENTS`

Invocation authorizes creating one Azure DevOps pull request after its content and coordinates have been shown to the user. It does not authorize pushing, rewriting history, bypassing policies, enabling auto-complete, completing the PR, or creating a duplicate.

## Phase 1: Establish repository state

1. Read repository instructions (`AGENTS.md`, `CLAUDE.md`, and applicable linked context).
2. Run `git status --short --branch`, `git remote get-url origin`, `git branch --show-current`, and `git log --oneline --decorate -10`.
3. Confirm the origin is Azure DevOps and resolve the source branch from `$ARGUMENTS` or the current branch. Resolve the target from `$ARGUMENTS`, repository instructions, or the remote default branch; do not assume `main` when it can be inspected.
4. Verify the source differs from the target and has a remote ref. If it is not pushed, stop and ask whether to push it; do not push as part of this skill.
5. Resolve organization, project, and repository from the origin URL. Use `az devops configure --list` only to fill missing values, and ask for any value that remains ambiguous.

Complete when organization URL, project, repository, source branch, and target branch are explicit and the source exists remotely.

## Phase 2: Check for an existing PR

Run a bounded query for active PRs with this source and target:

```text
az repos pr list --org <org-url> --project <project> --repository <repository> --source-branch <source> --target-branch <target> --status active --output json
```

If a matching PR exists, stop and report its ID and URL. Do not create a duplicate.

Complete when no active matching PR exists, or the existing PR has been reported and execution has stopped.

## Phase 3: Build the PR content

Inspect `git diff <target-remote-ref>...<source-remote-ref> --stat`, the commit list in that range, and any task/issue context supplied by the user. Draft:

- **Title:** imperative or outcome-focused, specific, and normally under 72 characters.
- **Description:** valid Markdown with `## Summary` containing 1–3 concrete bullets and `## Test plan` containing checked or unchecked items that reflect commands actually run or explicitly remain outstanding.
- **Work items:** include IDs only when supplied by the user or unambiguously present in authoritative task context; never infer an ID from unrelated numbers.

Do not add generated-by attribution unless repository instructions require it. Do not claim tests passed unless their successful output was observed in this session or supplied as trusted evidence.

Write the description to a temporary UTF-8 file outside the repository. Show the exact title, description, coordinates, and work-item IDs to the user. Ask for confirmation if any content or coordinate was inferred rather than explicitly supplied; otherwise the explicit invocation is sufficient authorization to proceed.

Complete when the PR preview contains no placeholders, unsupported claims, or ambiguous coordinates and any required confirmation has been received.

## Phase 4: Validate and create with Azure CLI

Resolve Python 3 as `python3`, `python`, or `py -3`. Run the bundled wrapper without `--execute` first:

```text
<python> <skill-dir>/scripts/create_ado_pr.py --org <org-url> --project <project> --repository <repository> --source <source> --target <target> --title <title> --description-file <temp-file> [--work-item <id> ...]
```

Inspect its JSON preview. Proceed only when `command[0:4]` is `az repos pr create`, all coordinates match Phase 1, and `description_sha256` identifies the previewed file. Then rerun the same command with `--execute` appended. Never replace the wrapper with shell interpolation of multiline Markdown.

If Azure CLI reports authentication failure, stop and ask the user to authenticate. For any other error, report the command's stderr without retrying with broader permissions, policy bypass, or altered coordinates.

Complete when Azure CLI returns a created PR object, or a specific blocker has been reported without creating a partial or duplicate PR.

## Phase 5: Verify and report

From the creation response, report the PR ID, title, source and target, repository, and web URL. Query that PR once with `az repos pr show` and verify those fields match the preview. Remove the temporary description file created by this invocation.

Complete when the created PR is verified against the preview and its ID and URL have been reported.
