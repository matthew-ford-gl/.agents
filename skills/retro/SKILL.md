---
name: retro
description: "Lightweight end-of-session self-reflection that captures repeated friction, rediscovery, and user corrections as improvement candidates for skills, agents, hooks, and repo context — appended to a persistent findings ledger. Use when the session is wrapping up, on phrasings like 'wrap up', 'we're done', 'end of session', or before a handoff. Not for: deep post-task reconstruction of artifacts and PRs (use retrospective), or handoff document production (use handoff)."
model: sonnet  # short in-session checklist + one ledger append; judgement is classification, not investigation
---

# Retro — end-of-session self-reflection

Runs in-session while live context still exists — no DB archaeology, no subagents, no investigation. "Nothing found" is a valid, cheap output; most sessions append nothing or one line.

Distinct from `retrospective`, which reconstructs a task from artifacts (git log, PRs, ROOT-CAUSE.md) and routes *domain learnings* to repo docs. `retro` is about **improving the agent tooling itself** — skills, agents, hooks, AGENTS.md, model pins.

## 1. Scan the session (from memory, ~1 minute)

Ask, in order:

1. **Rediscovery** — did I re-derive a command, flag, path, or env var that should already be documented? (e.g. re-found a render command, re-guessed a test filter, re-solved a port conflict)
2. **Repeated friction** — did I do the same fiddly thing more than ~3 times? (e.g. hand-built the same REST call, same env var prefix on every exec)
3. **User corrections** — did the user correct my approach, re-ask a question, or reject a first attempt? Each correction is a probable trigger or routing miss.
4. **Missed triggers** — did work happen manually that an existing skill should have caught? Check the skill list mentally; a near-miss means a `description` fix, not a new skill.
5. **Skill gaps** — was there genuinely no skill/agent for a repeatable pattern?

If a session-stats sidecar exists for this session (`~/.agents/session-stats/<session_id>.json`, written by the Stop hook), read it — top shell-command prefixes and tool counts confirm or kill suspicions about #1–#2. Absence of the file is fine; memory alone suffices.

## 2. Classify each candidate

| Candidate | Route |
|---|---|
| Repo-specific command/setup/convention rediscovered | That repo's `AGENTS.md` |
| Cross-repo action pattern with judgement | New skill, or extend an existing one |
| Existing skill didn't fire on its use case | Fix its `description`/`when_to_use` — never a new skill |
| Generic/unpinned subagent dispatch for a stable role | Named agent or `model:` pin question |
| Mechanical repeated API/command calls | Script inside a skill |
| One-off, unlikely to recur | Discard — do not log |

Hard rule: a single incident is a candidate, not a conclusion. Only the ledger (multiple sessions showing the same friction) justifies building.

## 3. Append to the ledger

Ledger: `~/.agents/session-findings.md`. Append one line per candidate under today's date heading (create the heading if absent):

```markdown
## YYYY-MM-DD

- [AGENTS-MD] <finding> — <repo/path> (session: <short title or id>)
- [SKILL-NEW] <finding>
- [SKILL-FIX] <finding> — <which skill>
- [AGENT] <finding>
- [SCRIPT] <finding>
```

One line each, evidence-terse. If nothing qualifies, append nothing and say so.

## 4. Report

```
Retro: N finding(s) logged.
- [ROUTE] one-line finding
Ledger: ~/.agents/session-findings.md (M total entries this month — flag for review if a
finding now has 2+ occurrences across sessions)
```

When a ledger entry accumulates a second occurrence, say so explicitly — that's the user's cue to approve building the fix. Never implement the fix inside retro; the finding is the output.
