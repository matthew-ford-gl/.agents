# AI Agent & Skill Library

A central repository of reusable agent definitions and command skills for Claude and Devin. This repo is the canonical source; the PowerShell scripts in the root symlink them into the tool-specific directories so the agents are picked up by each assistant.

- `agents-symlink.ps1` — links `agents/<name>/AGENT.md` into `~/.claude/agents/<name>.md` and `~/.devin/agents/<name>`.
- `skills-symlink.ps1` — links `skills/<name>` into `~/.claude/skills/<name>` and removes stale Devin duplicates.

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
├── agents-symlink.ps1
├── skills-symlink.ps1
├── .gitignore
└── hooks/
    ├── hooks.json
    └── scripts/
```

---

## Usage

1. Run the symlink scripts to make the agents and skills available to Claude and Devin:
   ```powershell
   ./agents-symlink.ps1
   ./skills-symlink.ps1
   ```
2. Start a skill from inside the target project:
   ```
   /plan-task "Add payment retry logic to the checkout service"
   /analyse-bug "Checkout intermittently returns 500 for duplicate requests"
   ```
3. The orchestrator/workflow agents will use the relevant reviewer agents as needed.

---

## Models

The agent definitions specify a preferred model for each role:

- `opus` — large-model reasoning and decision-making.
- `sonnet` — balanced reasoning for senior review, security, architecture, and discussion.
- `haiku` — fast, focused checks such as accessibility.
- `swe` — software engineering optimised review and code analysis.
