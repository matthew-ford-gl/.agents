# Fix Plan (only if the human asks for fixes)

If the human asks to act on the findings, do **not** improvise a plan file location. This plan is meant to be resumable — batches of fixes get checked off over multiple sessions, so it must always live in the same, predictable place instead of scattered across whatever directory a session happened to start in.

1. **Location**: `{plans-root}/{session-name}/quality-audit-plan.md`
   - `{plans-root}` is the `DEVIN_PLANS_DIR` environment variable if it's set (lets an individual user point this at a different drive, a synced folder, etc.), otherwise the cross-platform default `~/.devin/plans` (i.e. `%USERPROFILE%\.devin\plans` on Windows, `$HOME/.devin/plans` on macOS/Linux). Never hardcode a drive letter or OS-specific path — resolve it this way every time so the skill works unmodified on any machine.
   - `{session-name}` is a stable slug identifying this audit/fix effort — e.g. the repo name plus target (`myapp-quality-audit`, `myapp-diff-2026-08-17`). Use the current session/task name if one is already established; otherwise derive a short kebab-case slug from the repo and target and stick with it for the rest of the effort.
   - Before creating anything, check whether `{plans-root}/{session-name}/quality-audit-plan.md` already exists. If it does, **resume it** — do not overwrite. Reconcile: keep existing checked-off items as-is, add any newly found findings, and remove findings that no longer apply (file deleted/rewritten).
   - Create the `{plans-root}/{session-name}/` subfolder (and `{plans-root}` itself) if it doesn't exist.

2. **Format** — a checklist grouped by severity, then file, so batches can be marked off incrementally:

```markdown
# Quality Audit Fix Plan — {target}

Source audit: {date}
Status: {n}/{total} resolved

## Critical
- [ ] {file}:{line} — {issue} [{dimension}/{rule}] → {fix}

## Major
- [ ] {file}:{line} — {issue} [{dimension}/{rule}] → {fix}

## Minor
- [ ] {file}:{line} — {issue} [{dimension}/{rule}] → {fix}
```

3. **Working the plan**: as each batch of fixes is implemented and verified, check off the corresponding items (`- [x]`) and update the `Status` line in place — do not create a new file per batch. This is what makes the plan resumable: a new session (on the same machine, with the same `DEVIN_PLANS_DIR` if set) can open `{plans-root}/{session-name}/quality-audit-plan.md`, see exactly what's done and what's left, and continue.

4. Implementing the fixes themselves still follows normal workflow (e.g. via `/ship` or manual edits) — this step only governs where the tracking plan lives and how it's kept up to date.
