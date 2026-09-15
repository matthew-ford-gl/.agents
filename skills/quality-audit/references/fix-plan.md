# Fix Plan (only if the human asks for fixes)

If the human asks to act on the findings, do **not** improvise a plan file location. This plan is meant to be resumable — batches of fixes get checked off over multiple sessions, so it must always live in the same, predictable place instead of scattered across whatever directory a session happened to start in.

1. **Location**: `{audit-session}/quality-audit-plan.md`
   - `{audit-session}` is the persistent session created by `quality-audit` at `<context_root>/<repo>/quality-audit/<session-name>/`. Resolve `context_root` through the canonical precedence in the repository `README.md`, beginning with the tool-agnostic `CONTEXT_STORAGE_PATH`; do not introduce a skill- or host-specific storage variable.
   - `{session-name}` is the stable slug established by the source audit, including its target and revision identity. Reuse that session rather than deriving a second location for fixes.
   - Before creating anything, check whether `{audit-session}/quality-audit-plan.md` already exists. If it does, **resume it** — do not overwrite. Reconcile: keep existing checked-off items as-is, add any newly found findings, and remove findings that no longer apply (file deleted/rewritten).

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

3. **Working the plan**: as each batch of fixes is implemented and verified, check off the corresponding items (`- [x]`) and update the `Status` line in place — do not create a new file per batch. This is what makes the plan resumable: a new session can resolve the same `context_root`, open `{audit-session}/quality-audit-plan.md`, see exactly what's done and what's left, and continue.

4. Implementing the fixes themselves still follows normal workflow (e.g. via `/ship` or manual edits) — this step only governs where the tracking plan lives and how it's kept up to date.
