---
name: skill-creator
description: "Create, revise, evaluate, and improve Devin or Claude Code skills and reusable agent workflows. Use whenever a user asks to make, update, refactor, test, benchmark, troubleshoot, or improve the triggering of a SKILL.md or reusable agent definition. Not for: read-only auditing of an existing skill library without intent to revise (use skill-reviewer)."
argument-hint: "<skill creation or improvement task>"
model: sonnet
---

# Skill Creator

Skill task: $ARGUMENTS

Create or improve a skill through an evidence-driven draft, test, and refinement loop. Join the workflow at the user's current stage rather than restarting completed work.

## 0. Should this exist? (pre-gate)

Before building, confirm the skill is worth the context cost:

- Can the host already do this well? Run the task once without a skill. No documented failure means do not build — if you did not watch the agent fail without the skill, you do not know whether the skill teaches the right thing.
- If you cannot write three evals for it, do not build it.
- Will it be used 5+ times? One-off tasks should be done inline.
- Always-relevant and small? Put it in the repo's `AGENTS.md` / `CLAUDE.md` / `.context/` passive context instead. Passive inline context beats skill retrieval for content needed on every task.
- Deterministic, repeated computation? Use a script bundled in the skill, not prose.
- Guaranteed enforcement on every event? Use a hook or gate, not a skill.

Complete this phase when every question above has an explicit answer and the answers justify building or revising a skill rather than doing the task inline, using passive context, or using a hook.

## 1. Choose the artifact

| You need | Build | Why |
|---|---|---|
| Reusable procedure or domain knowledge the model loads when relevant | **Skill** (default) | Adds supporting files and invocation control. |
| User-controlled side-effect macro (deploy, release, publish) | Skill with `disable-model-invocation: true` | Prevents the model from invoking it automatically. |
| Background conventions the model applies, user never invokes | Skill with `user-invocable: false` | Reference-content archetype. |
| Work that floods the main context (logs, search results, bulk reads) | **Subagent** | Isolation: explore in a separate window, return a distilled summary. |
| Always-relevant, small project facts | **AGENTS.md / CLAUDE.md** | Passive context is consistently available. |
| Both reusable instructions and isolation | Skill + fork/subagent dispatch | Use a brief, actionable prompt only. |

Complete this phase when one row of the table is selected and matches the capability, invocation, and isolation needs captured so far.

## 2. Locate the target and governing conventions

Determine whether this is a new skill or an update. For an update, use the actual source path reported by skill discovery rather than assuming where the skill lives.

Before writing:

- Invoke any available instruction-writing or host-specific skill-authoring guidance.
- Inspect nearby skills and project rules for frontmatter, naming, path, and tool conventions.
- Put new repository skills under `skills/<skill-name>/` unless repository conventions specify another root.
- Preserve an existing skill's location unless the user asks to migrate it.
- Treat repository configuration, schemas, command help, and existing scripts as live sources of truth.

Complete this phase when the target path, applicable conventions, and whether content is being created or revised are explicit.

## 3. Capture intent

Extract answers already present in the conversation before asking questions. Establish:

1. What capability the skill provides.
2. Which user requests or contexts should trigger it.
3. Required inputs, outputs, and side effects.
4. Ordered workflow and decision branches.
5. Edge cases, safety boundaries, dependencies, and approval points.
6. Objective completion criteria.
7. Whether evaluation is useful.

Recommend evaluation for deterministic outputs, transformations, code generation, or fixed workflows. For subjective work, prefer focused human review unless the user wants benchmarks. Ask only for unresolved information that changes the design.

Collect three or more natural trigger phrases the user would say to invoke this skill. These inform the `description` and `when_to_use` fields.

Complete this phase when the skill can be drafted without guessing hidden intent.

## 4. Design

Plan the artifact before writing:

- Confirm the artifact type from the table in section 1.
- State the complexity contract: non-applicability, cost/fast path, and fallback behavior.
- List the file structure (`SKILL.md`, `references/`, `scripts/`, `assets/`).
- Plan evals now: at least three, each testing a documented baseline gap or failure mode.

Use this structure for the skill directory:

```text
skill-name/
├── SKILL.md
├── references/    # branch-specific guidance, if needed
├── scripts/       # deterministic or repeated operations, if needed
└── assets/        # templates or output resources, if needed
```

Complete this phase when the artifact type, file structure, and eval plan are decided.

## 5. Draft or revise

Write imperative instructions in execution order. For each phase:

- State the actions to perform.
- Put branch-specific guidance where the branch occurs.
- End with a checkable completion criterion.

Frontmatter rules:

- `name`: lowercase kebab-case, matching the directory name. ≤64 characters; no leading/trailing/consecutive hyphens; no "anthropic" or "claude" unless the platform allows it.
- `description`: third person, verb-first capabilities. Use when [triggers/contexts]. Not for: [near-miss exclusions]. Keep it under 1,024 characters; combined with `when_to_use` (if present) under 1,536 characters.
- `argument-hint`: concise expected invocation input.
- `model` or `compatibility`: include only when runtime requirements justify it.

Description quick formula:

```
[Verb-first capabilities]. Use when [triggers/contexts]. Not for: [near-miss exclusions].
```

Body rules:

- Keep `SKILL.md` under 500 lines and ideally under 5,000 tokens (~200 lines for the always-relevant core).
- Move lengthy or branch-specific detail into `references/` and state exactly when to read each file.
- References are one level deep from `SKILL.md`; if a reference exceeds 100 lines, add a table of contents.
- Prefer existing tools and scripts over restating facts the agent can inspect cheaply.
- Preserve useful existing behavior when revising. Remove duplication, stale runtime-specific assumptions, unsupported tool names, and prose that does not alter invocation, decisions, execution, or completion.
- Do not add bundled resources unless they are used by the workflow.

Core authoring principles:

1. The model is already smart. Only add context it does not have; challenge every paragraph's token cost.
2. Standing instructions, not one-time steps. Skill content persists for the rest of the session.
3. Do not over-prompt. Avoid CRITICAL/MUST trigger language by default; current models overtrigger under it. Escalate force only for rules that measurably get missed, and explain why.
4. Gates beat persuasion. "Proceed only when X passes" plus external or deterministic checks. Never self-assessed compliance or anti-rationalization tables.
5. Match freedom to fragility. Fragile or sequence-critical work gets an exact script; open-ended work gets heuristics.
6. Feedback loops for quality-critical output. Run a validator → fix → repeat.

Safety: skills must not conceal surprising side effects, credential access, data exfiltration, destructive behavior, or unauthorized access.

Complete this phase when an agent can follow the draft without inferring missing steps or tools.

## 6. Evaluate

Adapt evaluation depth to the task and user preference. Load `references/evaluate.md` for the step-by-step procedure: its "Baseline-first approach" section for rigorous gap-driven validation, "Lightweight review" for small or subjective skills, or "Comparative evaluation" for objectively testable or consequential skills.

If the host provides skill-evaluation tools (e.g., `skill-eval:validate_skill`, `test_triggers`, `run_eval`), use them for validation, trigger testing, and grading. On hosts without those tools, perform the equivalent checks manually:

- Validate frontmatter is well-formed and the `name` matches the directory.
- Probe the description with should-trigger and should-not-trigger phrases.
- Run the core prompts and check outputs against the eval assertions.

Keep evaluation artifacts outside the installed skill tree. Resolve the host operating system's temporary directory and use `<temp>/<skill-name>-workspace/iteration-N/`; remove artifacts created for the run before finishing unless the user asks to preserve them. If the host has no writable temporary directory, ask the user where to place them rather than creating a sibling workspace. Do not require upstream scripts, graders, or viewers that are absent from the installed skill; use available host tools and clearly report any omitted metric.

Complete this phase when evidence shows where the draft helps, does not help, or regresses behavior.

## 7. Refine

Revise the smallest authoritative source that addresses each finding:

- Improve metadata for missed or false triggers.
- Improve ordering or branch conditions for execution failures.
- Add references only when branch-specific detail obscures the core workflow.
- Add scripts only for deterministic repeated work.
- Remove instructions that do not change outcomes.

Re-run affected prompts after each meaningful revision. Expand the test set only after the core cases behave correctly. Stop when completion criteria pass, regressions are resolved, and further changes no longer have evidence-backed value.

## 8. Validate and report

Before finishing, verify:

- Frontmatter parses and required fields exist.
- Name and directory match.
- The description covers every intended trigger without claiming unrelated work.
- Steps are ordered and each phase has a checkable end.
- Safety and approval boundaries are explicit.
- Runtime-specific tools are available or have a host-neutral fallback.
- Project and global path precedence is correct.
- References and scripts exist and are reachable from `SKILL.md`.
- No instruction is duplicated across sources of truth.
- New and changed behavior has been reviewed or tested at the agreed depth.

Report the exact files created or changed, evaluation performed, results, and any remaining limitations.

## Integration with sibling skills

| Counterpart | Hand-off |
|---|---|
| `prompt-craft` (or `prompt`) | Use for wording the prompt body of an agent definition or skill; this skill owns structure, frontmatter, and evals. |
| `subagent-dispatch` (or `agent`) | Use when dispatching analyzer or behavioral-test subagents during evaluation. |
| `clarify` | Use when intake is ambiguous before designing the skill. |
| `prose` (or `write`) | Use for polishing human-facing documentation generated by or about the skill. |
