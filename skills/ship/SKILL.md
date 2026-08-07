---
name: ship
description: Orchestrate a task through specialist agents and raise a PR
model: sonnet
---
You are the orchestrator. Task: $ARGUMENTS

Before doing anything else:
1. Read the repository root `AGENTS.md` and any nearer `AGENTS.md` files for the paths you
   will touch. Treat repository instructions as mandatory throughout execution.
2. If `.claude/CLAUDE.md` exists in the repo root, read it.
3. If `.context/index.md` exists, scan it for keywords matching the task domain and load
   every matched standard, playbook, and convention file into your context.
4. Resolve your own workflow file by checking, in order, and using the first that exists:
   `.devin/agents/orchestrator/AGENT.md` → `.claude/agents/orchestrator.md` →
   `~/.agents/agents/orchestrator/AGENT.md` → `~/.claude/agents/orchestrator.md`. Read it.
5. For each agent you will spawn, resolve its file the same way: check, in order,
   `.devin/agents/<name>/AGENT.md` → `.claude/agents/<name>.md` →
   `~/.agents/agents/<name>/AGENT.md` → `~/.claude/agents/<name>.md`; use the first that exists

Then execute the workflow. Pass all loaded project context to the orchestrator and any
other agents you spawn.