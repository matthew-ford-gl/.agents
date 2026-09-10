#!/usr/bin/env python3
import argparse
import json
import subprocess
import sys


def run_json(*args):
    result = subprocess.run(args, check=True, capture_output=True, text=True)
    return json.loads(result.stdout or "null")


def classify_status(value):
    status = (value or "").lower()
    if status in {"approved", "succeeded", "success", "completed"}:
        return "green"
    if status in {"queued", "running", "pending", "in_progress", "expected"}:
        return "waiting"
    if status in {"expired", "stale"}:
        return "requeue-candidate"
    if status in {"rejected", "failed", "failure", "broken", "cancelled", "timed_out", "action_required"}:
        return "actionable-failure"
    return "other"


def ado_snapshot(pr):
    metadata = run_json("az", "repos", "pr", "show", "--id", pr, "-o", "json")
    project = metadata["repository"]["project"]["id"]
    repo = metadata["repository"]["id"]
    route = [f"project={project}", f"repositoryId={repo}", f"pullRequestId={pr}"]
    policy_result = run_json("az", "repos", "pr", "policy", "list", "--id", pr, "-o", "json")
    policies = policy_result.get("value", []) if isinstance(policy_result, dict) else policy_result
    threads = run_json("az", "devops", "invoke", "--area", "git", "--resource", "pullRequestThreads", "--route-parameters", *route, "--api-version", "7.1", "-o", "json")
    iterations = run_json("az", "devops", "invoke", "--area", "git", "--resource", "pullRequestIterations", "--route-parameters", *route, "--api-version", "7.1", "-o", "json")
    iteration_values = iterations.get("value", iterations or [])
    latest = max((item.get("id", 0) for item in iteration_values), default=0)
    changes = run_json("az", "devops", "invoke", "--area", "git", "--resource", "pullRequestIterationChanges", "--route-parameters", *route, f"iterationId={latest}", "--api-version", "7.1", "-o", "json") if latest else {"changeEntries": []}
    unresolved = []
    for thread in threads.get("value", threads or []):
        comments = [comment for comment in thread.get("comments", []) if comment.get("commentType", "text") == "text"]
        if thread.get("status", "").lower() in {"active", "pending"} and comments:
            unresolved.append({"id": thread.get("id"), "status": thread.get("status"), "comments": [{"id": c.get("id"), "author": (c.get("author") or {}).get("displayName"), "content": c.get("content")} for c in comments]})
    normalized_policies = []
    for policy in policies:
        context = policy.get("context") or {}
        status = policy.get("status")
        expired = bool(policy.get("isExpired"))
        normalized_policies.append({"id": policy.get("evaluationId") or policy.get("id"), "name": context.get("displayName") or (policy.get("configuration") or {}).get("type", {}).get("displayName"), "status": status, "classification": "requeue-candidate" if expired else classify_status(status), "build_id": context.get("buildId"), "expired": expired})
    return {
        "platform": "ado", "pr": metadata.get("pullRequestId"), "title": metadata.get("title"), "url": metadata.get("url"),
        "source_branch": metadata.get("sourceRefName"), "target_branch": metadata.get("targetRefName"),
        "source_commit": (metadata.get("lastMergeSourceCommit") or {}).get("commitId"), "target_commit": (metadata.get("lastMergeTargetCommit") or {}).get("commitId"),
        "conflict": metadata.get("mergeStatus") == "conflicts", "merge_status": metadata.get("mergeStatus"), "latest_iteration": latest,
        "changed_files": [entry.get("item", {}).get("path") for entry in changes.get("changeEntries", changes.get("value", [])) if entry.get("item", {}).get("path")],
        "threads": unresolved, "policies": normalized_policies,
        "reviewers": [{"id": r.get("id"), "name": r.get("displayName"), "required": bool(r.get("isRequired")), "vote": r.get("vote")} for r in metadata.get("reviewers", [])],
    }


def github_snapshot(pr):
    fields = "number,title,url,headRefName,baseRefName,headRefOid,baseRefOid,mergeable,mergeStateStatus,files,reviews,statusCheckRollup"
    metadata = run_json("gh", "pr", "view", pr, "--json", fields)
    checks = []
    for check in metadata.get("statusCheckRollup", []):
        status = check.get("conclusion") or check.get("state") or check.get("status")
        checks.append({"id": check.get("detailsUrl"), "name": check.get("name") or check.get("context"), "status": status, "classification": classify_status(status)})
    return {
        "platform": "github", "pr": metadata.get("number"), "title": metadata.get("title"), "url": metadata.get("url"),
        "source_branch": metadata.get("headRefName"), "target_branch": metadata.get("baseRefName"), "source_commit": metadata.get("headRefOid"), "target_commit": metadata.get("baseRefOid"),
        "conflict": metadata.get("mergeable") == "CONFLICTING" or metadata.get("mergeStateStatus") == "DIRTY", "merge_status": metadata.get("mergeStateStatus"),
        "changed_files": [item.get("path") for item in metadata.get("files", [])], "threads": [], "checks": checks,
        "reviews": [{"author": (r.get("author") or {}).get("login"), "state": r.get("state"), "commit": (r.get("commit") or {}).get("oid")} for r in metadata.get("reviews", [])],
        "threads_query_required": True,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("platform", choices=("ado", "github"))
    parser.add_argument("pr")
    parser.add_argument("--output")
    args = parser.parse_args()
    try:
        pr = args.pr.rstrip("/").split("/")[-1] if args.platform == "ado" else args.pr
        snapshot = ado_snapshot(pr) if args.platform == "ado" else github_snapshot(pr)
    except (subprocess.CalledProcessError, KeyError, json.JSONDecodeError) as error:
        detail = error.stderr.strip() if isinstance(error, subprocess.CalledProcessError) and error.stderr else str(error)
        print(json.dumps({"error": detail}, separators=(",", ":")), file=sys.stderr)
        raise SystemExit(1)
    payload = json.dumps(snapshot, separators=(",", ":"))
    if args.output:
        with open(args.output, "w", encoding="utf-8") as target:
            target.write(payload + "\n")
    print(payload)


if __name__ == "__main__":
    main()
