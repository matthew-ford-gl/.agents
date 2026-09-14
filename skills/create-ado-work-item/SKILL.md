---
name: create-ado-work-item
description: "Creates a well-formed Azure DevOps work item with reviewed title, type, description, acceptance criteria or custom fields, classification paths, assignment, and optional parent relation by using Azure CLI safely. Use when explicitly asked to create, file, or raise an ADO bug, story, task, or other work item. Not for: GitHub issues, updating existing work items, bulk imports, deleting items, or changing project process configuration."
argument-hint: "<type> <title> [description/fields/parent]"
model: swe
---

# Create Azure DevOps Work Item

Task: `$ARGUMENTS`

Invocation authorizes creating one previewed work item and, when explicitly requested, linking it to one parent. It does not authorize changing project configuration, creating missing users or classification paths, bulk creation, or modifying existing work items.

## Phase 1: Resolve project conventions

1. Read repository instructions and inspect `git remote get-url origin` plus `az devops configure --list`.
2. Confirm the target is Azure DevOps. Resolve organization and project from `$ARGUMENTS`, the remote, or configured defaults; ask when ambiguity remains.
3. Resolve the exact work-item type from the user's request and the types available to the project. Do not silently substitute Bug, User Story, Product Backlog Item, Task, or another process-specific type.
4. When area, iteration, assignee, state, custom fields, or a parent are requested, validate that their identifiers or paths exist before creation.

Complete when the organization, project, exact type, and all requested project-specific values are valid and explicit.

## Phase 2: Draft and check content

1. Draft a concise, outcome-focused title and a description grounded only in supplied context.
2. Include reproduction steps, expected/actual behavior, acceptance criteria, or implementation notes only when appropriate and supported. Do not invent environment details, severity, business impact, test results, or acceptance criteria.
3. Put description and discussion content in separate temporary UTF-8 files outside the repository. Pass process-specific fields such as acceptance criteria as explicit `reference-name=value` entries after confirming the field exists for this work-item type.
4. Run a bounded WIQL title search in the target project for active, recent likely duplicates. If a likely duplicate exists, stop and show it unless the user explicitly confirms a distinct item is needed.
5. Show the exact type, title, content, fields, paths, assignee, and parent. Ask for confirmation if any substantive value was inferred rather than supplied.

Complete when the preview has no placeholders, unsupported claims, invalid fields, or unresolved likely duplicate.

## Phase 3: Validate and create

Resolve Python 3 and run the bundled wrapper without `--execute`:

```text
<python> <skill-dir>/scripts/create_ado_work_item.py --org <org-url> --project <project> --type <type> --title <title> [--description-file <file>] [--discussion-file <file>] [--area <path>] [--iteration <path>] [--assigned-to <identity>] [--field <reference-name=value> ...] [--parent <id>]
```

Inspect the JSON preview. Proceed only when the first command is `az boards work-item create`, all values match the reviewed preview, file hashes identify the reviewed content, and custom fields remain separate arguments. Then append `--execute` and rerun it. Never interpolate multiline content or field arrays through a shell.

If a parent was requested, the wrapper creates the item before adding the relation. If relation creation fails, the item still exists: stop, report its ID and the failed parent link, and do not create a replacement. On authentication failure, ask the user to authenticate.

Complete when Azure CLI returns one created item, or the exact partial-creation boundary is reported.

## Phase 4: Verify and report

Query the returned ID with `az boards work-item show --id <id> --expand all --org <org-url> --output json`. Verify the type, title, project fields, content, and optional parent relation against the preview. Report the ID, title, type, state, and web URL, then remove temporary files created by this invocation.

Complete when the item and requested parent relation are verified or any mismatch is explicitly reported.
