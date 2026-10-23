---
name: dotnet
description: "Choose correct dotnet CLI invocations for solution discovery, locked-mode restore, build, format-check, full and filtered test runs, vulnerability audits, and package management. Use when working in a .NET repo and needing to build, test, format-check, restore, audit, add or list packages, or run a project — especially when the correct flag sequence would otherwise be rediscovered each time. Not for: .NET Framework-era msbuild/xbuild commands, project-specific business logic, or CI pipeline authoring."
model: sonnet  # canonical command selection from a fixed table; no judgement beyond matching intent to a command
---

# dotnet CLI playbook

Prefer the repo's own documented commands first — check `AGENTS.md`, `CLAUDE.md`, `CONTRIBUTING.md`, and CI YAML before this playbook. This file exists so the correct flag sequences are chosen the first time, not rediscovered.

## 1. Locate the solution

Prefer `*.slnx`, then `*.sln`, then operate on the specific `*.csproj`. Run from the directory containing it rather than `cd`-hopping — or pass the path explicitly. Check `global.json` for the required SDK (`dotnet --list-sdks` to confirm it's installed).

## 2. Standard verify pipeline

Run in this order; each step gates the next:

```sh
dotnet restore <sln> --locked-mode
dotnet build <sln> --no-restore --nologo
dotnet format <sln> --verify-no-changes --no-restore
dotnet test <sln> --no-restore --nologo
# plus the vulnerability audit from §4
```

- `--locked-mode` fails if `packages.lock.json` is out of date — correct for verification. If lock files need regenerating, use `dotnet restore --force-evaluate` deliberately, not silently.
- `--no-restore` after the first restore avoids redundant network work on every later step.
- Omit the format step when the repo has no `.editorconfig` or doesn't enforce `dotnet format` in CI.

Complete when every step exits 0; route failures to §6 instead of retrying variants.

## 3. Targeted test runs

Always narrow before running the whole suite:

```sh
dotnet test <test-project> --no-restore --nologo \
  --filter "FullyQualifiedName~Namespace.Class.Method"
```

- Filter on `FullyQualifiedName~<substring>` — matches partial names, most robust.
- Combine with `|`: `FullyQualifiedName~FooTests|FullyQualifiedName~BarTests`.
- `Name~` filters display names (theories/methods); `TestCategory=`, `Priority=` work when the suite uses traits.
- Run one project (`test/Foo.Tests`) rather than the solution to skip unrelated projects.

## 4. Packages and vulnerabilities

```sh
dotnet list <sln> package --vulnerable --include-transitive --no-restore
dotnet list <sln> package --outdated --no-restore
dotnet add <csproj> package <Name> --version <x.y.z>
dotnet remove <csproj> package <Name>
```

- Pin explicit versions; never float (`*`, `>=`). Prefer versions published >7 days ago.
- After `add`/`remove`, rerun `dotnet restore --locked-mode` expectation: lock files change, so update them with `dotnet restore --force-evaluate` and review the diff.

## 5. Run, watch, and stuck processes

```sh
dotnet watch test --project <test-project>
```

- Kill stragglers before re-running a web project. Windows: `Get-NetTCPConnection -LocalPort <port>` → `Stop-Process -Id <pid>`, or `taskkill /PID <pid> /F`. POSIX: `lsof -i :<port>` → `kill <pid>`.

## 6. Failure triage

- Restore fails on `--locked-mode` → lock file drift; regenerate deliberately and review, don't silently bypass.
- `format --verify-no-changes` fails → run `dotnet format <sln>` and inspect the diff before staging.
- Test filter matches nothing → check the exact namespace/class via `dotnet test --list-tests`.
- Vulnerability audit flags transitive packages → usually fixed by bumping the direct package that pulls them, or an explicit top-level pin.
