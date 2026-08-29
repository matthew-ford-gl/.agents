---
name: tdd
description: Test-driven development through public seams using one red-green-refactor vertical slice at a time. Use when implementing a feature or bug fix test-first, when the user mentions TDD or red-green-refactor, or when an approved test strategy must be executed.
argument-hint: "<feature or fix slice>"
model: sonnet
---

# Test-Driven Development

Task: $ARGUMENTS

Read the repository root and affected-path `AGENTS.md` files, `.claude/CLAUDE.md` when present,
and task-relevant entries from `.context/index.md`. Treat their branch, test, and validation
rules as mandatory. Use the project's domain vocabulary from its loaded context, glossary,
tests, and ADRs.

## 1. Establish the test seam

Identify the public interface through which behaviour is exercised and observed. Reuse established test seams and conventions where they exist. If the proposed seam is new, architecturally significant, or one of several materially different choices, confirm it with the human before writing tests.

Tests specify externally observable behaviour. Avoid private methods, internal collaborator assertions, and side-channel verification unless that side channel is itself the public contract.

## 2. Select one vertical slice

Choose the smallest acceptance-criterion slice that crosses the real implementation path. State:

- Behaviour being added or corrected
- Public seam under test
- Independent expected result
- Why the test will fail before implementation

Expected values must come from the specification, a worked example, or another independent source—not by repeating the production algorithm in the test.

## 3. Red

Write one test for the slice and run the narrowest relevant command. Confirm it fails for the expected behavioural reason.

A compile error caused solely by a deliberately missing public interface may count as red. Test setup failures, unrelated failures, and assertions that pass before the change do not.

If the test does not produce a trustworthy red signal, correct the test or seam before implementing.

## 4. Green

Implement only the behaviour required to make the current test pass. Run the narrow test until green, then run the nearest affected suite to detect collateral failures.

Do not anticipate later slices or build speculative extension points.

## 5. Refactor

With the tests green, remove duplication and improve names or structure without changing behaviour. Keep the public seam stable unless the completed slice proves it is wrong. Re-run the narrow and affected suites after refactoring.

## 6. Repeat and complete

Repeat one slice at a time in acceptance-criterion and risk order. The TDD task is complete when:

- Every agreed acceptance criterion is exercised at an agreed public seam
- Every retained test was observed red for the intended reason before its implementation
- Narrow and affected suites are green
- Tests remain insensitive to internal refactoring
- Unimplemented, deferred, or untestable behaviour is reported explicitly

## Test smells

Reject or revise tests that are:

- **Implementation-coupled** — they mock or assert internal structure rather than behaviour
- **Tautological** — expected output is computed with the same logic as production
- **Insensitive** — the test passes before the behaviour exists or after the relevant production path is broken
- **Over-broad** — one failure could represent several unrelated behaviours
- **Horizontally staged** — a batch of speculative tests is written before any slice reaches green
