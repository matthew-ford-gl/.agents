# Upstream

Vendored from <https://github.com/cloudflare/security-audit-skill> (`skills/security-audit/`).

- Pinned commit: `c1c8a8c1471069fb0e188eeaff69b8e8db6564a8` (main, fetched 2026-10-23)
- License: MIT — see `LICENSE` (copyright notice retained per license terms)

## Local modifications

Only `SKILL.md` is modified; every other file is byte-identical to upstream:

1. Frontmatter: added `argument-hint` and `model: opus`; appended a house-style `Not for:` clause to `description`.
2. Added a "Local mapping (Devin CLI)" paragraph at the end of the *Platform terminology* section, mapping the agent-neutral roles to `run_subagent` / `subagent_explore` / `subagent_general` and noting Windows sandbox limitations.

## Known platform limitation (Windows)

Both `validate-coverage-ledger.cjs` and `validate-findings.cjs` fail closed when run as CLIs on Windows ("OS no-follow and nonblocking input protection is unavailable"). Library-level validation and all non-CLI tests pass. Run the validators under WSL/Linux/macOS, or accept an `incomplete` run per the skill's own rules. Upstream test suite: `validate-coverage-ledger.test.cjs` 24/24 pass (7 skipped); `validate-findings.test.cjs` 22 pass, 7 CLI-only failures on Windows, 5 skipped.

## Refreshing

1. Fetch upstream at the new commit (sparse checkout of `skills/security-audit`).
2. Diff `SKILL.md` upstream-vs-local; re-apply the two edits above.
3. Copy all other files verbatim, plus `LICENSE` from the repo root.
4. Update the pinned commit above.
