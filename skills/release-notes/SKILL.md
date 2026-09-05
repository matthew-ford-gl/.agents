---
name: release-notes
description: "Drafts and inserts customer-facing release-note entries for the PWA (release-notes-pwa.json) and SiteHub (release-notes-sitehub.json) apps, either for the version currently being shipped or by backfilling every version merged since the last documented entry. Use when asked to add, write, update, or backfill release notes for the PWA or SiteHub, or to check whether any shipped version is missing release notes. Not for: internal/engineering changelogs, or documenting a version that has not actually shipped."
argument-hint: "[--backfill] [version or PR description]"
disable-model-invocation: true
model: sonnet  # tone-matched customer-facing writing and PR triage — no heavy multi-step reasoning needed
---

# Release Notes

Task: $ARGUMENTS

This is a user-invoked workflow because it writes customer-facing text that ships to end users and edits static JSON served in production. Invoking it authorizes drafting and inserting entries for versions that have actually shipped. It does not authorize inventing entries for unshipped versions, editing existing entries, or skipping a locale.

## 1. Pick mode

- **Default** (no `--backfill`): draft the entry for the version currently being shipped — the changes in the current branch/PR since the last documented release. Normally one version.
- **`--backfill`**: scan the full merged-PR history since the last documented entry and add every missing version, not just the latest.

Steps 2, and 4-7 are identical either way; step 3 differs in scope.

## 2. Identify the last documented version and the current shipped version

1. Open `src/web/epos-launcher/public/release-notes-pwa.json` and `release-notes-sitehub.json`. The first array entry in each is the latest documented version — note its `version` and `date`.
2. PWA current shipped version: the first three segments of the `name:` field in `.devops/bastion-web.yaml` (e.g. `0.40.3`), cross-checked against `version` in `src/web/epos-launcher/package.json`.
3. SiteHub current shipped version: the equivalent field in the SiteHub pipeline YAML.
4. If the last documented version already matches the current shipped version in both files, there is nothing to do — say so and stop.

## 3. Gather the changes

- **Default mode**: read the diff/PR for the current branch, plus any commits already merged to main since the last documented date that bump the version. Scope to the single version step being shipped.
- **Backfill mode**: list every PR merged to main since the last documented entry's date. Group them by version bump — a version boundary is a commit that bumps `package.json` or the pipeline YAML version. Each boundary becomes one release-notes entry.

## 4. Categorise each change as PWA, SiteHub, or both

- Touches `src/web/epos-launcher/` → PWA.
- Touches the .NET SiteHub backend (C# projects under `src/`, Android host, SiteHub services) → SiteHub.
- A single PR can be both — split its changes across the matching file(s).

## 5. Write customer-facing descriptions

For every version being added, write plain-language bullet points in `en` (mandatory), `de`, and `th`:

- Audience is a non-technical clerk/operator, not an engineer.
- Skip purely internal changes (CI tweaks, refactors, test cleanup) unless they have a user-visible effect (faster loading, fewer crashes, more stable).
- Group several small fixes shipped in the same version into one summary bullet rather than listing each individually.
- Match the tone of existing entries in the target file: short sentences starting with a verb ("Added…", "Fixed…", "Improved…").
- Never use raw PR titles, branch names, work-item IDs, or engineering jargon ("refactored DI container", "bumped NuGet packages", "fixed flaky pipeline") — translate to what the change means for the person using the till.

## 6. Insert entries

Prepend to the top of the array in the matching file(s) — never reorder or edit existing entries:

```json
{
  "version": "0.39.0",
  "date": "2026-06-XX",
  "entries": {
    "en": ["Description 1.", "Description 2."],
    "de": ["German description 1.", "German description 2."],
    "th": ["Thai description 1.", "Thai description 2."]
  }
}
```

Newer versions go first. Backfill mode may add several entries in one pass — keep them in descending version order, most recent at the top.

## 7. Validate — gate before finishing

Run:

```
node src/web/epos-launcher/scripts/check-release-notes.mjs
```

This must pass clean: both files valid JSON, every entry has an `en` locale, and the pipeline version from `.devops/bastion-web.yaml` has a matching PWA entry. Fix and re-run until it passes — do not report completion on a failing or warning run.

## Forbidden

- Raw PR titles, branch names, or work-item IDs in descriptions.
- Engineering jargon a clerk wouldn't understand.
- Removing, reordering, or editing existing entries — only prepend new ones.
- An entry missing any of the three locales.
- Trailing commas or malformed JSON.
- Entries for versions that have not actually shipped.

## Reference

- `ReleaseNoteEntry` type: `src/web/epos-launcher/src/types/releaseNotes.ts` — `version: string`, `date: string`, `entries: Record<locale, string[]>`.
- Release notes page: `/release-notes/:product`, linked from the clerk login screen via a rocket icon next to each version. PWA and SiteHub have separate pages and files.
- The JSON files are static assets fetched at runtime — editing them doesn't touch the JS bundle.
- `en` is the fallback locale; CI doesn't enforce `de`/`th`, but always provide them.
