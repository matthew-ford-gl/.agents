---
name: writing-for-agents
description: "Guides how to write and structure agent-consumed instructions and reference documents, including SKILL.md, AGENT.md, AGENTS.md, CLAUDE.md, rules, and documents reached through their pointers. Use when writing or editing SKILL.md, AGENT.md, AGENTS.md, CLAUDE.md, rules, or documents reached through their pointers. Not for: skill frontmatter/eval mechanics — use skill-creator for that; wording an individual prompt's text — use prompt-craft for that."
argument-hint: "<instruction-writing task>"
model: sonnet  # editing/reviewing instruction prose is style-and-structure judgement over prior drafts, not multi-step or multi-agent reasoning; sonnet is sufficient
---

# Writing for Agents

Treat every instruction document as a program whose output varies with context. Optimise for reliable invocation, clear execution, and maintainable sources of truth.

## 1. Map the context pointers

A context pointer is always-loaded wording that tells an agent what out-of-context material exists and the distinct conditions that require loading it. Skill descriptions, agent descriptions, and rules-file references are pointers.

Identify every file this document points to and every file that points to it. For each pointer:

- Front-load the capability or trigger
- Name each genuinely distinct invocation branch once
- Remove synonyms that merely restate a branch
- Make the wording sufficient for reliable discovery without summarising the whole target

A strong target behind a weak pointer remains unreliable — improve the pointer before duplicating target content into always-loaded context.

Complete when the full pointer graph (in and out) is listed and every pointer in it supports reliable discovery on its own wording.

## 2. Assign each piece of content to a tier

Place each fact, rule, or instruction at the highest tier that needs it and no higher:

1. **In-file steps** — ordered actions every invocation performs
2. **In-file reference** — rules consulted by several steps
3. **Disclosed reference** — branch-specific detail loaded through an explicit pointer

Keep definitions, rules, caveats, and completion criteria for one concept together. Split material into a lower tier only when branches need substantially different context, or when a later step's visible detail would cause the current step to be rushed.

Complete when every piece of content in the document has an explicit tier assignment and nothing sits at a tier higher than it needs.

## 3. Write steps with completion criteria

Write positive, imperative steps in execution order. End every phase with a checkable completion criterion. Prefer exhaustive bounds such as "every acceptance criterion maps to a test" over vague outcomes such as "ensure good coverage."

Use a compact, established leading term when it reliably carries the intended discipline. Define coined terms once. Phrase the desired behaviour directly; reserve prohibitions for safety boundaries that cannot be expressed positively.

Complete when every phase in the document reads as an action in execution order and ends with a criterion someone else could check without asking the author.

## 4. Choose and encode the invocation category

Decide whether the instruction being written is:

- **Model-invoked** when a clear task condition should trigger it automatically
- **User-invoked** when it initiates a consequential workflow or needs deliberate human control
- **Agent-only** when it is a specialist reached through an orchestrator

Write the description to encode that invocation, not to market the document — include the task classes and branches that should trigger it, and exclude near-misses that belong to a sibling document.

Complete when the chosen category is stated and the description's trigger language matches it.

## 5. Prune and re-point duplicated rules

For every rule, fact, or convention in the document, check whether it is already recoverable from a live source of truth (repository configuration, scripts, schemas, command help) or from another authoritative document. If so, delete it here and leave a pointer instead. Keep each rule in exactly one authoritative location.

Remove lines that do not affect invocation, decisions, execution, or completion. Push branch-specific reference behind an explicit pointer (progressive disclosure) when it would otherwise obscure the main sequence.

Complete when no rule in the document is duplicated from, or duplicated into, another authoritative source.

## 6. Validate

For SKILL.md files, follow skill-creator's own §8 *Validate and report* checklist — frontmatter parsing, name/directory match, description coverage, ordered steps with checkable ends, safety/approval boundaries, tool and path precedence, reference/script reachability, and no cross-source duplication all apply unchanged; do not re-derive them here.

For generic instruction docs outside skill-creator's scope (AGENT.md, AGENTS.md, CLAUDE.md, rules files, and documents reached through their pointers), additionally verify what that checklist does not cover:

- Every file this doc points to, and every file that points to it, exists and is reachable — the pointer graph from step 1 has no dead ends.
- Detail is disclosed at the point it becomes relevant, since these docs have no `references/` directory convention to fall back on.
- The document can be followed without guessing hidden intent.

Complete when the applicable checklist — skill-creator's §8 for skill files, the three checks above for generic docs — passes with no open items.
