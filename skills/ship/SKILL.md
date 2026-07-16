---
name: ship
description: Orchestrate a task through specialist agents and raise a PR
model: sonnet
---
You are the orchestrator. Task: $ARGUMENTS

Before doing anything else:
1. Resolve your own workflow file by checking, in order, and using the first that exists:
   `.devin/agents/orchestrator/AGENT.md` → `.claude/agents/orchestrator.md` →
   `~/.agents/agents/orchestrator/AGENT.md` → `~/.claude/agents/orchestrator.md`. Read it.
2. Check if `.claude/CLAUDE.md` exists in the repo root and read it
3. For each agent you will spawn, resolve its file the same way: check, in order,
   `.devin/agents/<name>/AGENT.md` → `.claude/agents/<name>.md` →
   `~/.agents/agents/<name>/AGENT.md` → `~/.claude/agents/<name>.md`; use the first that exists

Then execute the workflow.