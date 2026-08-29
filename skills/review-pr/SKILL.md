---
name: review-pr
description: Review a pull request against its originating issue/spec and coding standards. Takes a PR URL (GitHub or Azure DevOps), fetches the requirements from linked work items/issues, analyses the diff for requirement gaps and coding standards violations, and presents a consolidated PASS/FAIL verdict with a fixes table.
argument-hint: "<PR URL (GitHub or Azure DevOps)>"
model: sonnet
---
You are reviewing a pull request against its requirements and coding standards.

Input: `$ARGUMENTS` — a full PR URL. Supports both GitHub and Azure DevOps formats.

## What This Command Does

Fetches the PR description and linked work items/issues to understand the intent. Then runs two parallel reviewers: one checking whether the code faithfully implements the requirements (no gaps, no bad assumptions, no missing acceptance criteria), and one checking coding standards. Results are consolidated into a single PASS/FAIL verdict with a fixes table. Optionally posts comments to the PR and/or fixes the issues locally.

---

## Phase 0: Load Project Context

Before doing anything, load the project-specific context:

1. Read the repository root `AGENTS.md` and any nearer `AGENTS.md` files for the paths
   touched by the PR. Treat repository instructions as mandatory.
2. If `.claude/CLAUDE.md` exists in the repo root, read it.
3. If `.context/index.md` exists, scan it for keywords matching the PR's domain and load
   every matched standard, playbook, and convention file into your context.

Pass all loaded context to the agents you spawn.

---

## Phase 1: Parse the PR URL

Parse `$ARGUMENTS` to determine the platform and extract identifiers.

**GitHub** — URLs matching `github.com/{owner}/{repo}/pull/{number}`:
- Extract `owner`, `repo`, `pullNumber`.
- Set `platform = github`.

**Azure DevOps** — URLs matching `dev.azure.com/{org}/{project}/_git/{repo}/pullrequest/{id}`
or `{org}.visualstudio.com/{project}/_git/{repo}/pullrequest/{id}`:
- Extract `org`, `project`, `repo`, `pullRequestId`.
- Set `platform = ado`.

If the URL does not match either pattern, stop and tell the human the URL is not recognised.

---

## Phase 2: Fetch PR Details

### GitHub

1. Call `pull_request_read` (method: `get`) via MCP server `devin/github-mcp-server` to get
   the PR title, description/body, and linked issue references.
2. Parse the PR body for issue references (`#123`, `Fixes #123`, `Closes #123`,
   `https://github.com/{owner}/{repo}/issues/{n}`).
3. Call `pull_request_read` (method: `get_diff`) to get the full diff.
4. Call `pull_request_read` (method: `get_files`) to get the list of changed files.

### Azure DevOps

1. Call `repo_pull_request` (action: `get`, `includeWorkItemRefs: true`,
   `includeChangedFiles: true`) via MCP server `azure-devops` to get the PR title,
   description, linked work item IDs, and changed files.
2. Call `repo_pull_request` (action: `get`) again without extra flags if needed for the
   diff content — or use `gh` / `az repos pr diff` CLI as a fallback.

---

## Phase 3: Fetch Requirements Context

Gather the full requirements/spec from every linked work item or issue.

### GitHub

For each linked issue number found in Phase 2:
- Call `issue_read` (method: `get`) via `devin/github-mcp-server` to get the issue title,
  body, labels, and state.
- If the issue body references other issues or specs, follow one level deep.

### Azure DevOps

For each linked work item ID found in Phase 2:
- Call `wit_work_item` (action: `get`, `expand: Relations`) via `azure-devops` to get
  the work item title, description, acceptance criteria, state, and relations.
- For parent work items (e.g. a Task's parent User Story), follow one level up to get
  the broader context and acceptance criteria.

Compile all gathered requirements into a single **Requirements Summary**:
- What is the intent of this change?
- What are the acceptance criteria (explicit or inferred)?
- What constraints were stated?
- What is out of scope (if mentioned)?

---

## Phase 4: Run Parallel Review (2 agents simultaneously)

Launch TWO agents in parallel, each receiving the full PR diff, the changed file list,
the PR description, the Requirements Summary from Phase 3, and all project context
from Phase 0.

### Agent 1 — Requirements Analyst

```
You are a requirements analyst reviewing a pull request diff against its originating
issue/spec. Your job is to find gaps between what was asked for and what was implemented.

You have been given:
- The PR description
- The full requirements/acceptance criteria from linked work items/issues
- The PR diff

Analyse the diff against the requirements. For each finding, classify it.

Look for:
- MISSING REQUIREMENT: An acceptance criterion or stated requirement that has no
  corresponding change in the diff
- BAD ASSUMPTION: The code assumes something about the domain, data shape, or user
  behaviour that contradicts or is not supported by the spec
- SCOPE CREEP: Changes in the diff that go beyond what the issue/spec asked for and
  were not flagged as intentional (ignore minor refactors of touched code)
- INCOMPLETE IMPLEMENTATION: A requirement is partially addressed but edge cases,
  error handling, or specific scenarios mentioned in the spec are missing
- SPEC AMBIGUITY: The spec is unclear and the implementation made a choice that could
  be wrong — flag for human review

For each finding state:
1. What the requirement says (quote from the issue/spec)
2. What the diff does (or does not do)
3. Severity: CRITICAL (blocks acceptance) / MAJOR (likely rework) / MINOR (polish)
4. The specific file(s) and line(s) involved

If no linked issues or requirements were found, state this explicitly — do not
fabricate requirements. Instead, review the PR description itself as the spec and
note that no formal requirements were linked.

End with: PASS (no critical or major findings) or FAIL (one or more critical/major findings).
```

### Agent 2 — Code Standards Reviewer

Resolve the `code-reviewer` agent by checking, in order, and using the first that exists:
`.devin/agents/code-reviewer/AGENT.md` -> `.claude/agents/code-reviewer.md` ->
`~/.agents/agents/code-reviewer/AGENT.md` -> `~/.claude/agents/code-reviewer.md`. Read it.

```
{Full content of the resolved code-reviewer AGENT.md}

You are reviewing this PR diff. There is no prior approved plan — treat the PR description
as the plan. Review the diff for coding standards violations.

PR Description:
{PR description}

Diff:
{full diff}

Changed files:
{file list}

{Project context from Phase 0}
```

The code-reviewer agent will return APPROVED or BLOCKED with Must fix / Should fix / Nit
categories. Map these to the consolidated severity scale:
- Must fix -> CRITICAL
- Should fix -> MAJOR
- Nit -> MINOR

**Launch both simultaneously.**

---

## Phase 5: Consolidate and Report

After both agents complete, merge all findings into a single table sorted by severity,
then by source (Requirements first, then Standards).

Determine the overall verdict:
- **FAIL** if any CRITICAL or MAJOR finding exists from either agent
- **PASS** if only MINOR findings (or none)

Present to the human:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PR REVIEW — {PR title}
{PR URL}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Verdict: {PASS / FAIL}

Requirements:  {PASS / FAIL}  ({n} findings)
Standards:     {APPROVED / BLOCKED}  ({n} findings)

┌──────────┬───────────────┬────────────────────────────────────────┬──────────────────┐
│ Severity │ Category      │ Finding                                │ Location         │
├──────────┼───────────────┼────────────────────────────────────────┼──────────────────┤
│ CRITICAL │ Requirements  │ {description}                          │ {file:line}      │
│ CRITICAL │ Standards     │ {description}                          │ {file:line}      │
│ MAJOR    │ Requirements  │ {description}                          │ {file:line}      │
│ MAJOR    │ Standards     │ {description}                          │ {file:line}      │
│ MINOR    │ Requirements  │ {description}                          │ {file:line}      │
│ MINOR    │ Standards     │ {description}                          │ {file:line}      │
└──────────┴───────────────┴────────────────────────────────────────┴──────────────────┘

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

If there are no findings at all, print:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PR REVIEW — {PR title}
{PR URL}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Verdict: PASS

No issues found. Requirements fully addressed. Code meets standards.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## Phase 6: Post Comments — STOP and ask

If there are findings (any severity), ask the human:

```
Would you like me to post these findings as review comments on the PR?
  [Y] Yes — post as PR review comments
  [N] No  — keep the review local only
```

Wait for human response.

- **Yes**:
  - **GitHub**: Use `pull_request_review_write` (method: `create`) to create a pending
    review, then `add_comment_to_pending_review` for each finding that has a specific
    file:line location, then `pull_request_review_write` (method: `submit_pending`) with
    event `COMMENT` (if PASS) or `REQUEST_CHANGES` (if FAIL). For findings without a
    specific line, include them in the review body summary.
  - **Azure DevOps**: Use `repo_pull_request_thread_write` to create a comment thread for
    each finding with the appropriate file path and line position. Set thread status to
    `Active` for CRITICAL/MAJOR findings and `Closed` for MINOR (nit) findings.
  - After posting, confirm to the human how many comments were posted.
- **No**: Continue to Phase 7.

---

## Phase 7: Fix Issues — STOP and ask

If there are CRITICAL or MAJOR findings, ask the human:

```
Would you like me to fix the {n} critical/major issues and push to the PR branch?
  [Y] Yes — fix and push
  [N] No  — done
```

Wait for human response.

- **Yes**:
  1. Check out the PR's source branch locally (use `git` for GitHub, `git` for ADO).
  2. For each CRITICAL and MAJOR finding, implement the fix:
     - For Requirements findings: implement the missing or incomplete requirement.
     - For Standards findings: apply the coding standards fix.
  3. After all fixes, run the project's build/lint/test commands (from `AGENTS.md` or
     the project's standard tooling) to verify nothing is broken.
  4. Commit with a message summarising the fixes:
     ```
     git commit -m "$(cat <<'EOF'
     Address PR review findings

     - {summary of each fix}

     Generated with [Devin](https://devin.ai)

     Co-Authored-By: Devin <158243242+devin-ai-integration[bot]@users.noreply.github.com>
     EOF
     )"
     ```
  5. Push to the PR branch.
  6. Report what was fixed and confirm the push.
- **No**: Report is complete. Exit.

---

## Spawning Mechanism

Detect which runtime you are in and use its native mechanism for parallel agents:

- **Devin CLI**: spawn each agent with `run_subagent`, `profile: "subagent_general"`,
  `is_background: true` for both agents, then collect each with `read_subagent`
  (`block: true`) once both have been launched.
  - Read the `code-reviewer` AGENT.md and pass its full content as part of the task prompt
    for Agent 2, since `code-reviewer` may not be a recognised built-in profile.
- **Claude Code**: spawn each as a `Task` tool call.
- **Other hosts**: use the native parallel-subagent primitive.
