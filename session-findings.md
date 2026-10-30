## 2026-10-28

- [AGENTS-MD] marp.cmd breaks on `&` in filenames; use `node node_modules/@marp-team/marp-cli/marp-cli.js`; `--theme-set` is array opt so keep last; `-I . -o dist` for output dir — process-docs (F&B decks)
- [AGENTS-MD] PDF via `node scripts/export-pdf.js` (Chrome only, Edge fails); marp --pdf prints before Mermaid draws — process-docs
- [SKILL-FIX] ado-pr-actions: script crashes FileNotFoundError on Windows (subprocess can't find `az`, needs az.cmd) — ado-pr-actions/scripts/ado_pr_actions.py
- [SKILL-FIX] create-ado-pr: did not capture PR ID after creation; had to look up via `az repos pr list` — create-ado-pr
- [SKILL-FIX] create-ado-pr: forbids pushing, but "commit and PR" implies push; user wants push of source branch included (plain push, no force; ask only if diverged) — create-ado-pr/SKILL.md Phase 1 step 4 + header
- [AGENTS-MD] process-docs files are CRLF in git; `sed -i`/appends flipped README to LF (248-line diff) until re-CRLF'd — check `git diff --stat` after sed edits — process-docs
- [AGENTS-MD] Fast visual check of a deck: `marp-cli.js "<deck>.md" --html --allow-local-files --images png -o dist/qr.png`, read dist/qr.00N.png, then delete — process-docs

## 2026-10-29

- [SKILL-FIX] itsm-security-docs exists at ~/.agents/skills/itsm-security-docs but absent from skill list; `skill` invoke returned "not found", found only via file search — registration/discovery gap (session: ITSM review of process-docs)
- [SCRIPT] Hand-wrote throwaway puppeteer script to measure per-slide overflow and diff against `git show HEAD:` baseline; AGENTS.md only says "review rendered output" — candidate `scripts/check-overflow.js` in process-docs (related to 2026-10-28 png-check entry)
- [AGENTS-MD] Edit tool echoes the base64 logo `header:` line (~37k chars truncated) on edits near front matter, bloating context — process-docs; note: avoid editing line 1-6, or accept noise

## 2026-10-30

- [AGENTS-MD] Per-slide PNG render: node node_modules/@marp-team/marp-cli/marp-cli.js "<deck>.md" --images png --allow-local-files -o $TEMP/x.png (marp.cmd breaks on & in filenames; rerun every edit) — process-docs (session: OIM deck slide consolidation)
- [RESOLVED] [SKILL-FIX] create-ado-pr wrapper on Windows: '&' or quotes in description truncate it at that point yet PR is still created (needs az.cmd list-args, no shell); fix by sanitising/escaping in create_ado_pr.py — create-ado-pr
