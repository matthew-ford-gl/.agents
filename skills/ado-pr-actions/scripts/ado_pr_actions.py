import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from urllib.parse import unquote

API_VERSION = "7.1"


def parse_pr_url(url):
    m = re.match(
        r"https?://dev\.azure\.com/([^/]+)/([^/]+)/_git/([^/]+)/pullrequest/(\d+)",
        url.strip(),
    )
    if not m:
        raise SystemExit(f"Cannot parse Azure DevOps PR URL: {url}")
    org, project, repo, pr_id = m.groups()
    return f"https://dev.azure.com/{org}", unquote(project), unquote(repo), int(pr_id)


def route_params(project, repository_id, pr_id, thread_id=None):
    params = {
        "project": project,
        "repositoryId": repository_id,
        "pullRequestId": pr_id,
    }
    if thread_id is not None:
        params["threadId"] = thread_id
    flat = []
    for k, v in params.items():
        flat.extend(["--route-parameters", f"{k}={v}"])
    return flat


def az(args_list):
    return ["az", "devops", "invoke", "--only-show-errors", "--output", "json"] + args_list


def build_command(args):
    org, project, repo, pr_id = args.org, args.project, args.repository, args.pr
    base = ["--org", org, "--api-version", API_VERSION]

    if args.action == "list":
        return az(base + ["--area", "git", "--resource", "pullRequestThreads",
                          *route_params(project, repo, pr_id)])

    if args.action == "show":
        return az(base + ["--area", "git", "--resource", "pullRequestThreads",
                          *route_params(project, repo, pr_id, args.thread_id)])

    if args.action == "comment":
        content = read_content(args)
        body = json.dumps({
            "comments": [{"parentCommentId": 0, "content": content, "commentType": 1}],
            "status": 1,
        })
        return az(base + ["--area", "git", "--resource", "pullRequestThreads",
                          *route_params(project, repo, pr_id),
                          "--http-method", "POST", "--in-file", write_body(body)])

    if args.action == "reply":
        content = read_content(args)
        body = json.dumps({"content": content, "commentType": 1})
        return az(base + ["--area", "git", "--resource", "pullRequestThreadComments",
                          *route_params(project, repo, pr_id, args.thread_id),
                          "--http-method", "POST", "--in-file", write_body(body)])

    if args.action in ("resolve", "reopen", "close", "wontfix"):
        # CommentThreadStatus: unknown=0, active=1, fixed=2, wontFix=3,
        # closed=4, byDesign=5, pending=6
        status = {"resolve": 2, "reopen": 1, "close": 4, "wontfix": 3}[args.action]
        body = json.dumps({"status": status})
        return az(base + ["--area", "git", "--resource", "pullRequestThreads",
                          *route_params(project, repo, pr_id, args.thread_id),
                          "--http-method", "PATCH", "--in-file", write_body(body)])

    raise SystemExit(f"Unknown action: {args.action}")


def read_content(args):
    content = Path(args.content_file).read_text(encoding="utf-8")
    if not content.strip():
        raise SystemExit("Content file is empty")
    return content


def write_body(body):
    import tempfile
    fd, path = tempfile.mkstemp(suffix=".json", prefix="ado-pr-action-")
    with open(fd, "w", encoding="utf-8") as f:
        f.write(body)
    return path


def parse_args():
    p = argparse.ArgumentParser(description="Azure DevOps PR thread/comment actions")
    p.add_argument("action", choices=["list", "show", "comment", "reply",
                                      "resolve", "reopen", "close", "wontfix"])
    p.add_argument("--pr-url", help="Full ADO PR URL; sets org/project/repository/pr")
    p.add_argument("--org")
    p.add_argument("--project")
    p.add_argument("--repository", help="Repository ID (GUID) or name")
    p.add_argument("--pr", type=int, help="Pull request ID")
    p.add_argument("--thread-id", type=int)
    p.add_argument("--content-file", type=Path)
    p.add_argument("--execute", action="store_true",
                   help="Run the az call; without it, print a preview only")
    return p.parse_args()


def main():
    args = parse_args()
    if args.pr_url:
        args.org, args.project, args.repository, args.pr = parse_pr_url(args.pr_url)
    for f in ("org", "project", "repository", "pr"):
        if getattr(args, f) is None:
            raise SystemExit(f"--{f} is required (or pass --pr-url)")
    if args.action in ("show", "reply", "resolve", "reopen", "close", "wontfix") \
            and args.thread_id is None:
        raise SystemExit(f"--thread-id is required for '{args.action}'")
    if args.action in ("comment", "reply") and args.content_file is None:
        raise SystemExit(f"--content-file is required for '{args.action}'")

    command = build_command(args)
    is_read = args.action in ("list", "show")
    body_file = next(
        (command[i + 1] for i, v in enumerate(command[:-1]) if v == "--in-file"),
        None,
    )

    if not args.execute and not is_read:
        print(json.dumps({"command": command, "execute": False}, indent=2))
        if body_file:
            Path(body_file).unlink(missing_ok=True)
        return

    try:
        result = subprocess.run([shutil.which(command[0]) or command[0], *command[1:]], text=True, capture_output=True)
        if result.returncode:
            sys.stderr.write(result.stderr)
            raise SystemExit(result.returncode)
    finally:
        if body_file:
            Path(body_file).unlink(missing_ok=True)

    if args.action == "list":
        threads = json.loads(result.stdout).get("value", [])
        summary = [
            {
                "id": t["id"],
                "status": t.get("status"),
                "comments": len(t.get("comments", [])),
                "first": (t.get("comments") or [{}])[0].get("content", "")[:120],
            }
            for t in threads
        ]
        print(json.dumps(summary, indent=2))
    else:
        print(result.stdout)


if __name__ == "__main__":
    main()
