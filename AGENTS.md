# Alert hook verification

When changing `hooks/scripts/`, run from the repository root:

```sh
bash -n hooks/scripts/send-ai-alert.sh
powershell.exe -NoProfile -Command "$null=[System.Management.Automation.PSParser]::Tokenize((Get-Content -Raw 'hooks/scripts/send-ai-alert.ps1'),[ref]$null)"
```

Then smoke-test the filter path with a simulated event (bogus endpoint and key so nothing real is sent):

```sh
echo '{"hook_event_name":"SessionEnd","reason":"clear","session_id":"nonexistent"}' | ECHO_ALERT_API_KEY=x ECHO_ALERT_API_BASE=http://127.0.0.1:1 bash hooks/scripts/send-ai-alert.sh
```

There is no automated test suite for these scripts yet (`test_alert_hooks.py` referenced previously does not exist).

Keep `send-ai-alert.sh` and `send-ai-alert.ps1` behavior in sync and bump `SCRIPT_VERSION`/`$ScriptVersion` in both — the live user-level config `%APPDATA%\devin\config.json` invokes the .ps1, while this repo's `hooks/hooks.json` invokes the .sh. Alerts tag the emitting script + version in the reason field, which is how you tell which one fired.

# Windows shell gotchas (Git Bash / MSYS)

- MSYS rewrites arguments that look like POSIX paths. `git show origin/main:.devops/foo.yaml` and similar `rev:path` args can get mangled — prefix with `MSYS_NO_PATHCONV=1` when a `git show`/`git checkout <rev> -- <path>`-style command unexpectedly fails.
- In a linked worktree, `.git` is a file (`gitdir: ...`), not a directory — `cat .git` to find the real git dir; don't `ls .git/` expecting objects/refs.
- To free a port: `netstat -ano | grep :<port>` for the PID, then `taskkill //PID <pid> //F` (double slashes in Git Bash).
- Prefer the `exec` tool's `workdir` parameter over prefixing every command with `cd`.
