---
name: ship
description: "Orchestrates a task end-to-end through specialist review agents and raises a PR. Use when the user asks to ship, implement, or deliver a change with review gates, as a one-shot (non-route-based) task. Not for: per-route UI iteration loops (use iterate), or planning-only requests (use plan-task)."
model: sonnet # one-shot orchestration + PR authoring needs reliable multi-step tool use; opus's extra cost isn't justified for this non-iterative workflow
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

Complete this phase when project context and the resolved orchestrator path are both confirmed.

Then execute the workflow. Pass all loaded project context to any agents you spawn.