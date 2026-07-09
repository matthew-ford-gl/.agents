---
name: iterate
description: Run a capture-fix-verify loop over routes through specialist agents and raise a single PR
model: sonnet
---
You are the iterative orchestrator. Argument: $ARGUMENTS

`$ARGUMENTS` is a route name, `all`, or empty (resume / fresh) -- the workflow parses it.

Before doing anything else:
1. Read the workflow repo-first: if `.claude/agents/iterative-orchestrator.md` exists use it, else use `~/.claude/agents/iterative-orchestrator.md`
2. If `.claude/CLAUDE.md` exists in the repo root, read it
3. For each agent you spawn, check `.claude/agents/<name>.md` first; fall back to `~/.claude/agents/<name>.md`

Then execute the workflow.
