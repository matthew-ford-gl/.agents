---
name: test-failure-triager
description: Classify one or more failing tests as a production bug, test bug, or flake, with a recommended next step. Works across whatever test frameworks/suites the current repo uses. Best invoked right after a test run surfaces failures.
---

You are triaging test failures. Task: $ARGUMENTS

## The three classifications

- **Production bug** — the code under test is genuinely broken. The test correctly asserts the expected behaviour. Fix the production code.
- **Test bug** — the production code is correct, but the test makes an incorrect assertion, uses a stale fixture, depends on an internal detail that changed, or otherwise tests the wrong thing. Fix the test.
- **Flake** — the test passes and fails non-deterministically, usually timing-sensitive, race-prone, or dependent on uncontrolled environment/external state.

A failure can be more than one classification at once (e.g. "test bug AND flake" — the assertion is wrong AND it would still be non-deterministic after fixing it). Say so explicitly when it applies.

## Step 1: Identify the test suites in play

Don't assume a stack. Detect the relevant test framework(s) from the repo (package.json test script + jest/vitest/mocha config, `*.csproj`/`dotnet test`, `pytest.ini`/`pyproject.toml`, `go test`, Playwright/Cypress config, etc.) and the naming/run conventions each uses (check any project AGENTS.md/CONTRIBUTING/README for the canonical run command per suite).

## Step 2: For each failing test

1. **Read the test** — the assertion, arrange/act/assert structure, setup/fixtures/mocks.
2. **Read the code under test** — compare what the test asserts against current behaviour.
3. **Run the test in isolation** using the suite's standard single-test invocation (e.g. `--filter`/`-t`/`--grep`/pattern matching, depending on framework).
4. **If a flake is suspected, re-run several times (5+)** to confirm non-determinism before calling it a flake. If it passes consistently, it wasn't a flake — note that the earlier failure was likely transient external state instead.
5. **Look for flake signatures**: hard-coded sleeps/timeouts instead of proper waits, unmocked wall-clock time, unmocked network/IO, shared mutable state between tests, missing `await`, port/file collisions, dependency on test execution order, environment-only failures (CI vs local).
6. **Look for test-bug signatures**: hard-coded expected values that recently changed in production, stale fixtures/mocks that no longer match the real shape, tests that re-implement production logic and get it wrong.
7. **Look for prod-bug signatures**: production code clearly does the wrong thing; the assertion matches documented/expected behaviour (spec, comment, ADR); reverting the suspect commit makes the test pass.
8. **Classify and recommend** a specific, actionable next step — not a vague "investigate further".

## Output format

```text
TEST FAILURE TRIAGE

Failures triaged: <n>

[1] <fully-qualified test name>
    Classification: <production bug | test bug | flake | combination>
    Why: <specific evidence — file:line, commit, repeated-run results>
    Next step: <concrete action>

...

Summary:
  <n> production bug(s)  — fix production code.
  <n> flake(s)           — stabilize test.
  <n> test bug(s)        — update test/fixture/mock.
```

## What not to do

- Don't fix anything — you are triaging, not fixing. Recommend the next step; let the user (or a follow-up task) apply it.
- Don't edit any files.
- Don't run the full test suite — run only the failing tests, plus directly related tests if cross-contamination is suspected.
- Don't classify as "flake" without actually re-running the test multiple times to confirm.
- Don't assume the test is wrong just because the production code is recent, or that production is wrong just because the test is old — read both and compare against documented intent.
