---
name: skill-reviewer
description: >-
  Audit one skill or the whole skills/ library against skill-creator's own
  frontmatter, body, and validation rules — pre-gate justification, naming,
  description formula, size/reference structure, and the section-8 completion
  checklist. Reports graded findings and fixes them on request. Use when
  asked to grade, audit, or check one skill or the whole skills library
  against skill-creator's rules. Not for drafting or revising a skill from
  scratch (use skill-creator) and not for live trigger/eval testing
  (static rule-checking only).
argument-hint: "[skill-name | path] (empty = whole skills/ library)"
model: sonnet  # rule-checking against a fixed, already-loaded ruleset is reasoning-bound, not knowledge-bound — sonnet is sufficient and keeps cost down across up to 8 parallel per-skill passes
---

# Skill Reviewer

Target: `$ARGUMENTS`

## What This Command Does

Grades one skill, or every skill in the library, against the rules `skill-creator` itself enforces — pre-gate justification, frontmatter formula, body/size rules, and the section-8 validation checklist. Findings are consolidated into one severity-ranked report. Read-only until the human approves fixes.

---

## Phase 1: Resolve the Skill Root and the Ruleset

Resolve the one skill root that Phase 2 will also use — do not resolve the ruleset and the target set from independently-guessed paths, or the two could silently come from different roots if the copies at `~/.claude/skills` and `~/.agents/skills` ever diverge.

Check, in order, and use the first that exists: project-local `.claude/skills/` or `.devin/skills/` first, falling back to the user-global `~/.claude/skills/` or `~/.agents/skills/`.

Read `<that root>/skill-creator/SKILL.md` in full — this is the ruleset every finding below cites by section number.

If no candidate root contains a `skill-creator/SKILL.md`, stop and tell the human there is no ruleset to grade against.

## Phase 2: Resolve the Target Set

Parse `$ARGUMENTS`:

- **Empty** — target every `skills/*/SKILL.md` under the same root Phase 1 resolved.
- **A name or path** — resolve to that one skill's directory under the same root. If it doesn't match any existing skill, stop and say so.

For each target skill, read its full directory: `SKILL.md` plus everything under `references/`, `scripts/`, `assets/` — needed to check reachability and unused-resource rules, not just the main file.

If the resolved target set is empty, stop and tell the human — do not run reviews on nothing.

## Phase 3: Chunk and Fan Out

One skill = one chunk. Cap concurrent passes at 8 per wave — if there are more, run 8 at a time, waiting for each wave before starting the next.

Launch one `general-purpose` Task per chunk (no dedicated review persona exists for this, and reviewing one skill's worth of skills doesn't clear skill-creator's own "used 5+ times" bar for minting a new agent). On Devin, use the equivalent session/subagent dispatch mechanism instead of the Claude Code Task tool — the dispatch target is host-specific, the fan-out shape below is not. Give each pass:

- The full skill-creator ruleset text from Phase 1.
- The target skill's full file contents (not paths) — `SKILL.md` and everything under `references/`, `scripts/`, `assets/`.

Ask each pass to check the skill against the ruleset text given above, citing the section number it violates. The rule groups below are a navigational index only — a non-authoritative summary for your own orientation, not a second source of truth. Every pass must ground its findings in the actual skill-creator text supplied to it, not this paraphrase, since this list will drift if skill-creator's own rules change:

- **Pre-gate (§0)** — evidence the skill fails the "should this exist" bar: a one-off task, content that belongs in passive `AGENTS.md`/`CLAUDE.md` context instead, or something that should be a hook/gate instead of a skill. Report as **advisory only** — this is a human judgment call, never auto-fixed.
- **Frontmatter (§5)** — `name` matches the directory, lowercase kebab-case, ≤64 chars, no leading/trailing/consecutive hyphens, no disallowed platform words; `description` follows the verb-first / "Use when [triggers]" / "Not for [exclusions]" formula and stays under the length caps; `model`/`compatibility` present without a runtime reason.
- **Body rules (§5)** — `SKILL.md` over budget (500 lines hard cap, ~200 lines/~5,000 tokens for the always-relevant core); branch-specific detail that belongs in `references/` instead of the main body; a `references/` file more than one level deep or over 100 lines without a table of contents; bundled resources not used by the workflow; stale tool names or runtime-specific assumptions; instructions duplicated across files.
- **Section 8 checklist** — frontmatter parses; `name` matches directory; description covers every intended trigger without claiming unrelated work; steps are ordered with a checkable end per phase; safety/approval boundaries are explicit; every referenced file/script actually exists and is reachable from `SKILL.md`; no instruction duplicated across sources of truth.
- **Safety (§5)** — no concealed side effects, credential access, data exfiltration, or destructive behavior.

Each finding needs: severity, the section it violates, `file:line`, and a concrete fix.

- **Critical** — hard-rule violation: name/directory mismatch, broken/unreachable reference path, frontmatter that fails to parse, concealed unsafe behavior.
- **Major** — description formula violation, size budget blown, duplicated instructions, missing safety/approval boundary.
- **Minor** — wording/style polish that doesn't change behavior.

Complete this phase when every chunk has returned a findings list (or an explicit error) and no wave remains unrun.

## Phase 4: Consolidate and Report

Merge all chunk results into one list, sorted by severity (Critical → Major → Minor), then by skill name. Print to the console — do not write a report file:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SKILL REVIEW — {target}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Skills reviewed: {n}

Critical ({n}):
  {skill}/SKILL.md:{line} — {issue} [§{section}] → {fix}

Major ({n}):
  {skill}/SKILL.md:{line} — {issue} [§{section}] → {fix}

Minor ({n}):
  {skill}/SKILL.md:{line} — {issue} [§{section}] → {fix}

Advisory — pre-gate (§0) concerns (not auto-fixed):
  {skill} — {concern}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

If nothing was found, print:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SKILL REVIEW — {target}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Skills reviewed: {n}

No violations found. Every reviewed skill matches skill-creator's rules.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

Findings only — no changes are made in this step.

## Phase 5: Fix on Approval — STOP and ask

If there are any Critical, Major, or Minor findings, ask the human:

```
Would you like me to fix these {n} findings now?
  [Y] Yes — apply fixes
  [N] No  — keep the review local only
```

Wait for the human's response.

- **No**: report stands, done.
- **Yes**:
  1. For each Critical/Major/Minor finding, apply the fix directly to the affected skill's `SKILL.md` or resource file.
  2. Never auto-fix advisory (§0 pre-gate) findings — those may mean deleting or relocating the skill entirely, which is a human decision. Leave them listed in the final report.
  3. After all edits, re-check: frontmatter still parses, `name` still matches its directory, and every reference/script path referenced from `SKILL.md` still resolves.
  4. Report exactly which files changed, which findings were fixed, and which remain (advisory items, or anything that couldn't be safely auto-fixed) — call those out explicitly rather than dropping them silently.
