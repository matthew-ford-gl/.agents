import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--org", required=True)
    parser.add_argument("--id", required=True, type=int)
    parser.add_argument("--title")
    parser.add_argument("--description-file", type=Path)
    parser.add_argument("--draft", choices=("true", "false"))
    parser.add_argument("--reviewer", action="append", default=[])
    parser.add_argument("--required-reviewer", action="append", default=[])
    parser.add_argument("--work-item", action="append", default=[])
    parser.add_argument("--execute", action="store_true")
    return parser.parse_args()


def main():
    args = parse_args()
    commands = []
    update = ["az", "repos", "pr", "update", "--id", str(args.id), "--org", args.org]
    description = None
    if args.title is not None:
        if not args.title.strip():
            raise SystemExit("Title cannot be empty")
        update.extend(["--title", args.title])
    if args.description_file:
        description = args.description_file.read_text(encoding="utf-8")
        if not description.strip():
            raise SystemExit("Description file is empty")
        update.extend(["--description", description])
    if args.draft:
        update.extend(["--draft", args.draft])
    if len(update) > 8:
        commands.append(update + ["--output", "json", "--only-show-errors"])
    for required, reviewers in ((False, args.reviewer), (True, args.required_reviewer)):
        if reviewers:
            commands.append([
                "az", "repos", "pr", "reviewer", "add", "--id", str(args.id),
                "--reviewers", *reviewers, "--required", str(required).lower(),
                "--org", args.org, "--output", "json", "--only-show-errors",
            ])
    if args.work_item:
        commands.append([
            "az", "repos", "pr", "work-item", "add", "--id", str(args.id),
            "--work-items", *args.work_item, "--org", args.org,
            "--output", "json", "--only-show-errors",
        ])
    if not commands:
        raise SystemExit("At least one update is required")

    preview = {"commands": commands, "execute": args.execute}
    if description is not None:
        preview["description_sha256"] = hashlib.sha256(description.encode("utf-8")).hexdigest()
    if not args.execute:
        print(json.dumps(preview, indent=2))
        return

    results = []
    for index, command in enumerate(commands):
        result = subprocess.run(command, text=True, capture_output=True)
        if result.returncode:
            sys.stderr.write(json.dumps({"completed_commands": index, "failed_command": command}) + "\n")
            sys.stderr.write(result.stderr)
            raise SystemExit(result.returncode)
        results.append(json.loads(result.stdout) if result.stdout.strip() else None)
    print(json.dumps(results))


if __name__ == "__main__":
    main()
