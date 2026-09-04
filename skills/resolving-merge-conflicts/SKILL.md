---
name: resolving-merge-conflicts
description: "Resolve an in-progress Git merge or rebase conflict hunk by hunk from each side's original intent, then verify the integrated result. Use when Git reports unresolved merge or rebase conflicts. Not for: starting a new merge/rebase, or resolving conflicts outside an in-progress Git operation."
argument-hint: "<optional merge context>"
model: sonnet  # bounded hunk-by-hunk evidence tracing and verification is procedural judgement, not multi-agent synthesis; sonnet is sufficient
---

# Resolving Merge Conflicts

Task context: $ARGUMENTS

## 1. Establish state

Read the repository root and affected-path `AGENTS.md` files, `.claude/CLAUDE.md` when present, and task-relevant entries from `.context/index.md`. Treat their branch and validation rules as mandatory.

Inspect Git status, the merge or rebase state, conflicting paths, relevant history, and repository instructions. Do not begin a new merge or rebase. Do not abort, skip commits, reset, check out over changes, or rewrite history without explicit human approval for that action.

Complete this step when the merge or rebase state, the full list of conflicting paths, and the applicable repository and branch rules are all identified.

## 2. Trace intent

For each conflicted change, identify the primary evidence for both sides:

- Introducing commits and commit messages
- Associated issues, pull requests, specifications, and ADRs
- Tests and callers expressing required behaviour
- Surrounding history when the immediate commit is ambiguous

Summarise both intents before resolving the hunk. Treat generated files according to the repository's documented regeneration process.

Complete this step when both sides' intent, and the evidence supporting each, is summarised for every conflicted change.

## 3. Resolve one hunk at a time

Preserve both intents when they are compatible. When they conflict, choose only when repository evidence clearly establishes precedence. Do not invent a third behaviour merely to make the text merge.

Stop and ask the human when:

- The intents are materially incompatible and neither has established precedence
- Resolution changes persisted meaning, public contracts, security, payments, compliance, or irreversible workflows
- Primary evidence is unavailable or contradictory
- Continuing requires a destructive or history-rewriting action

After each file, confirm conflict markers are gone and review the complete file in context. Stage only resolved conflict paths; never stage unrelated changes.

Complete this step when every conflict marker is removed, each resolution's intent decision (or the reason it was escalated) is recorded, and only resolved paths are staged.

## 4. Verify integration

Discover validation commands from repository instructions and CI. Run the narrowest relevant checks first, then the required project gate. Fix integration failures attributable to the resolution; report unrelated pre-existing failures separately.

Complete this step when the narrowest relevant checks and the required project gate have both been run, with results (pass, fail, or pre-existing failure) reported.

## 5. Complete safely

Present the resolved paths, intent decisions, trade-offs, and verification results. Ask for confirmation before creating a merge commit or continuing a rebase unless the human explicitly requested completion of the in-progress operation. Never push unless explicitly asked.

Completion requires zero unresolved paths, no conflict markers, preservation or explicit disposition of both intents, and a green required gate or a clearly reported blocker.
