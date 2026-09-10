#!/usr/bin/env python3
import argparse
import json
import os
import pathlib
import re
import subprocess
import tempfile
import uuid


def run(*args):
    return subprocess.run(args, check=True, capture_output=True, text=True).stdout.strip()


def resolve_agent(repo, name):
    candidates = [
        repo / ".devin" / "agents" / name / "AGENT.md",
        repo / ".claude" / "agents" / f"{name}.md",
        pathlib.Path.home() / ".agents" / "agents" / name / "AGENT.md",
        pathlib.Path.home() / ".claude" / "agents" / f"{name}.md",
    ]
    return next((path.resolve() for path in candidates if path.is_file()), None)


def configured_root(repo):
    candidates = []
    if os.environ.get("CONTEXT_STORAGE_PATH"):
        candidates.append(pathlib.Path(os.path.expandvars(os.path.expanduser(os.environ["CONTEXT_STORAGE_PATH"]))))
    for config in (repo / ".devin" / "agent-context.json", pathlib.Path.home() / ".config" / "devin" / "agent-context.json"):
        if config.is_file():
            try:
                value = json.loads(config.read_text(encoding="utf-8")).get("root")
            except (OSError, json.JSONDecodeError):
                continue
            if value:
                root = pathlib.Path(os.path.expandvars(os.path.expanduser(value)))
                candidates.append(root if root.is_absolute() else config.parent / root)
    candidates.extend((pathlib.Path(tempfile.gettempdir()), repo / ".tmp"))
    for candidate in candidates:
        try:
            candidate = candidate.expanduser().resolve()
            candidate.mkdir(parents=True, exist_ok=True)
            probe = candidate / f".land-pr-probe-{uuid.uuid4()}"
            probe.write_text("ok", encoding="utf-8")
            probe.unlink()
            return candidate
        except OSError:
            continue
    raise SystemExit("no writable context root")


def safe(value):
    return re.sub(r"[^A-Za-z0-9._-]+", "-", value).strip("-._") or "unknown"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("pr")
    parser.add_argument("--session-id", default=os.environ.get("DEVIN_SESSION_ID") or str(uuid.uuid4()))
    parser.add_argument("--create", action="store_true")
    args = parser.parse_args()

    repo = pathlib.Path(run("git", "rev-parse", "--show-toplevel")).resolve()
    remote = run("git", "remote", "get-url", "origin")
    platform = "github" if "github.com" in remote else "ado" if "dev.azure.com" in remote or "visualstudio.com" in remote else "unknown"
    status = run("git", "status", "--porcelain=v1", "--untracked-files=all")
    repo_name = safe(repo.name)
    pr_id = safe(args.pr.rstrip("/").split("/")[-1])
    root = configured_root(repo).expanduser().resolve()
    session = root / repo_name / safe(args.session_id)
    context = session / "land-pr"
    persistent = root / repo_name
    paths = {
        "context_dir": context,
        "checkpoint_path": persistent / f"land-pr-checkpoint-{pr_id}.json",
        "handoff_path": persistent / f"land-pr-handoff-{pr_id}.md",
        "telemetry_path": context / "telemetry.jsonl",
    }
    if args.create:
        context.mkdir(parents=True, exist_ok=True)
        if context.parent != session or session.parent != persistent:
            raise SystemExit("context path failed descendant check")
        for child in ("threads", "ci-logs", "standards"):
            (context / "current-batch" / child).mkdir(parents=True, exist_ok=True)

    agents = {name: resolve_agent(repo, name) for name in ("pr-fixer", "code-reviewer")}
    local_context = root == (repo / ".tmp").resolve()
    ignored = subprocess.run(("git", "check-ignore", "-q", str(repo / ".tmp")), capture_output=True).returncode == 0 if local_context else True
    result = {
        "repo": str(repo),
        "remote": remote,
        "platform": platform,
        "branch": run("git", "branch", "--show-current"),
        "clean": not bool(status),
        "dirty_paths": status.splitlines(),
        "agents": {name: str(path) if path else None for name, path in agents.items()},
        "repository_tmp_requires_ignore": local_context and not ignored,
        **{key: str(value) for key, value in paths.items()},
    }
    print(json.dumps(result, separators=(",", ":")))


if __name__ == "__main__":
    main()
