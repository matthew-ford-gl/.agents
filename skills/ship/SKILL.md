---
name: ship
description: "Routes and delivers a task end-to-end through the proportionate planning path, specialist review gates, implementation, validation, and a PR. Use when the user asks to ship, implement, or deliver a one-shot change and wants one plan-approval checkpoint before autonomous execution. Not for: per-route UI iteration loops (use iterate), planning without implementation (use plan-task), or an existing PR (use land-pr)."
model: sonnet # routing and one-shot orchestration need reliable multi-step tool use; strategic work is delegated to plan-task's stronger model
---
# Ship

Task: `$ARGUMENTS`

Use one front door and select the planning depth from repository evidence. The human approves the
selected plan once; after approval, execution owns ordinary technical corrections and returns only
for decisions that change the accepted mandate.

## 1. Load enough context to route

1. Read the repository root `AGENTS.md` and any nearer `AGENTS.md` files for likely affected paths.
2. Read repository `.claude/CLAUDE.md` when present.
3. Scan `.context/index.md` when present and load matching project guidance.
4. Inspect the task's likely code boundaries, contracts, persistence, deployment units, and recent
   history. Do not perform full implementation analysis merely to classify the route.

Complete when the likely scope and every strategic-routing condition below have an evidence-backed
true or false result.

## 2. Select one planning route

Choose **STRATEGIC** when any condition is true:

- the task changes architectural boundaries, component ownership, or dependencies between
  deployable units;
- it changes a public API, protocol, persisted-data meaning, migration order, or rollout topology;
- it introduces or changes domain identities, invariants, lifecycle rules, or bounded contexts;
- multiple materially different approaches remain and their trade-offs affect users, operations,
  compatibility, or rollback;
- failure has a high blast radius or no straightforward rollback;
- repository instructions explicitly require an ADR or strategic review for this change.

Choose **DIRECT** otherwise. File count alone does not make a task strategic. If evidence is
insufficient to classify one of the conditions, ask one focused question rather than defaulting to
the expensive route.

State the route and one-line evidence. Complete when exactly one route is selected.

## 3. Dispatch the selected workflow

For **STRATEGIC**, resolve `plan-task` using project-before-user precedence:
`.devin/skills/plan-task/SKILL.md` → `.claude/skills/plan-task/SKILL.md` →
`~/.agents/skills/plan-task/SKILL.md` → `~/.claude/skills/plan-task/SKILL.md`. Invoke it through the
host skill mechanism when available; otherwise read and follow the resolved file. Pass `$ARGUMENTS`
and the routing evidence. `plan-task` owns strategic debate, the human acceptance gate, and its
pre-approved Orchestrator handoff. Do not run a second plan or Orchestrator invocation afterward.

For **DIRECT**, resolve Orchestrator using project-before-user precedence:
`.devin/agents/orchestrator/AGENT.md` → `.claude/agents/orchestrator.md` →
`~/.agents/agents/orchestrator/AGENT.md` → `~/.claude/agents/orchestrator.md`. Read it and execute
that workflow with `$ARGUMENTS` and the loaded project context. Orchestrator owns the plan approval
gate and all subsequent execution.

For every delegated agent, use the same project-before-user path precedence and pass pointers to
loaded context rather than duplicating verbose content.

Complete when the selected workflow reports its PR or a precise human-decision, safety, permission,
or external blocker.
