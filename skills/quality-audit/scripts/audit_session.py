#!/usr/bin/env python3
import argparse
import hashlib
import json
import os
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path

MAX_FILES = 15
MAX_BYTES = 30 * 1024
MAX_ATTEMPTS = 2
DIMENSIONS = ("SOLID", "Naming & Clean Code", "Complexity", "Code Smells & Duplication")


def slug(value):
    result = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return result or "audit"


def atomic_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(value, handle, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def context_root(repo, explicit=None):
    candidates = []
    if explicit:
        candidates.append(Path(explicit))
    if os.environ.get("CONTEXT_STORAGE_PATH"):
        candidates.append(Path(os.path.expandvars(os.path.expanduser(os.environ["CONTEXT_STORAGE_PATH"]))))
    for config in (repo / ".devin" / "agent-context.json", Path.home() / ".config" / "devin" / "agent-context.json"):
        if not config.is_file():
            continue
        try:
            value = json.loads(config.read_text(encoding="utf-8")).get("root")
        except (OSError, json.JSONDecodeError):
            continue
        if value:
            candidate = Path(os.path.expandvars(os.path.expanduser(value)))
            candidates.append(candidate if candidate.is_absolute() else config.parent / candidate)
    candidates.extend((Path(tempfile.gettempdir()), repo / ".tmp"))
    for candidate in candidates:
        try:
            candidate = candidate.expanduser().resolve()
            candidate.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(prefix=".quality-audit-probe-", dir=candidate):
                pass
            return candidate
        except OSError:
            continue
    raise ValueError("no writable context root")


def manifest_entries(manifest_path, repo):
    raw = load_json(manifest_path)
    raw = raw.get("files", raw) if isinstance(raw, dict) else raw
    entries = []
    for item in raw:
        relative = item["path"] if isinstance(item, dict) else item
        relative = Path(relative).as_posix()
        source = (repo / relative).resolve()
        try:
            source.relative_to(repo)
        except ValueError as error:
            raise ValueError(f"manifest path escapes repository: {relative}") from error
        if not source.is_file():
            raise ValueError(f"manifest file does not exist: {relative}")
        entries.append({"path": relative, "bytes": source.stat().st_size})
    paths = [entry["path"] for entry in entries]
    if not entries:
        raise ValueError("manifest is empty")
    if len(paths) != len(set(paths)):
        raise ValueError("manifest contains duplicate paths")
    return sorted(entries, key=lambda entry: entry["path"])


def chunk_entries(entries, start=1):
    chunks = []
    current = []
    current_bytes = 0
    for entry in entries:
        if current and (len(current) == MAX_FILES or current_bytes + entry["bytes"] > MAX_BYTES):
            chunks.append(current)
            current = []
            current_bytes = 0
        current.append(entry)
        current_bytes += entry["bytes"]
        if entry["bytes"] > MAX_BYTES:
            chunks.append(current)
            current = []
            current_bytes = 0
    if current:
        chunks.append(current)
    return [make_chunk(f"C{index:04d}", files) for index, files in enumerate(chunks, start)]


def make_chunk(chunk_id, files, attempt=0, parent=None):
    total = sum(item["bytes"] for item in files)
    return {
        "id": chunk_id,
        "files": files,
        "file_count": len(files),
        "bytes": total,
        "oversized_single_file": len(files) == 1 and total > MAX_BYTES,
        "status": "pending",
        "attempt": attempt,
        "parent": parent,
        "result": None,
        "error": None,
    }


def session_fingerprint(repo, target, revision, standard, entries):
    payload = {
        "repo": str(repo),
        "target": target,
        "revision": revision,
        "standard": str(standard),
        "files": entries,
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()


def command_init(args):
    repo = Path(args.repo).expanduser().resolve()
    standard = Path(args.standard).expanduser().resolve()
    entries = manifest_entries(args.manifest, repo)
    fingerprint = session_fingerprint(repo, args.target, args.revision, standard, entries)
    root = context_root(repo, args.context_root) / slug(repo.name) / "quality-audit"
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    name = slug(args.session) if args.session else f"{slug(Path(args.target).name)}-{args.revision[:7]}-{timestamp}"
    session = root / name
    state_path = session / "state.json"
    if state_path.exists():
        state = load_json(state_path)
        if state["fingerprint"] != fingerprint:
            raise ValueError(f"session exists with different inputs: {session}")
        print(session)
        return
    chunks = chunk_entries(entries)
    state = {
        "schema_version": 1,
        "status": "auditing",
        "fingerprint": fingerprint,
        "repository": str(repo),
        "target": args.target,
        "revision": args.revision,
        "standard": str(standard),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "manifest_file_count": len(entries),
        "manifest_bytes": sum(item["bytes"] for item in entries),
        "next_chunk_number": len(chunks) + 1,
        "chunks": chunks,
    }
    session.mkdir(parents=True, exist_ok=True)
    (session / "chunks").mkdir(exist_ok=True)
    (session / "results").mkdir(exist_ok=True)
    (session / "retries").mkdir(exist_ok=True)
    atomic_json(session / "manifest.json", {"files": entries})
    for chunk in chunks:
        atomic_json(session / "chunks" / f"{chunk['id']}.json", chunk)
    atomic_json(state_path, state)
    print(session)


def is_active(chunk):
    if chunk["status"] == "pending":
        return True
    return chunk["status"] == "rejected" and chunk["file_count"] == 1 and chunk["attempt"] < MAX_ATTEMPTS


def recompute_status(state):
    active = [chunk for chunk in state["chunks"] if is_active(chunk)]
    failed = [chunk for chunk in state["chunks"] if chunk["status"] == "failed"]
    if failed:
        state["status"] = "blocked"
    elif not active:
        state["status"] = "ready-for-synthesis"
    else:
        state["status"] = "auditing"


def command_next_wave(args):
    session = Path(args.session).expanduser().resolve()
    state = load_json(session / "state.json")
    pending = [chunk for chunk in state["chunks"] if is_active(chunk)][: args.limit]
    print(json.dumps({"session": str(session), "chunks": pending}, indent=2))


def inspected_files(text):
    lines = text.splitlines()
    try:
        start = next(index for index, line in enumerate(lines) if line.strip().lower() == "files inspected:") + 1
    except StopIteration:
        return []
    files = []
    for line in lines[start:]:
        match = re.match(r"^\s*-\s+`?([^`]+?)`?\s*$", line)
        if not match:
            if line.strip():
                break
            continue
        files.append(match.group(1).strip())
    return files


def dimension_summaries(text):
    found = []
    for dimension in DIMENSIONS:
        if re.search(rf"(?mi)^\s*{re.escape(dimension)}:\s*\d+ critical,\s*\d+ major,\s*\d+ minor\.\s*$", text):
            found.append(dimension)
    return found


def split_rejected(state, chunk, is_incomplete):
    files = chunk["files"]
    if len(files) < 2:
        if is_incomplete or chunk["attempt"] + 1 >= MAX_ATTEMPTS:
            chunk["status"] = "failed"
        else:
            chunk["attempt"] += 1
        return
    midpoint = (len(files) + 1) // 2
    children = []
    for subset in (files[:midpoint], files[midpoint:]):
        child_id = f"C{state['next_chunk_number']:04d}"
        state['next_chunk_number'] += 1
        children.append(make_chunk(child_id, subset, chunk["attempt"] + 1, chunk["id"]))
    state["chunks"].extend(children)


def command_record(args):
    session = Path(args.session).expanduser().resolve()
    state_path = session / "state.json"
    state = load_json(state_path)
    chunk = next((item for item in state["chunks"] if item["id"] == args.chunk), None)
    if not chunk:
        raise ValueError(f"unknown chunk: {args.chunk}")
    if chunk["status"] not in ("pending", "rejected"):
        raise ValueError(f"chunk {args.chunk} is already {chunk['status']}")
    text = Path(args.result).read_text(encoding="utf-8")
    expected = [item["path"] for item in chunk["files"]]
    echoed = inspected_files(text)
    summaries = dimension_summaries(text)
    reasons = []
    is_incomplete = bool(re.search(r"(?im)^\s*INCOMPLETE\s*:\s*true\s*$", text))
    if is_incomplete:
        reasons.append("auditor reported INCOMPLETE: true")
    if not re.search(r"(?im)^\s*INCOMPLETE\s*:\s*false\s*$", text):
        reasons.append("missing INCOMPLETE: false completion marker")
    if echoed != expected:
        reasons.append(f"manifest mismatch: expected {expected}, echoed {echoed}")
    missing_dimensions = [dimension for dimension in DIMENSIONS if dimension not in summaries]
    if missing_dimensions:
        reasons.append(f"missing dimension summaries: {missing_dimensions}")
    destination_dir = session / ("results" if not reasons else "retries")
    destination_dir.mkdir(exist_ok=True)
    destination = destination_dir / f"{chunk['id']}-attempt-{chunk['attempt'] + 1}.md"
    destination.write_text(text, encoding="utf-8", newline="\n")
    chunk["result"] = str(destination)
    if reasons:
        chunk["status"] = "rejected"
        chunk["error"] = "; ".join(reasons)
        split_rejected(state, chunk, is_incomplete)
    else:
        chunk["status"] = "accepted"
        chunk["error"] = None
    state["updated_at"] = datetime.now(timezone.utc).isoformat()
    recompute_status(state)
    atomic_json(state_path, state)
    print(json.dumps({"chunk": chunk["id"], "status": chunk["status"], "error": chunk["error"]}, indent=2))


def command_status(args):
    session = Path(args.session).expanduser().resolve()
    state = load_json(session / "state.json")
    counts = {}
    for chunk in state["chunks"]:
        counts[chunk["status"]] = counts.get(chunk["status"], 0) + 1
    accepted_files = sum(chunk["file_count"] for chunk in state["chunks"] if chunk["status"] == "accepted")
    print(json.dumps({
        "session": str(session),
        "status": state["status"],
        "chunks": counts,
        "accepted_files": accepted_files,
        "manifest_files": state["manifest_file_count"],
    }, indent=2))


def resolve_agent_md(repo):
    candidates = [
        repo / ".devin" / "agents" / "quality-auditor" / "AGENT.md",
        repo / ".claude" / "agents" / "quality-auditor.md",
        Path.home() / ".agents" / "agents" / "quality-auditor" / "AGENT.md",
        Path.home() / ".claude" / "agents" / "quality-auditor.md",
    ]
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    fallback = Path(__file__).resolve().parents[3] / "agents" / "quality-auditor" / "AGENT.md"
    if fallback.is_file():
        return fallback
    raise ValueError("could not resolve quality-auditor AGENT.md")


def command_prompt(args):
    session = Path(args.session).expanduser().resolve()
    state = load_json(session / "state.json")
    chunk = next((item for item in state["chunks"] if item["id"] == args.chunk), None)
    if not chunk:
        raise ValueError(f"unknown chunk: {args.chunk}")
    repo = Path(args.repo).expanduser().resolve() if args.repo else Path(state["repository"])
    standard = Path(state["standard"]).expanduser().resolve()
    agent_md = resolve_agent_md(repo)
    agent_text = agent_md.read_text(encoding="utf-8")
    standard_text = standard.read_text(encoding="utf-8") if standard.is_file() else ""
    files = []
    for entry in chunk["files"]:
        source = (repo / entry["path"]).resolve()
        try:
            content = source.read_text(encoding="utf-8", errors="replace")
        except OSError as error:
            raise ValueError(f"cannot read {entry['path']}: {error}") from error
        files.append({"path": entry["path"], "content": content})
    parts = [
        f"# quality-auditor prompt for {chunk['id']}",
        "",
        "You are a quality-auditor worker. The instructions below are self-contained.",
        "Follow the response format exactly. Do not add preamble, headings, or numbering.",
        "",
        agent_text,
        "",
        "## Code-quality standard",
        "",
        standard_text,
        "",
        f"## Chunk {chunk['id']} files to inspect",
        "",
        "Echo the exact repository-relative paths below in the `Files inspected:` block.",
    ]
    for file in files:
        parts.extend([
            "",
            f"### {file['path']}",
            f"--- begin {file['path']} ---",
            file["content"],
            f"--- end {file['path']} ---",
        ])
    parts.extend([
        "",
        "## Final reminder",
        "",
        "Return only the audit result in the exact format above. Start with `Files inspected:`. End with `INCOMPLETE: false` if every file was inspected, or `INCOMPLETE: true` followed by the uninspected file list if not.",
    ])
    prompt_dir = session / "prompts"
    prompt_dir.mkdir(exist_ok=True)
    prompt_path = prompt_dir / f"{chunk['id']}-prompt.md"
    prompt_path.write_text("\n".join(parts), encoding="utf-8", newline="\n")
    print(prompt_path)


def command_reset(args):
    session = Path(args.session).expanduser().resolve()
    state_path = session / "state.json"
    state = load_json(state_path)
    if args.chunk:
        targets = [item for item in state["chunks"] if item["id"] == args.chunk and item["status"] == "failed"]
    else:
        targets = [item for item in state["chunks"] if item["status"] == "failed"]
    if not targets:
        print(json.dumps({"reset": [], "status": state["status"]}, indent=2))
        return
    for chunk in targets:
        chunk["status"] = "pending"
        chunk["attempt"] += 1
        chunk["error"] = None
    recompute_status(state)
    state["updated_at"] = datetime.now(timezone.utc).isoformat()
    atomic_json(state_path, state)
    print(json.dumps({"reset": [chunk["id"] for chunk in targets], "status": state["status"]}, indent=2))


def parser():
    root = argparse.ArgumentParser(description="Persistent quality-audit session state")
    commands = root.add_subparsers(dest="command", required=True)
    init = commands.add_parser("init")
    init.add_argument("--repo", required=True)
    init.add_argument("--target", required=True)
    init.add_argument("--revision", required=True)
    init.add_argument("--standard", required=True)
    init.add_argument("--manifest", required=True)
    init.add_argument("--context-root")
    init.add_argument("--session")
    init.set_defaults(handler=command_init)
    wave = commands.add_parser("next-wave")
    wave.add_argument("--session", required=True)
    wave.add_argument("--limit", type=int, default=8, choices=range(1, 9))
    wave.set_defaults(handler=command_next_wave)
    record = commands.add_parser("record")
    record.add_argument("--session", required=True)
    record.add_argument("--chunk", required=True)
    record.add_argument("--result", required=True)
    record.set_defaults(handler=command_record)
    status = commands.add_parser("status")
    status.add_argument("--session", required=True)
    status.set_defaults(handler=command_status)
    prompt = commands.add_parser("prompt")
    prompt.add_argument("--session", required=True)
    prompt.add_argument("--chunk", required=True)
    prompt.add_argument("--repo")
    prompt.set_defaults(handler=command_prompt)
    reset = commands.add_parser("reset")
    reset.add_argument("--session", required=True)
    reset.add_argument("--chunk")
    reset.set_defaults(handler=command_reset)
    return root


def main():
    args = parser().parse_args()
    try:
        args.handler(args)
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as error:
        raise SystemExit(f"error: {error}") from error


if __name__ == "__main__":
    main()
