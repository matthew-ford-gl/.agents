---
name: version-bump
description: "Bump a version field (patch by default) in the repo's version-bearing files, commit on a new branch, and open a PR. Use when asked to increment, bump, or update patch/minor/major versions — including phrasings like 'increment the patch version', 'bump versions and PR it', or 'do a version bump on a new branch'. Not for: releasing/tagging pipelines, changelog generation (use release-notes), or dependency version updates (use the package manager)."
model: sonnet  # mechanical find-edit-branch-PR flow; the only judgement is which files the user meant
---

# Version bump

Mechanical chore: find version fields, bump, branch, PR. The judgement is scope — bump only the files/components the user named, never everything found.

## 1. Confirm scope and base

- Which components? Users often name a subset ("only X and Y") — bump exactly those, even if more version fields exist.
- Start from latest default branch unless told otherwise: `git fetch origin && git checkout -b chore/bump-<component>-<version> origin/<default>`.
- Refuse on a dirty tree unless the user says the changes are unrelated and may ride along.

## 2. Locate the version fields

Check these, in order of likelihood:

- CI/deploy YAML: `grep -rn "version" .devops/ .azure-pipelines/ .github/` — a starting heuristic; tune for quoted keys or `version =` styles as the repo dictates. Often one `version:` key per service file.
- `*.csproj` / `Directory.Build.props`: `<Version>`, `<VersionPrefix>`, `<AssemblyVersion>`.
- `package.json`: `"version": "x.y.z"` (note: `npm version` also tags — edit the field directly when the flow is bump-branch-PR).
- `*.nuspec`, `app.manifest`, Helm `Chart.yaml` (`version:` vs `appVersion:` — ask if both present).

Report what you found and which you'll change before editing if the set is ambiguous.

## 3. Bump

- Default to patch (`x.y.Z+1`); only do minor/major when asked.
- Preserve formatting exactly — quoting, indentation, surrounding comments.
- Prerelease suffixes (`-beta.3`): keep the suffix and bump the numeric part unless told otherwise.

## 4. Commit, push, PR

- Commit only the version files: `git add <files> && git commit -m "Bump <component> to <version>"`.
- Confirm the changed-file list and target branch with the user before pushing, unless they pre-authorized the full bump-branch-PR flow (e.g. "bump it and PR it").
- Push and open the PR using the repo's remote type — `gh pr create` for GitHub; for Azure DevOps use the `create-ado-pr` skill (title like "Bump <component> patch versions"). If `create-ado-pr` isn't installed, push the branch and return the compare-PR URL for the user to open manually.

## Completion

Done when: only the intended files changed, the new version is exactly one increment up, branch is pushed, and a PR link is returned. If a version field looks hand-maintained elsewhere too (docs, README badges), flag it rather than editing silently.
