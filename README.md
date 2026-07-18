# AI Agent & Skill Library

A central repository of reusable agent definitions, command skills, and lifecycle hooks for Claude Code and Devin CLI. This repo is the canonical source. Devin reads `.agents/` directly; the install scripts symlink agents, skills, and hooks into the directories where Claude Code and Devin CLI expect them.

- `install-windows.ps1` / `install-mac.sh` — creates symlinks for agents, skills, and hooks; removes stale Devin copies. Skips any component whose source does not exist.
- `uninstall-windows.ps1` / `uninstall-mac.sh` — removes the symlinks created by the install script.

---

## Agents

Agents are discussion personas and reviewers that can be invoked by the orchestrator or by the `/ship`, `/plan-task`, `/iterate`, and `/ui-review` skills.

| Agent | Stage | Role | Model |
|-------|-------|------|-------|
| `orchestrator` | Workflow | Main execution workflow: plan, review, implement, test, and raise a PR. | opus |
| `iterative-orchestrator` | Workflow | Autonomous per-route UI fix loop: capture, analyse, fix, re-verify, and raise a single PR. | opus |
| `director` | Discussion | Binding decision maker. Synthesises all debate positions into `DECISION.md` with `PROCEED` / `PROCEED WITH MODIFICATIONS` / `DEFER` / `REJECT`. | opus |
| `senior-engineer` | Plan | Validates implementation plans against engineering standards (architecture, code quality, API design, performance, resilience, observability, testing). | sonnet |
| `qa-gatekeeper` | Plan & Diff | Dual-mode QA reviewer: plan mode checks testability, implementation mode checks committed tests against the test strategy. | swe |
| `security-analyst` | Plan & Diff | Two-pass threat model (STRIDE) and standards compliance covering OWASP, GDPR, PCI-DSS, business logic, abuse, and supply chain. | sonnet |
| `guardian` | Discussion | Principal Engineer production-safety persona. Holds the Safety Veto for data loss, security breach, and payment corruption. | sonnet |
| `pragmatist` | Discussion | Complexity challenger and MVP champion. Pushes for the minimum shippable slice and probability-grounded risk estimates. | sonnet |
| `craftsman` | Discussion | Code-quality and test-first champion. Owns the Test-First Strategy table and enforces SOLID. | sonnet |
| `architect` | Discussion | Principal Architect. Reviews service boundaries, data ownership, coupling, abstraction correctness, and evolution risk. | sonnet |
| `user-advocate` | Discussion | End-user perspective. Traces user journeys, edge cases, and accidental complexity in the UX. | sonnet |
| `historian` | Discussion | Institutional memory guardian. Cross-references plans against git history, past incidents, and documented patterns. | sonnet |
| `code-reviewer` | Diff | Reviews the concrete diff against the approved plan for bugs, plan-drift, and standard violations. | swe |
| `accessibility-reviewer` | Plan & Diff | Conditional reviewer for UI changes. Checks WCAG 2.2 Level AA, keyboard operability, ARIA, and touch targets. | haiku |
| `dependency-reviewer` | Plan & Diff | Conditional reviewer for package changes. Checks supply chain, maintenance, license, necessity, transitive deps, and CVEs. | swe |
| `migration-reviewer` | Plan & Diff | Conditional reviewer for schema and data migrations. Checks zero-downtime compatibility, sequencing, rollback, and scale. | sonnet |
| `observability-reviewer` | Diff | Verifies new code paths have structured logging, metrics, tracing, and production-debuggable signals. | swe |
| `performance-reviewer` | Diff | Checks for N+1 queries, algorithmic complexity, missing indexes, unbounded fetches, caching gaps, and memory leaks. | swe |
| `docs-updater` | Utility | Keeps `/docs` folder files in sync with current code, API contracts, and CLI flags. | swe |

---

## Skills

Skills are top-level commands that can be invoked by the user to drive a complete workflow.

| Skill | Invocation | What it does |
|-------|------------|--------------|
| `/plan-task` | `<task description>` | Full planning-to-execution pipeline. Runs 3 parallel analysts, a 6-persona structured debate, a binding Director decision, then hands off to the Orchestrator to implement and raise a PR. |
| `/ship` | `<task description>` | Short alias for the Orchestrator workflow: plan, review, implement, test, and raise a PR. |
| `/analyse-bug` | `<bug description>` | Structured root cause analysis pipeline. Correlates live data, ranks hypotheses, runs a multi-persona discussion, and writes `ROOT-CAUSE.md` only after live-data confirmation. |
| `/verify-fix` | `<ROOT-CAUSE.md> [--diff <diff>]` | Post-implementation verification. Confirms the root cause is addressed, checks for partial fixes, and detects regressions. |
| `/review-plans` | `<plan file>` | Adversarial review. Two agents independently attack the plan for fatal flaws and feasibility gaps against the actual codebase. |
| `/iterate` | `[route or all]` | Iterative UI fix loop. Routes through specialist agents, captures, analyses, fixes, and re-verifies one route at a time, raising a single PR. |
| `/ui-review` | `[route or all]` | Screenshot-driven UX review. Configured via `.claude/ui-review.json`; captures, analyses, fixes, and re-verifies each route. |
| `/retrospective` | `[task name / PR / bug]` | Post-task knowledge extraction. Reconstructs the session, routes reusable learnings to `bugs/`, `docs/`, `CLAUDE.md`, or `~/.claude/CLAUDE.md`, and proposes process improvements. |

---

## Hooks

Hooks are shell scripts that run automatically at specific points in the Devin CLI / Claude Code lifecycle. The canonical definition lives in `hooks/hooks.json` and the scripts in `hooks/scripts/`. The install scripts symlink `hooks.json` to `~/.claude/settings.local.json`, where both Devin CLI and Claude Code pick it up automatically.

| Hook | Events | What it does |
|------|--------|--------------|
| `send-ai-alert.sh` | `Stop`, `Notification`, `SessionEnd` | POSTs an alert to an external API when the agent stops for input, sends a notification, or the session ends. Derives `repo` from `git remote` (supports Azure DevOps and GitHub/GitLab URLs) and `taskDescription` from the current branch. Fire-and-forget — never blocks the agent. |

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
  "timestamp": "2026-07-18T13:42:33Z"
}
```

`taskDescription`, `repo`, and `reason` are required. `timestamp` defaults to UTC now.

---

## Repository Layout

```
.
├── agents/
│   ├── accessibility-reviewer/
│   ├── architect/
│   ├── code-reviewer/
│   ├── craftsman/
│   ├── dependency-reviewer/
│   ├── director/
│   ├── docs-updater/
│   ├── guardian/
│   ├── historian/
│   ├── iterative-orchestrator/
│   ├── migration-reviewer/
│   ├── observability-reviewer/
│   ├── orchestrator/
│   ├── performance-reviewer/
│   ├── pragmatist/
│   ├── qa-gatekeeper/
│   ├── security-analyst/
│   ├── senior-engineer/
│   └── user-advocate/
├── skills/
│   ├── analyse-bug/
│   ├── iterate/
│   ├── plan-task/
│   ├── retrospective/
│   ├── review-plans/
│   ├── ship/
│   ├── ui-review/
│   └── verify-fix/
├── install-mac.sh
├── install-windows.ps1
├── uninstall-mac.sh
├── uninstall-windows.ps1
├── .gitignore
└── hooks/
    ├── hooks.json
    └── scripts/
        └── send-ai-alert.sh
```

---

## Usage

This repo is intended to be cloned into your user profile as `~/.agents` (e.g. `C:\Users\<you>\.agents`). The install scripts derive all tool paths from the parent of this `.agents` directory.

1. Run the install script for your platform to make the agents and skills available to Claude Code. Devin already reads `.agents/` directly.

   **Windows:**
   ```powershell
   ./install-windows.ps1
   ```

   **Mac / Linux:**
   ```bash
   ./install-mac.sh
   ```

   Only the tools whose directories exist (`.claude` and/or `.devin` / `AppData\Roaming\devin`) are touched.

   The Mac installer also supports optional flags and a target directory:
   ```bash
   ./install-mac.sh --devin      # install Devin symlinks only
   ./install-mac.sh --claude     # install Claude symlinks only (default)
   ./install-mac.sh --claude --devin
   ./install-mac.sh /path/to/project --claude --devin
   ```
2. Start a skill from inside the target project:
   ```
   /plan-task "Add payment retry logic to the checkout service"
   /analyse-bug "Checkout intermittently returns 500 for duplicate requests"
   ```
3. To remove the Claude Code symlinks later, run the matching uninstall script:

   **Windows:**
   ```powershell
   ./uninstall-windows.ps1
   ```

   **Mac / Linux:**
   ```bash
   ./uninstall-mac.sh
   ```

   The Mac uninstaller supports the same optional flags as the installer.

---

## Models

The agent definitions specify a preferred model for each role:

- `opus` — large-model reasoning and decision-making.
- `sonnet` — balanced reasoning for senior review, security, architecture, and discussion.
- `haiku` — fast, focused checks such as accessibility.
- `swe` — software engineering optimised review and code analysis.
