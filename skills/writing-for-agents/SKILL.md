---
name: writing-for-agents
description: Reference for creating or editing agent-consumed instructions, including SKILL.md, AGENT.md, AGENTS.md, CLAUDE.md, rules, and documents reached through their pointers. Use whenever changing those files.
argument-hint: "<instruction-writing task>"
model: sonnet
---

# Writing for Agents

Treat every instruction document as a program whose output varies with context. Optimise for reliable invocation, clear execution, and maintainable sources of truth.

## Context pointers

A context pointer is always-loaded wording that tells an agent what out-of-context material exists and the distinct conditions that require loading it. Skill descriptions, agent descriptions, and rules-file references are pointers.

For each pointer:

- Front-load the capability or trigger
- Name each genuinely distinct invocation branch once
- Remove synonyms that merely restate a branch
- Make the wording sufficient for reliable discovery without summarising the whole target

A strong target behind a weak pointer remains unreliable. Improve the pointer before duplicating target content into always-loaded context.

## Information hierarchy

Place information at the highest tier that needs it and no higher:

1. **In-file steps** — ordered actions every invocation performs
2. **In-file reference** — rules consulted by several steps
3. **Disclosed reference** — branch-specific detail loaded through an explicit pointer

Keep definitions, rules, caveats, and completion criteria for one concept together. Split material when branches need substantially different context or when visible later steps cause the current step to be rushed.

## Steps and completion criteria

Write positive, imperative steps in execution order. End every phase with a checkable completion criterion. Prefer exhaustive bounds such as “every acceptance criterion maps to a test” over vague outcomes such as “ensure good coverage.”

Use a compact, established leading term when it reliably carries the intended discipline. Define coined terms once. Phrase the desired behaviour directly; reserve prohibitions for safety boundaries that cannot be expressed positively.

## Invocation design

Choose whether the instruction is:

- **Model-invoked** when a clear task condition should trigger it automatically
- **User-invoked** when it initiates a consequential workflow or needs deliberate human control
- **Agent-only** when it is a specialist reached through an orchestrator

Descriptions encode invocation, not marketing. Include the task classes and branches that should trigger the instruction.

## Pruning and sources of truth

Keep each rule in one authoritative location and point to it elsewhere. Treat repository configuration, scripts, schemas, and command help as live sources of truth; document only reasons, conventions, or expensive discoveries that cannot be read cheaply from the environment.

Remove lines that do not affect invocation, decisions, execution, or completion. Use progressive disclosure when branch-specific reference obscures the main sequence.

## Review checklist

Before finishing, verify:

- The description triggers all intended branches without claiming unrelated work
- Steps are ordered and each phase has a checkable end
- Safety and approval boundaries are explicit
- Runtime-specific tool names are abstracted or covered by host branches
- Project-level and user-level path precedence is correct
- No rule is duplicated from another authoritative document
- Detail is disclosed at the point it becomes relevant
- The document can be followed without guessing hidden intent
