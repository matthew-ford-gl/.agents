---
name: iterate
description: Run a capture-fix-verify loop over routes through specialist agents and raise a single PR
model: sonnet
---
You are the iterative orchestrator. Argument: $ARGUMENTS

`$ARGUMENTS` is a route name, `all`, or empty (resume / fresh) -- the workflow parses it.

Before doing anything else:
1. Resolve your own workflow file by checking, in order, and using the first that exists:
   `.devin/agents/iterative-orchestrator/AGENT.md` → `.claude/agents/iterative-orchestrator.md` →
   `~/.agents/agents/iterative-orchestrator/AGENT.md` → `~/.claude/agents/iterative-orchestrator.md`. Read it.
2. If `.claude/CLAUDE.md` exists in the repo root, read it
3. For each agent you spawn, resolve its file the same way: check, in order,
   `.devin/agents/<name>/AGENT.md` → `.claude/agents/<name>.md` →
   `~/.agents/agents/<name>/AGENT.md` → `~/.claude/agents/<name>.md`; use the first that exists

Then execute the workflow.
