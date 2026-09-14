import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--org", required=True)
    parser.add_argument("--project", required=True)
    parser.add_argument("--type", required=True)
    parser.add_argument("--title", required=True)
    parser.add_argument("--description-file", type=Path)
    parser.add_argument("--discussion-file", type=Path)
    parser.add_argument("--area")
    parser.add_argument("--iteration")
    parser.add_argument("--assigned-to")
    parser.add_argument("--field", action="append", default=[])
    parser.add_argument("--parent", type=int)
    parser.add_argument("--execute", action="store_true")
    return parser.parse_args()


def read_optional(path, label):
    if path is None:
        return None
    content = path.read_text(encoding="utf-8")
    if not content.strip():
        raise SystemExit(f"{label} file is empty")
    return content


def main():
    args = parse_args()
    if not args.title.strip() or not args.type.strip():
        raise SystemExit("Title and type cannot be empty")
    for field in args.field:
        name, separator, value = field.partition("=")
        if not separator or not name.strip() or not value:
            raise SystemExit(f"Invalid field assignment: {field}")

    description = read_optional(args.description_file, "Description")
    discussion = read_optional(args.discussion_file, "Discussion")
    create = [
        "az", "boards", "work-item", "create", "--org", args.org,
        "--project", args.project, "--type", args.type, "--title", args.title,
    ]
    for option, value in (
        ("--description", description),
        ("--discussion", discussion),
        ("--area", args.area),
        ("--iteration", args.iteration),
        ("--assigned-to", args.assigned_to),
    ):
        if value is not None:
            create.extend([option, value])
    if args.field:
        create.extend(["--fields", *args.field])
    create.extend(["--output", "json", "--only-show-errors"])

    preview = {"create_command": create, "parent": args.parent, "execute": args.execute}
    for label, content in (("description", description), ("discussion", discussion)):
        if content is not None:
            preview[f"{label}_sha256"] = hashlib.sha256(content.encode("utf-8")).hexdigest()
    if not args.execute:
        print(json.dumps(preview, indent=2))
        return

    result = subprocess.run(create, text=True, capture_output=True)
    if result.returncode:
        sys.stderr.write(result.stderr)
        raise SystemExit(result.returncode)
    item = json.loads(result.stdout)
    item_id = item.get("id")
    if not item_id:
        sys.stderr.write("Create response did not contain a work item ID\n")
        raise SystemExit(1)

    relation = None
    if args.parent is not None:
        relation_command = [
            "az", "boards", "work-item", "relation", "add", "--id", str(item_id),
            "--relation-type", "parent", "--target-id", str(args.parent),
            "--org", args.org, "--output", "json", "--only-show-errors",
        ]
        relation_result = subprocess.run(relation_command, text=True, capture_output=True)
        if relation_result.returncode:
            sys.stderr.write(json.dumps({"created_work_item_id": item_id, "failed_command": relation_command}) + "\n")
            sys.stderr.write(relation_result.stderr)
            raise SystemExit(relation_result.returncode)
        relation = json.loads(relation_result.stdout) if relation_result.stdout.strip() else None
    print(json.dumps({"work_item": item, "parent_relation": relation}))


if __name__ == "__main__":
    main()
