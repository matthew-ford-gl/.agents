---
name: token-savers
description: "Explains the RTK and Caveman token savers, then installs only their local-only parts on Windows, Linux or macOS after the user approves. Use when asked about saving tokens, cutting agent cost or context, "what is RTK", "what is caveman", or to install, check or remove RTK or Caveman. Not for: Caveman Cloud, adaptive model routing, rtk-proxy, building Caveman middleware into an app, or tuning prompts (use prompt-craft)."
argument-hint: "[explain | install | status | uninstall]"
---

# Token savers: RTK and Caveman

Two free tools that cut tokens. Neither is installed without an explicit yes.

| | RTK | Caveman skill | Caveman CLI (optional) |
|---|---|---|---|
| Cuts | Shell output the agent reads (git, tests, ls, grep). Up to ~90% of that output | Words the agent writes. ~65% less reply text; little effect on total cost | Tool output, logs, JSON and diffs before the model reads them |
| How | Single binary plus an agent hook that rewrites `git status` to `rtk git status` | A skill/rule file | Local proxy and wrapper (`caveman claude`) |
| Needs | Nothing else | Node 18+ | Node 22.13+ |
| Licence | Apache-2.0 + BUSL-1.1 (`rtk-oss` edition is Apache-2.0 only) | Apache-2.0 | Apache-2.0 |

Savings claims are vendor figures. RTK counts only bash output, and the saving shrinks once prompt, history and output tokens are included.

## Local-only boundary

Install only these:

- RTK binary and agent hook. Telemetry ships off; verify it.
- Caveman skill (`npx skills add`). No Caveman code runs at runtime.
- Caveman CLI only if the user asks, with telemetry forced off first.

Never install or enable: `rtk-proxy`, `caveman login`, adaptive model selection/router, Caveman Cloud, or `rtk telemetry enable`. The Caveman CLI telemetry is on by default (opt-out), so every CLI command below runs with `DO_NOT_TRACK=1`.

Installs do download from GitHub, npm, winget or brew. Say so. No prompts, code or command output are sent anywhere by these tools; the model provider still sees whatever the agent sends it today.

## Workflow

### 1. Explain and detect

Show the table above in two or three sentences, then detect state:

```sh
rtk --version && rtk gain     # gain must print a dashboard; otherwise wrong "rtk" (Rust Type Kit) or missing
rtk telemetry status
node --version
caveman --version
```

Detect OS (`uname -s`, or Windows) and which agents exist: Claude Code, Devin, Codex, Gemini CLI, Cursor, Windsurf, Cline, OpenCode.

Done when you can state per tool: installed / missing / wrong package.

### 2. Get approval

Ask the user, using `ask_user_question` where available:

- Which of RTK, Caveman skill, Caveman CLI to install (default: RTK + Caveman skill).
- Which agents to wire up.
- RTK edition: full or `rtk-oss` (Apache-2.0 only).

Stop on no. Do not install on silence.

### 3. Install RTK

Skip if `rtk gain` already works. Pick by OS; use `RTK_EDITION=oss` or `rtk-ai/tap/rtk-oss` for the Apache edition.

| OS | Command |
|---|---|
| Windows | `winget install rtk-ai.rtk` (open a new shell for PATH). Optional: `winget install BurntSushi.ripgrep.MSVC` since some filters need `rg` |
| macOS / Linux | `brew install rtk-ai/tap/rtk` if brew exists, else `curl -fsSL https://raw.githubusercontent.com/rtk-ai/rtk/master/install.sh | sh` (installs to `~/.local/bin`; add to PATH) |

Never `cargo install rtk` (wrong crate); use `cargo install --git https://github.com/rtk-ai/rtk --branch master rtk` if cargo is the only route.

Then wire agents the user chose. Hook edits change agent settings files, so use `--show` first and state the file being modified:

```sh
rtk init -g                      # Claude Code
rtk init -g --codex
rtk init -g --gemini
rtk init -g --agent cursor       # or windsurf, cline, kilocode, droid, ...
```

The hook fires only on shell tool calls, not built-in Read/Grep/Glob. The agent must be restarted.

Done when `rtk --version` and `rtk gain` succeed, `rtk telemetry status` shows `enabled: no`, and `rtk init -g --show` lists the chosen agent.

### 4. Install the Caveman skill

Requires Node 18+. Run with telemetry env off:

```sh
DO_NOT_TRACK=1 DISABLE_TELEMETRY=1 npx skills add JuliusBrussee/caveman -g
```

PowerShell: `$env:DO_NOT_TRACK=1; $env:DISABLE_TELEMETRY=1; npx skills add JuliusBrussee/caveman -g`.

Add `-a <agent>` per chosen agent (`devin`, `codex`, `gemini-cli`, `windsurf`, `cline`, ...); without it the installer asks. Do not use the unified `install.sh`/`install.ps1` one-liner: it also wires hooks and plugins for every detected agent.

The skill does not auto-start for most agents; tell the user to type `/caveman` (`$caveman` in Codex) and say `stop caveman` to end it. To make it default, put `{"defaultMode": "caveman"}` in `~/.config/caveman/config.json`.

Done when the skill file exists in the agent's skill directory.

### 5. Install the Caveman CLI (only if requested)

Requires Node 22.13+. Set the opt-out before the first command:

```sh
export DO_NOT_TRACK=1
npm install -g @caveman-ai/cli
caveman telemetry off
caveman setup --install      # signed, checksummed binaries into ~/.caveman/bin
caveman telemetry status     # must show off
```

PowerShell: `$env:DO_NOT_TRACK=1`, same commands. Persist the opt-out for hooks started outside a shell: `caveman telemetry off` writes `~/.caveman-cloud/config.json`.

Use `caveman wrap <agent>` for one-off sessions with no persistent config changes. Avoid `caveman <agent>` unless the user accepts it persistently enables the integration (undo: `caveman disable <agent>`). Never run `caveman login`, and decline any prompt to enable model routing.

Done when `caveman telemetry status` reports off and `caveman setup` shows required binaries installed.

### 6. Report

State: what was installed, versions, which agent files changed, telemetry status for each tool, and that a restart is needed. If any step failed, say which and what was left half-done.

## Status and uninstall

- Status: step 1 commands plus `rtk gain` and `caveman stats`.
- Uninstall RTK: `rtk init -g --uninstall`, then `winget uninstall rtk-ai.rtk` or `brew uninstall rtk` or delete `~/.local/bin/rtk`.
- Uninstall Caveman: `caveman disable <agent>` if used, `npm uninstall -g @caveman-ai/cli`, delete `~/.caveman` and `~/.caveman-cloud`, remove the skill with `npx skills remove caveman -g` (check `npx skills --help` first) or delete its folder from the agent's skills directory.
- Confirm before deleting any directory.

## Known limits

- Caveman skill token savings apply to replies only; the effect on total cost is small.
- Docs were read, source was not audited. For a stricter guarantee, run with outbound traffic monitored or firewalled except to the model provider.
