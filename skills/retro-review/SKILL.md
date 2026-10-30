---
name: retro-review
description: "Reads the retro findings ledger (~/.agents/session-findings.md), picks the entries that apply to the current repo, and applies them: updates the repo's AGENTS.md with verified [AGENTS-MD] findings and reports the other routes. Use when asked to 'apply retro findings', 'update this repo from the ledger', 'review session findings here', or 'sync AGENTS.md from retro'. Not for: logging new findings (use retro), post-task artifact reconstruction (use retrospective), or implementing skill/agent/hook fixes for unrelated repos."
argument-hint: "[optional repo name or path filter]"
---

# Retro-review — apply the ledger to the current repo

Ledger: `~/.agents/session-findings.md` (written by `retro`). Entry format: `- [ROUTE] finding — <repo/path> (session: ...)`, grouped under `## YYYY-MM-DD`. Entries tagged `[RESOLVED]` or `[APPLIED ...]` are done.

## 1. Identify the repo

Resolve the repo root (`git rev-parse --show-toplevel`) and its name (root folder name; also the origin URL's last segment). Note whether it is `~/.agents` itself.

Done when the repo name and root are known.

## 2. Select entries

Read the ledger. Keep an entry only if it is not `[RESOLVED]`/`[APPLIED ...]` and either:

- its `— <repo/path>` suffix names this repo (case-insensitive match on repo name or a path inside it), or
- it has no repo suffix and its route is `[SKILL-*]`, `[AGENT]` or `[SCRIPT]` and this repo is `~/.agents`.

Entries naming other repos are ignored. Entries with no repo suffix in any other repo are listed as "unscoped" and not applied.

Done when the matched, unscoped, and ignored counts are known.

## 3. Verify each matched entry against the repo

A ledger line is a single-session claim. Before writing anything, check it against live state: the command, path, flag, or file it cites exists; the fact is not already in `AGENTS.md` (or `CLAUDE.md`); it is not contradicted by repo files. Drop stale or duplicate entries and mark them `[APPLIED <date> <repo>: already present]` or report them as stale.

Done when every matched entry is classified as apply, already-present, or stale.

## 4. Apply

- `[AGENTS-MD]`: add a terse bullet to the repo's `AGENTS.md` in the most fitting section (create the file and a sensible heading if missing). Rewrite for a future agent: imperative, one line, include the command verbatim.
- Preserve the file's line endings and existing formatting. If the repo stores files as CRLF, write CRLF; confirm with `git diff --stat` that only intended lines changed.
- `[SKILL-FIX]`, `[SKILL-NEW]`, `[AGENT]`, `[SCRIPT]`: in `~/.agents` only, report as proposals and do not implement; building from the ledger needs the user's approval (retro's rule). Elsewhere, ignore them.

Done when `git diff` shows only the intended `AGENTS.md` changes.

## 5. Mark the ledger

For each applied or already-present entry, prefix it in `session-findings.md` with `[APPLIED YYYY-MM-DD <repo>]`. Change nothing else in the ledger; keep its line endings.

## 6. Report

List: entries applied (with the AGENTS.md section), already present, stale (with reason), proposals for skills/agents/scripts, and unscoped entries needing a repo decision. Do not commit or push unless asked.
