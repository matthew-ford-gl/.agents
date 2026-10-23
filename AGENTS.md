# Alert hook verification

When changing `hooks/scripts/`, run from the repository root:

```sh
python -m unittest discover -s hooks/scripts -p test_alert_hooks.py -v
bash -n hooks/scripts/send-ai-alert.sh
```

The tests use temporary SQLite databases and mock alert delivery and sound. Bash and PowerShell integration cases skip when their executable is unavailable. Keep verification isolated from the real Echo endpoint.

# Windows shell gotchas (Git Bash / MSYS)

- MSYS rewrites arguments that look like POSIX paths. `git show origin/main:.devops/foo.yaml` and similar `rev:path` args can get mangled — prefix with `MSYS_NO_PATHCONV=1` when a `git show`/`git checkout <rev> -- <path>`-style command unexpectedly fails.
- In a linked worktree, `.git` is a file (`gitdir: ...`), not a directory — `cat .git` to find the real git dir; don't `ls .git/` expecting objects/refs.
- To free a port: `netstat -ano | grep :<port>` for the PID, then `taskkill //PID <pid> //F` (double slashes in Git Bash).
- Prefer the `exec` tool's `workdir` parameter over prefixing every command with `cd`.
