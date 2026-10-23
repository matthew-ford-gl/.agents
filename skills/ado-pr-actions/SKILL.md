---
name: ado-pr-actions
description: "Reads and acts on Azure DevOps pull request review threads and comments — list threads, show a thread, post a top-level comment, reply to a thread, and resolve, reopen, close, or won't-fix a thread — by using Azure CLI safely. Use when asked to reply to PR comments, resolve or reopen review threads, list outstanding PR feedback, or post a comment on an Azure DevOps PR. Not for: creating a PR (use create-ado-pr), editing PR metadata (use update-ado-pr), reviewing a PR (use review-pr), or GitHub PRs."
argument-hint: "<action> <ADO PR URL> [thread id / comment]"
model: sonnet  # mechanical `az devops invoke` calls with fixed shapes; no synthesis or judgement beyond mapping intent to an action
---

# Azure DevOps PR Actions

Task: `$ARGUMENTS`

Invocation authorizes reading PR threads and comments freely. Writing — posting a comment or reply, or changing a thread's status — requires the user to have asked for that specific action; `land-pr` invocations may also carry thread-reply/resolution authorization. It never authorizes completing, abandoning, or voting on the PR, editing PR metadata, or bypassing branch policies.

## Phase 1: Resolve coordinates

The fastest path is the full PR URL:

```text
https://dev.azure.com/{org}/{project}/_git/{repository}/pullrequest/{id}
```

Pass it as `--pr-url` and the script derives org, project, repository, and PR ID. Otherwise supply `--org`, `--project`, `--repository` (name or GUID), and `--pr` individually. Resolve Python 3 as `python3`, `python`, or `py -3`.

If the repository must be a GUID, resolve it once with:

```text
az repos show --org <org-url> --project <project> --repository <name> --query id -o tsv
```

## Phase 2: Read (always safe)

List threads — returns compact JSON: thread id, status, comment count, first comment preview:

```text
<python> <skill-dir>/scripts/ado_pr_actions.py list --pr-url <url>
```

Show one thread's full comments:

```text
<python> <skill-dir>/scripts/ado_pr_actions.py show --pr-url <url> --thread-id <id>
```

Read actions execute immediately; they need no preview step.

## Phase 3: Write (preview, then execute)

Write content goes in a temporary UTF-8 file passed via `--content-file` — never inline multiline Markdown into a shell command.

| Action | Command fragment | Effect |
|---|---|---|
| `comment` | `--content-file <file>` | New top-level PR comment |
| `reply` | `--thread-id <id> --content-file <file>` | Reply inside an existing thread |
| `resolve` | `--thread-id <id>` | Set thread status to fixed/resolved |
| `reopen` | `--thread-id <id>` | Reopen a resolved thread |
| `close` | `--thread-id <id>` | Close thread without resolution |
| `wontfix` | `--thread-id <id>` | Mark thread won't-fix |

Run without `--execute` first. Inspect the JSON preview: the `command` array's first elements must be `az devops invoke` and the route parameters must match the intended PR and thread. Then rerun with `--execute` appended.

```text
<python> <skill-dir>/scripts/ado_pr_actions.py reply --pr-url <url> --thread-id <id> --content-file <file>
<python> <skill-dir>/scripts/ado_pr_actions.py reply --pr-url <url> --thread-id <id> --content-file <file> --execute
```

Resolve threads only when the underlying feedback is actually addressed — cite the fixing commit in a reply before resolving when the change isn't self-evident.

## Phase 4: Verify and report

After a write, confirm from the response that the comment landed or the thread status changed. On authentication failure, stop and ask the user to authenticate. Report thread IDs acted on and the resulting status.
