---
name: handoff
description: Compact the current session into a temporary, redacted handoff document so another agent can continue unfinished work without reconstructing the conversation.
argument-hint: "<optional focus for the next session>"
model: sonnet
---

# Session Handoff

Focus for the next session: $ARGUMENTS

1. Resolve the operating system's temporary directory: `[System.IO.Path]::GetTempPath()` or `$env:TEMP` on Windows, and `$TMPDIR` falling back to `/tmp` on macOS/Linux. Save a uniquely named Markdown handoff there, never in the repository.
2. Inspect the current repository and task state needed for continuation, including branch, working-tree status, active plans, decisions, issue or PR links, and verification results.
3. Reference existing artifacts by absolute path or URL rather than duplicating their contents. Do not restate diffs, specifications, ADRs, plans, or committed history.
4. Redact credentials, tokens, personal data, customer data, and other secrets. Describe required access by name only.
5. Write these sections:
   - **Objective** — intended outcome and optional next-session focus
   - **Current state** — completed, in progress, and not started
   - **Decisions and constraints** — only session knowledge not already captured elsewhere
   - **Artifacts** — paths, issue/PR URLs, branch, and relevant commits
   - **Verification** — commands run, outcomes, and gates not run
   - **Open questions and blockers** — owner and consequence of each
   - **Next actions** — ordered, concrete continuation steps
   - **Suggested skills** — exact skills the next agent should invoke and why
6. Read the finished file once to confirm it contains no secret values and can be followed without the current conversation.
7. Report the absolute handoff path and a one-sentence summary. Do not modify the repository.
