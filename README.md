# AI Agent & Skill Library

A central repository of reusable agent definitions, command skills, and lifecycle hooks for Claude Code and Devin CLI. This repo is the canonical source. Devin reads `.agents/` directly; the install scripts render Claude-specific definitions, link Devin definitions where needed, and link shared hooks into the directories where each CLI expects them.

- `install-windows.ps1` / `install-mac.sh` / `install-wsl.sh` — renders Claude agents and skills with compatible models, creates Devin and hook symlinks where needed, and removes stale Devin copies. Skips any component whose source does not exist.
- `uninstall-windows.ps1` / `uninstall-mac.sh` / `uninstall-wsl.sh` — removes the artifacts created by the install script.

---

## Agents

Agents are discussion personas and reviewers that can be invoked by the orchestrator or by the `/ship`, `/plan-task`, `/architecture-audit`, `/iterate`, and `/ui-review` skills.

| Agent | Stage | Role | Devin / Claude model | Tools |
|-------|-------|------|----------------------|-------|
| `orchestrator` | Workflow | Main execution workflow: plan, review, implement, test, and raise a PR. | opus / opus | unrestricted |
| `iterative-orchestrator` | Workflow | Autonomous per-route UI fix loop: capture, analyse, fix, re-verify, and raise a single PR. | opus / opus | unrestricted |
| `director` | Discussion | Binding decision maker. Synthesises all debate positions into `DECISION.md` with `PROCEED` / `PROCEED WITH MODIFICATIONS` / `DEFER` / `REJECT`. | opus / opus | read-only |
| `senior-engineer` | Plan | Validates implementation plans against engineering standards (architecture, code quality, API design, performance, resilience, observability, testing). | sonnet / sonnet | read-only |
| `qa-gatekeeper` | Plan & Diff | Dual-mode QA reviewer: plan mode checks testability, implementation mode checks committed tests against the test strategy. | swe / haiku | read-only |
| `security-analyst` | Plan & Diff | Two-pass threat model (STRIDE) and standards compliance covering OWASP, GDPR, PCI-DSS, business logic, abuse, and supply chain. | sonnet / sonnet | read-only + web_search |
| `guardian` | Discussion | Principal Engineer production-safety persona. Holds the Safety Veto for data loss, security breach, and payment corruption. | sonnet / sonnet | read-only |
| `pragmatist` | Discussion | Complexity challenger and MVP champion. Pushes for the minimum shippable slice and probability-grounded risk estimates. | sonnet / sonnet | read-only |
| `craftsman` | Discussion | Code-quality and test-first champion. Owns the Test-First Strategy table and enforces SOLID. | sonnet / sonnet | read-only |
| `architect` | Discussion | Principal Architect. Reviews service boundaries, data ownership, coupling, abstraction correctness, and evolution risk. | sonnet / sonnet | read-only |
| `user-advocate` | Discussion | End-user perspective. Traces user journeys, edge cases, and accidental complexity in the UX. | sonnet / sonnet | read-only |
| `historian` | Discussion | Institutional memory guardian. Cross-references plans against git history, past incidents, and documented patterns. | sonnet / sonnet | read-only + exec |
| `code-reviewer` | Diff | Reviews the concrete diff against the approved plan for bugs, plan-drift, and standard violations. | swe / haiku | read-only |
| `backwards-compatibility-reviewer` | Diff | Checks upgrade and mixed-version safety across public APIs, schemas, persisted data, configuration, CLI contracts, events, integrations, deployment ordering, and rollback. | sonnet / sonnet | read-only |
| `accessibility-reviewer` | Plan & Diff | Conditional reviewer for UI changes. Checks WCAG 2.2 Level AA, keyboard operability, ARIA, and touch targets. | swe / haiku | read-only |
| `dependency-reviewer` | Plan & Diff | Conditional reviewer for package changes. Checks supply chain, maintenance, license, necessity, transitive deps, and CVEs. | swe / haiku | read-only + web_search |
| `migration-reviewer` | Plan & Diff | Conditional reviewer for schema and data migrations. Checks zero-downtime compatibility, sequencing, rollback, and scale. | sonnet / sonnet | read-only |
| `observability-reviewer` | Diff | Verifies new code paths have structured logging, metrics, tracing, and production-debuggable signals. | swe / haiku | read-only |
| `performance-reviewer` | Diff | Checks for N+1 queries, algorithmic complexity, missing indexes, unbounded fetches, caching gaps, and memory leaks. | swe / haiku | read-only |
| `requirements-compliance` | Diff | Checks whether a code diff faithfully and completely implements the originating issue, spec, or acceptance criteria. Finds requirement gaps, bad assumptions, incomplete implementation, and scope creep. | swe / haiku | read-only |
| `repo-investigator` | Investigation | Tests one bounded repository claim, traces production reachability, and returns an evidence-backed verdict with explicit uncertainty. | sonnet / sonnet | read-only + exec |
| `docs-updater` | Utility | Keeps `/docs` folder files in sync with current code, API contracts, and CLI flags. | swe / haiku | read/edit/write/exec |
| `domain-modeller` | Modelling | Actively sharpens domain language, rules, boundaries, and lifecycles through edge-case scenarios, then records crystallised glossary entries and decisions. | sonnet / sonnet | read/edit/write |

### Tool Access

Every agent except the two orchestrators declares `allowed-tools` in its frontmatter (a Devin
CLI custom-subagent field — see `docs.devin.ai/cli/subagents#custom-subagents`), enforced by
the runtime rather than left to convention:

- **read-only** — `read`, `grep`, `glob`. Covers every review/discussion persona: the
  orchestrator passes plan and file *content* directly into their prompt (never just paths),
  so these agents reason over what they're given and can't edit or run shell commands.
- **read-only + exec** — adds `exec`, used by `historian` for historical analysis and
  `repo-investigator` for non-mutating history, test, and static-analysis verification.
- **read-only + web_search** — adds `web_search`, used by `security-analyst` and
  `dependency-reviewer` for live CVE/advisory lookups.
- **unrestricted** — `orchestrator` and `iterative-orchestrator` have no `allowed-tools` field
  and keep full tool access (including `write`, `edit`, `exec`, `run_subagent`), since they
  are the only agents that actually implement changes and spawn other subagents.
- `docs-updater` edits and creates files in `/docs` directly, so it gets `read`, `glob`,
  `grep`, `edit`, `write`, `exec`.
- `domain-modeller` records crystallised glossary entries and domain decisions in established
  project files, so it gets `read`, `glob`, `grep`, `edit`, `write` but no shell access.

---

## Skills

Skills are top-level commands that can be invoked by the user to drive a complete workflow.

| Skill | Invocation | What it does |
|-------|------------|--------------|
| `/plan-task` | `<task description>` | Full planning-to-execution pipeline. Actively models changed domains, runs 3 analysts and a 6-persona debate, records accepted architectural decisions, decomposes the plan into tracer-bullet tickets, then hands off to the Orchestrator. |
| `/ship` | `<task description>` | Short alias for the Orchestrator workflow: plan, review, implement, test, and raise a PR. |
| `/analyse-bug` | `<bug description>` | Structured root cause analysis pipeline. Correlates live data, ranks hypotheses, runs a multi-persona discussion, and writes `ROOT-CAUSE.md` only after live-data confirmation. |
| `/verify-fix` | `<ROOT-CAUSE.md> [--diff <diff>]` | Post-implementation verification. Confirms the root cause is addressed, checks for partial fixes, and detects regressions. |
| `/review-pr` | `<PR URL>` | PR review against requirements, coding standards, and backwards compatibility. Checks upgrade paths, mixed-version deployments, public contracts, persisted data, migration/versioning obligations, and rollback safety before presenting a consolidated PASS/FAIL verdict. |
| `/review-plans` | `<plan file>` | Adversarial review. Two agents independently attack the plan for fatal flaws and feasibility gaps against the actual codebase. |
| `/investigate-repo` | `<question \| markdown \| path-to-markdown>` | Read-only investigation of a repository question or every finding in a Markdown audit, including evidence-backed production-reachability and dead-code checks. |
| `/iterate` | `[route or all]` | Iterative UI fix loop. Routes through specialist agents, captures, analyses, fixes, and re-verifies one route at a time, raising a single PR. |
| `/ui-review` | `[route or all]` | Screenshot-driven UX review. Configured via `.claude/ui-review.json`; captures, analyses, fixes, and re-verifies each route. |
| `/quality-audit` | `[path \| glob \| diff \| (empty)]` | Parallel code quality audit. Checks SOLID violations, naming conventions, cyclomatic/cognitive complexity, and clean-code smells across a path, a diff, or the whole repo. |
| `/retrospective` | `[task name / PR / bug]` | Post-task knowledge extraction. Reconstructs the session, routes reusable learnings to `bugs/`, `docs/`, `CLAUDE.md`, or `~/.claude/CLAUDE.md`, and proposes process improvements. |
| `/adr-drafter` | `<decision description>` | Draft an Architecture Decision Record following the repo's own ADR conventions or a sensible default house style. |
| `/test-failure-triager` | `<test output or description>` | Classify failing tests as production bug, test bug, or flake, with a recommended next step. Works across any test framework. |
| `/tdd` | `<feature or fix slice>` | Execute test-driven development through agreed public seams, one red-green-refactor vertical slice at a time. Model-invoked automatically during feature and bug implementation. |
| `/prototype` | `<question to answer>` | Build an isolated throwaway experiment for comparing product, UI, state, interaction, or technical design alternatives before production implementation. |
| `/architecture-audit` | `[subsystem, pain point, or path]` | Run an evidence-backed architecture survey across hotspots, ownership, module depth, coupling, test seams, and evolution risk without implementing changes. |
| `/handoff` | `[next-session focus]` | Write a temporary, redacted session handoff that references existing artifacts and gives another agent ordered continuation steps. |
| `/resolving-merge-conflicts` | `[merge context]` | Resolve an in-progress merge or rebase conflict from both sides' primary intent, with explicit safety and completion gates. |
| `/writing-for-agents` | `<instruction-writing task>` | Reference discipline for reliable agent instructions, context pointers, progressive disclosure, completion criteria, and sources of truth. Model-invoked when agent-consumed files are edited. |

---

## Hooks

Hooks are shell scripts that run automatically at specific points in the Devin CLI / Claude Code lifecycle. The canonical definition lives in `hooks/hooks.json` and the scripts in `hooks/scripts/`. The install scripts symlink `hooks.json` to `~/.claude/settings.local.json`, where both Devin CLI and Claude Code pick it up automatically.

| Hook | Events | What it does |
|------|--------|--------------|
| `send-ai-alert.sh` / `send-ai-alert.ps1` | `Stop`, `Notification`, `SessionEnd` | POSTs an alert to an external API when the agent stops for input, sends a notification, or the session ends. Derives `repo` from `git remote` (supports Azure DevOps and GitHub/GitLab URLs). Looks up the session's real title and last agent message from the local Devin CLI `sessions.db` (via `session-info.py`) for `taskDescription` and `reason`, falling back to the current git branch/directory name if the DB lookup is unavailable. Fire-and-forget — never blocks the agent. |
| `session-info.py` | (helper, not a hook) | Queries Devin CLI's local `sessions.db` (SQLite) for a session's `title` and most recent non-empty assistant message, given a `session_id`. Used by `send-ai-alert.*`. Always exits 0 and prints `{"title": null, "last_message": null}` on any failure. |

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `ECHO_ALERT_API_KEY` | Yes | API key for the alert endpoint. The hook silently exits if this is not set. |

Set the API key as a persistent environment variable before running the install script:

**Windows (PowerShell):**
```powershell
[Environment]::SetEnvironmentVariable('ECHO_ALERT_API_KEY', '<your-key>', 'User')
```

**Mac / Linux:**
```bash
echo 'export ECHO_ALERT_API_KEY="<your-key>"' >> ~/.bashrc
source ~/.bashrc
```

### Alert API Schema

The hook POSTs to `POST /api/alerts/aialert?apikey=<key>` with:

```json
{
  "taskDescription": "Working on branch: feat/my-feature",
  "repo": "org/project/repo",
  "reason": "Agent stopped — waiting for user input",
  "sessionUrl": null,
  "timestamp": "2026-07-18T13:42:33Z"
}
```

`taskDescription`, `repo`, and `reason` are required. `sessionUrl` is optional/nullable (there is no web UI session for local CLI runs). `timestamp` defaults to UTC now.

---

## Repository Layout

```
.
├── agents/
│   ├── accessibility-reviewer/
│   ├── architect/
│   ├── backwards-compatibility-reviewer/
│   ├── code-reviewer/
│   ├── craftsman/
│   ├── dependency-reviewer/
│   ├── director/
│   ├── docs-updater/
│   ├── domain-modeller/
│   ├── guardian/
│   ├── historian/
│   ├── iterative-orchestrator/
│   ├── migration-reviewer/
│   ├── observability-reviewer/
│   ├── orchestrator/
│   ├── performance-reviewer/
│   ├── pragmatist/
│   ├── qa-gatekeeper/
│   ├── repo-investigator/
│   ├── requirements-compliance/
│   ├── security-analyst/
│   ├── senior-engineer/
│   └── user-advocate/
├── skills/
│   ├── adr-drafter/
│   ├── analyse-bug/
│   ├── architecture-audit/
│   ├── handoff/
│   ├── investigate-repo/
│   ├── iterate/
│   ├── plan-task/
│   ├── prototype/
│   ├── quality-audit/
│   ├── resolving-merge-conflicts/
│   ├── retrospective/
│   ├── review-plans/
│   ├── review-pr/
│   ├── ship/
│   ├── tdd/
│   ├── test-failure-triager/
│   ├── ui-review/
│   ├── verify-fix/
│   └── writing-for-agents/
├── install-mac.sh
├── install-windows.ps1
├── install-wsl.sh
├── uninstall-mac.sh
├── uninstall-windows.ps1
├── uninstall-wsl.sh
├── .gitignore
└── hooks/
    ├── hooks.json
    └── scripts/
        └── send-ai-alert.sh
```

---

## Usage

This repo is intended to be cloned into your user profile as `~/.agents` (e.g. `C:\Users\<you>\.agents`). The install scripts derive all tool paths from the parent of this `.agents` directory, so cloning it anywhere else (e.g. alongside your other projects in `~/Documents/GitHub/agents-and-skills-library`) changes what running the scripts with no arguments does — the "parent directory" becomes wherever the repo actually lives, not your home directory. If you didn't clone it to `~/.agents`, either move/re-clone it there first, or always pass an explicit target directory (see step 1).

1. Run the install script for your platform to make the agents, skills, and hooks available to Claude Code. Devin already reads `.agents/` directly — but only because this repo's own `agents/`/`skills/` folders match the layout Devin CLI expects at `~/.agents/{agents,skills}`, which is only true when the repo is cloned exactly at `~/.agents`.

   **Windows:**
   ```powershell
   ./install-windows.ps1
   ```

   `install-windows.ps1` auto-detects which tools to install for: it only touches `.claude` and/or `AppData\Roaming\devin` if that directory already exists under your user profile.

   **Mac / Linux:**
   ```bash
   ./install-mac.sh
   ```

   **WSL (Windows):**
   ```bash
   ./install-wsl.sh
   ```

   `install-wsl.sh` defaults the install target to your WSL home directory (`~`) so the repo can live on a Windows-mounted drive (e.g. `/mnt/c/Users/<you>/.agents`) while the Claude/Devin configuration is installed into the WSL filesystem. It supports the same `--devin` and `--claude` flags as `install-mac.sh`.

   `install-mac.sh` does **not** auto-detect existing tool directories — it defaults to `--claude` only. Pass `--devin` explicitly to also install Devin symlinks, even if `.devin` already exists:
   ```bash
   ./install-mac.sh --devin      # install Devin agent/skill symlinks only
   ./install-mac.sh --claude     # install rendered Claude definitions only (default)
   ./install-mac.sh --claude --devin
   ./install-mac.sh /path/to/project --claude --devin
   ```

   Both scripts also symlink `hooks/hooks.json` to `settings.local.json` in the Claude directory whenever `.claude` is present, regardless of which `--claude`/`--devin` flags you pass.
2. Rerun the installer after changing a canonical agent or skill. Claude definitions are rendered copies rather than symlinks, so they do not update automatically.
3. Start a skill from inside the target project:
   ```
   /plan-task "Add payment retry logic to the checkout service"
   /analyse-bug "Checkout intermittently returns 500 for duplicate requests"
   ```
4. To remove the installed artifacts later, run the matching uninstall script:

   **Windows:**
   ```powershell
   ./uninstall-windows.ps1
   ```

   **Mac / Linux:**
   ```bash
   ./uninstall-mac.sh
   ```

   **WSL (Windows):**
   ```bash
   ./uninstall-wsl.sh
   ```

   `uninstall-mac.sh` and `uninstall-wsl.sh` remove Claude and/or Devin artifacts according to the same `--claude`/`--devin` flags as the installer. `uninstall-wsl.sh` defaults the target to `~` to match `install-wsl.sh`. `uninstall-windows.ps1` auto-detects both installations and takes no flags. All uninstallers also remove the managed hooks artifact.

---

## Models

Canonical definitions use Devin CLI short names. The installers render a runtime-specific `model:` value for Claude Code while leaving the canonical Devin definition unchanged:

| Purpose | Devin CLI | Claude Code |
|---------|-----------|-------------|
| Deep reasoning and decisions | `opus` | `opus` |
| Balanced senior review | `sonnet` | `sonnet` |
| Fast, cost-efficient checks | `swe` | `haiku` |

`opus` and `sonnet` are shared aliases. `swe` is Devin-specific and maps to Claude Code's fast `haiku` tier. The mapping is explicit and installation fails for an unmapped model, so a new alias cannot silently produce an invalid Claude definition.

Keep model names in canonical `model:` frontmatter valid for Devin CLI. When adding a model outside `opus`, `sonnet`, or `swe`, add and document its Claude mapping in both installers after confirming that each runtime supports the intended target.
