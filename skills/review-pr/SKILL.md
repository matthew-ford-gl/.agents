---
name: review-pr
description: "Reviews a GitHub or Azure DevOps pull request for requirements compliance, coding standards, and backwards compatibility across upgrades, mixed-version deployments, persisted data, and public contracts, then presents a consolidated PASS/FAIL verdict with a fixes table. Use when given a GitHub or Azure DevOps PR URL and asked to review, gate, or assess it for merge-readiness. Not for: reviewing a local diff or branch with no PR URL (use code-review), single-dimension security-only review (use security-review), or reviewing a plan before any code exists."
argument-hint: "<PR URL (GitHub or Azure DevOps)>"
model: sonnet  # orchestration/dispatch workload (parsing the PR, fanning out 3 reviewer subagents, consolidating results); the reasoning-heavy work happens in the dispatched agents, so a lighter model here is sufficient
---
You are reviewing a pull request against its requirements, coding standards, and backwards-compatibility obligations.

Input: `$ARGUMENTS` — a full PR URL. Supports both GitHub and Azure DevOps formats.

## What This Command Does

Fetches the PR description and linked work items/issues to understand intent. Then runs three parallel reviewers: requirements compliance, coding standards, and backwards compatibility. The compatibility pass checks supported consumers, public contracts, persisted artifacts, configuration and CLI behaviour, mixed-version deployment, rollback, versioning, and migration requirements. Results are consolidated into one PASS/FAIL verdict with a fixes table. Optionally posts comments to the PR and/or fixes issues locally.

---

## Phase 0: Load Project Context

Before doing anything, load the project-specific context:

1. Read the repository root `AGENTS.md` and any nearer `AGENTS.md` files for the paths
   touched by the PR. Treat repository instructions as mandatory.
2. If `.claude/CLAUDE.md` exists in the repo root, read it.
3. If `.context/index.md` exists, scan it for keywords matching the PR's domain and load
   every matched standard, playbook, and convention file into your context.

Pass all loaded context to the agents you spawn.

Complete when the applicable `AGENTS.md`/`CLAUDE.md` files have been read and any matched `.context/index.md` entries are loaded.

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

Complete when `platform` is set and its identifiers are extracted, or the human has been told the URL is unrecognised.

---

## Phase 2: Fetch PR Details

Read `references/github.md` if `platform = github`, or `references/azure-devops.md` if
`platform = ado`, and follow that file's Phase 2 steps to fetch the PR title,
description/body, linked issue/work-item references, full diff, and changed-files list.

Complete when the PR title, description, linked issue/work-item references, full diff, and changed-file list have all been captured.

---

## Phase 3: Fetch Requirements Context

Gather the full requirements/spec from every linked work item or issue found in Phase 2.
Read `references/github.md` or `references/azure-devops.md` (whichever matches `platform`)
and follow that file's Phase 3 steps to fetch each linked issue or work item.

Compile all gathered requirements into a single **Requirements Summary**:
- What is the intent of this change?
- What are the acceptance criteria (explicit or inferred)?
- What constraints were stated?
- What is out of scope (if mentioned)?

Complete when the Requirements Summary (intent, acceptance criteria, constraints, out-of-scope) has been compiled from every linked issue or work item.

---

## Phase 4: Resolve Agents

Resolve each agent's file by checking, in order, and using the first that exists:

**`requirements-compliance`**:
`.devin/agents/requirements-compliance/AGENT.md` -> `.claude/agents/requirements-compliance.md` ->
`~/.agents/agents/requirements-compliance/AGENT.md` -> `~/.claude/agents/requirements-compliance.md`.
Read it.

**`code-reviewer`**:
`.devin/agents/code-reviewer/AGENT.md` -> `.claude/agents/code-reviewer.md` ->
`~/.agents/agents/code-reviewer/AGENT.md` -> `~/.claude/agents/code-reviewer.md`.
Read it.

**`backwards-compatibility-reviewer`**:
`.devin/agents/backwards-compatibility-reviewer/AGENT.md` ->
`.claude/agents/backwards-compatibility-reviewer.md` ->
`~/.agents/agents/backwards-compatibility-reviewer/AGENT.md` ->
`~/.claude/agents/backwards-compatibility-reviewer.md`.
Read it.

If any agent definition is missing, stop and tell the human which agent could not be found.

Complete when all three agent definitions have been resolved and read, or the human has been told which one is missing.

---

## Phase 5: Run Parallel Review (3 agents simultaneously)

Read `references/spawning.md` and use the runtime mechanism it describes to launch all
three agents below simultaneously.

### Agent 1 — Requirements Compliance

Pass the full content of the resolved `requirements-compliance` AGENT.md as the agent
persona, followed by:

```
You are reviewing this PR diff for requirements compliance.

Requirements Summary:
{Requirements Summary from Phase 3}

PR Description:
{PR description}

Diff:
{full diff}

Changed files:
{file list}

{Project context from Phase 0}
```

The requirements-compliance agent will return APPROVED or BLOCKED with findings classified
as CRITICAL / MAJOR / MINOR. Map the verdict: APPROVED -> PASS, BLOCKED -> FAIL.

### Agent 2 — Code Standards

Pass the full content of the resolved `code-reviewer` AGENT.md as the agent persona,
followed by:

```
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

### Agent 3 — Backwards Compatibility

Pass the full content of the resolved `backwards-compatibility-reviewer` AGENT.md as the
agent persona, followed by:

```
You are reviewing this PR diff for backwards compatibility and upgrade safety.

Requirements Summary:
{Requirements Summary from Phase 3}

PR Description:
{PR description}

Diff:
{full diff}

Changed files:
{file list}

Review repository-visible callers, public exports, specifications, schemas, fixtures,
examples, deployment manifests, version policy, migrations, and compatibility tests needed
to establish the old contract and supported consumers. Distinguish confirmed breakage from
uncertain external-consumer risk.

{Project context from Phase 0}
```

The backwards-compatibility reviewer returns APPROVED or BLOCKED with CRITICAL / MAJOR /
MINOR findings. Preserve those severities directly. A described breaking change is not thereby
safe: verify every versioning, migration, deployment, communication, and rollback obligation
mandated by repository policy. A fully managed break is summarized without blocking; missing
or unsafe obligations retain their evidence-based severity.

**Launch all three simultaneously.**

Complete when all three agents have returned a verdict (APPROVED/BLOCKED) with their findings.

---

## Phase 6: Consolidate and Report

After all three agents complete, merge findings into a single table sorted by severity,
then by source (Requirements, Compatibility, Standards).

Determine the overall verdict:
- **FAIL** if any CRITICAL or MAJOR finding exists from any agent
- **PASS** if only MINOR findings (or none)

Present to the human:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PR REVIEW — {PR title}
{PR URL}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Verdict: {PASS / FAIL}

Requirements:   {PASS / FAIL}  ({n} findings)
Compatibility:  {PASS / FAIL}  ({n} findings)
Standards:      {PASS / FAIL}  ({n} findings)

┌──────────┬───────────────┬────────────────────────────────────────┬──────────────────┐
│ Severity │ Category      │ Finding                                │ Location         │
├──────────┼───────────────┼────────────────────────────────────────┼──────────────────┤
│ CRITICAL │ Requirements  │ {description}                          │ {file:line}      │
│ CRITICAL │ Compatibility │ {description}                          │ {file:line}      │
│ CRITICAL │ Standards     │ {description}                          │ {file:line}      │
│ MAJOR    │ Requirements  │ {description}                          │ {file:line}      │
│ MAJOR    │ Compatibility │ {description}                          │ {file:line}      │
│ MAJOR    │ Standards     │ {description}                          │ {file:line}      │
│ MINOR    │ Requirements  │ {description}                          │ {file:line}      │
│ MINOR    │ Compatibility │ {description}                          │ {file:line}      │
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

No issues found. Requirements are addressed, compatibility is preserved, and code meets standards.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

Complete when the consolidated table (or the no-findings message) has been presented to the human with a single overall PASS/FAIL verdict.

---

## Phase 7: Post Comments — STOP and ask

If there are findings (any severity), ask the human:

```
Would you like me to post these findings as review comments on the PR?
  [Y] Yes — post as PR review comments
  [N] No  — keep the review local only
```

Wait for human response.

- **Yes**: Read `references/github.md` or `references/azure-devops.md` (whichever matches
  `platform`) and follow that file's Phase 7 steps to post the findings as PR comments.
  After posting, confirm to the human how many comments were posted.
- **No**: Continue to Phase 8.

Complete when the human's choice has been acted on — comments posted and confirmed, or the decision to skip posting is made.

---

## Phase 8: Fix Issues — STOP and ask

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
     - For Compatibility findings: preserve the old contract or add the required versioning,
       compatibility layer, migration, deployment ordering, tests, consumer communication,
       and release guidance.
     - For Standards findings: apply the coding standards fix.
  3. After all fixes, run the project's build/lint/test commands (from `AGENTS.md` or
     the project's standard tooling) to verify nothing is broken. Re-run the
     `backwards-compatibility-reviewer` against the updated diff and resolve every remaining
     CRITICAL or MAJOR compatibility finding before committing.
  4. Commit with a message summarising the fixes. Resolve the attribution line from your own
     host/runtime, not from any other runtime's convention:
     - If the repository's or the user's own global instructions (e.g. repo `AGENTS.md`,
       `CLAUDE.md`) specify a commit-attribution or co-author convention, use it exactly as
       specified there.
     - Otherwise, fall back to a generic line naming your own tool, e.g.
       `Generated with [tool name]`, with a matching `Co-Authored-By:` line for that same
       tool. Never default to another runtime's convention (for example, do not hardcode a
       Devin attribution when running under Claude Code or any other host).

     ```
     git commit -m "$(cat <<'EOF'
     Address PR review findings

     - {summary of each fix}

     {Attribution line resolved above, per your host's convention}
     EOF
     )"
     ```
  5. Push to the PR branch.
  6. Report what was fixed and confirm the push.
- **No**: Report is complete. Exit.

Complete when the fixes are committed, pushed, and reported, or the human has declined and the report is complete.
