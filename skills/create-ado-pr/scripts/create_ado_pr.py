import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--org", required=True)
    parser.add_argument("--project", required=True)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--source", required=True)
    parser.add_argument("--target", required=True)
    parser.add_argument("--title", required=True)
    parser.add_argument("--description-file", required=True, type=Path)
    parser.add_argument("--work-item", action="append", default=[])
    parser.add_argument("--execute", action="store_true")
    return parser.parse_args()


def main():
    args = parse_args()
    description = args.description_file.read_text(encoding="utf-8")
    if not description.strip():
        raise SystemExit("Description file is empty")
    if args.source == args.target:
        raise SystemExit("Source and target branches must differ")

    command = [
        "az", "repos", "pr", "create",
        "--source-branch", args.source,
        "--target-branch", args.target,
        "--title", args.title,
        "--description", *description.splitlines(),
        "--org", args.org,
        "--project", args.project,
        "--repository", args.repository,
        "--output", "json",
        "--only-show-errors",
    ]
    if args.work_item:
        command.extend(["--work-items", *args.work_item])

    preview = {
        "command": command,
        "description_sha256": hashlib.sha256(description.encode("utf-8")).hexdigest(),
        "execute": args.execute,
    }
    if not args.execute:
        print(json.dumps(preview, indent=2))
        return

    az = shutil.which("az")
    if not az:
        raise SystemExit("az CLI not found on PATH")
    with tempfile.TemporaryDirectory() as tmp:
        desc_file, title_file = Path(tmp, "description.md"), Path(tmp, "title.txt")
        desc_file.write_text(description, encoding="utf-8")
        title_file.write_text(args.title, encoding="utf-8")
        run = list(command)
        run[run.index("--title") + 1] = f"@{title_file}"
        i = run.index("--description")
        j = next(k for k in range(i + 1, len(run)) if run[k].startswith("--"))
        run[i + 1:j] = [f"@{desc_file}"]
        result = subprocess.run([az, *run[1:]], text=True, capture_output=True)
    if result.returncode:
        sys.stderr.write(result.stderr)
        raise SystemExit(result.returncode)
    print(result.stdout)
    try:
        pr = json.loads(result.stdout)
        print(f"PR_ID={pr['pullRequestId']}", file=sys.stderr)
    except (ValueError, KeyError, TypeError):
        pass


if __name__ == "__main__":
    main()
