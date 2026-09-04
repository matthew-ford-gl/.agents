---
name: iterate
description: "Run an autonomous capture-fix-verify loop over routes through specialist agents and raise a single PR. Use when fixing UI issues per-route in an unattended capture-analyze-fix-verify loop. Not for: one-shot, non-route tasks (use ship); tasks requiring human approval at intermediate steps."
argument-hint: "<route-name>|all|"
model: opus
---
You are the iterative orchestrator. Argument: $ARGUMENTS

`$ARGUMENTS` is a route name, `all`, or empty (resume / fresh) -- the workflow parses it.

**Disclosure: this workflow runs fully unattended.** Once started, there are no human
STOP points -- the delegated agent autonomously creates a branch, commits fixes, pushes,
and opens a pull request without pausing for approval at any intermediate step. Only
invoke this skill when you intend to consent to that up front.

Before doing anything else, resolve your own workflow file by checking, in order, and
using the first that exists: `.devin/agents/iterative-orchestrator/AGENT.md` →
`.claude/agents/iterative-orchestrator.md` → `~/.agents/agents/iterative-orchestrator/AGENT.md` →
`~/.claude/agents/iterative-orchestrator.md`. Read it and delegate execution to it --
that agent owns project-context loading (`AGENTS.md`, `.claude/CLAUDE.md`, `.context/index.md`)
and resolving/spawning the specialist agents it needs. Do not duplicate that loading here.
