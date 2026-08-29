---
name: skill-creator
description: Create new skills and revise, evaluate, or improve existing skills. Use whenever a user asks to make, update, refactor, test, benchmark, troubleshoot, or improve the triggering of a SKILL.md or reusable agent workflow.
argument-hint: "<skill creation or improvement task>"
model: sonnet
---

# Skill Creator

Skill task: $ARGUMENTS

Create or improve a skill through an evidence-driven draft, test, and refinement loop. Join the workflow at the user's current stage rather than restarting completed work.

## 1. Locate the target and governing conventions

Determine whether this is a new skill or an update. For an update, use the actual source path reported by skill discovery rather than assuming where the skill lives.

Before writing:

- Invoke any available instruction-writing or host-specific skill-authoring guidance
- Inspect nearby skills and project rules for frontmatter, naming, path, and tool conventions
- Put new repository OpenSkills under `skills/<skill-name>/` unless repository conventions specify another OpenSkills root
- Preserve an existing skill's location unless the user asks to migrate it
- Treat repository configuration, schemas, command help, and existing scripts as live sources of truth

Complete this phase when the target path, applicable conventions, and whether content is being created or revised are explicit.

## 2. Capture intent

Extract answers already present in the conversation before asking questions. Establish:

1. What capability the skill provides
2. Which user requests or contexts should trigger it
3. Required inputs, outputs, and side effects
4. Ordered workflow and decision branches
5. Edge cases, safety boundaries, dependencies, and approval points
6. Objective completion criteria
7. Whether evaluation is useful

Recommend evaluation for deterministic outputs, transformations, code generation, or fixed workflows. For subjective work, prefer focused human review unless the user wants benchmarks. Ask only for unresolved information that changes the design.

Complete this phase when the skill can be drafted without guessing hidden intent.

## 3. Design the skill

Use this structure:

```text
skill-name/
├── SKILL.md
├── references/   # branch-specific guidance, if needed
├── scripts/      # deterministic or repeated operations, if needed
└── assets/       # templates or output resources, if needed
```

Write metadata as a reliable context pointer:

- `name`: lowercase kebab-case identifier matching the directory
- `description`: front-load what the skill does and name each distinct trigger once
- `argument-hint`: concise expected invocation input when useful
- `model` or `compatibility`: include only when local conventions or runtime requirements justify them

Keep the main workflow in `SKILL.md`. Move variant-specific or lengthy material into references and state exactly when to read each reference. Prefer existing tools and scripts over restating facts the agent can inspect cheaply.

Complete this phase when every intent item maps to either metadata, an ordered step, a decision branch, a disclosed reference, or a completion check.

## 4. Draft or revise

Write imperative instructions in execution order. For each phase:

- State the actions to perform
- Put branch-specific guidance where the branch occurs
- End with a checkable completion criterion

Preserve useful existing behavior when revising. Remove duplication, stale runtime-specific assumptions, unsupported tool names, and prose that does not alter invocation, decisions, execution, or completion. Do not add bundled resources unless they are used by the workflow.

Skills must match their stated intent and must not conceal surprising side effects, credential access, data exfiltration, destructive behavior, or unauthorized access.

Complete this phase when an agent can follow the draft without inferring missing steps or tools.

## 5. Evaluate the skill

Adapt evaluation depth to the task and user preference.

### Lightweight review

For small or subjective skills:

1. Create 2–3 realistic prompts covering the main path and an important edge case
2. Trace whether the description triggers appropriately
3. Trace each prompt through the workflow
4. Review outputs or expected behavior with the user when judgment is subjective

### Comparative evaluation

For objectively testable or consequential skills:

1. Define representative prompts and expected results before running them
2. For a new skill, compare runs with the skill against runs without it
3. For an existing skill, snapshot the old version and compare it against the revision
4. Launch independent runs in parallel when the host supports subagents
5. Use objective assertions for machine-checkable properties and human review for subjective quality
6. Record pass/fail evidence, errors, token or timing data when available, and qualitative feedback
7. Summarize discriminating improvements, regressions, variance, and cost trade-offs

Keep evaluation artifacts in a sibling `<skill-name>-workspace/iteration-N/` directory unless project conventions specify another location. Do not require upstream scripts, graders, or viewers that are absent from the installed skill; use available host tools and clearly report any omitted metric.

Complete this phase when evidence shows where the draft helps, does not help, or regresses behavior.

## 6. Refine

Revise the smallest authoritative source that addresses each finding:

- Improve metadata for missed or false triggers
- Improve ordering or branch conditions for execution failures
- Add references only when branch-specific detail obscures the core workflow
- Add scripts only for deterministic repeated work
- Remove instructions that do not change outcomes

Re-run affected prompts after each meaningful revision. Expand the test set only after the core cases behave correctly. Stop when completion criteria pass, regressions are resolved, and further changes no longer have evidence-backed value.

## 7. Validate and report

Before finishing, verify:

- Frontmatter parses and required fields exist
- Name and directory match
- The description covers every intended trigger without claiming unrelated work
- Steps are ordered and each phase has a checkable end
- Safety and approval boundaries are explicit
- Runtime-specific tools are available or have a host-neutral fallback
- Project and global path precedence is correct
- References and scripts exist and are reachable from `SKILL.md`
- No instruction is duplicated across sources of truth
- New and changed behavior has been reviewed or tested at the agreed depth

Report the exact files created or changed, evaluation performed, results, and any remaining limitations.
