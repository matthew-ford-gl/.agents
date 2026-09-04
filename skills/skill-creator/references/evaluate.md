# Evaluate: sub-procedures

Loaded from SKILL.md Section 6. Read only the section matching the chosen approach.

## Baseline-first approach

1. Write the `evals.json` or eval plan before improving the skill.
2. Run the task once without the new skill (baseline) and capture specific failures.
3. The baseline failures are the spec for the skill.
4. After drafting, run the same prompts with the skill and compare.
5. Iterate until the with-skill run beats baseline on the gap assertions.

## Lightweight review

For small or subjective skills:

1. Create 2–3 realistic prompts covering the main path and an important edge case.
2. Trace whether the description triggers appropriately.
3. Trace each prompt through the workflow.
4. Review outputs or expected behavior with the user when judgment is subjective.

## Comparative evaluation

For objectively testable or consequential skills:

1. Define representative prompts and expected results before running them.
2. For a new skill, compare runs with the skill against runs without it.
3. For an existing skill, snapshot the old version and compare it against the revision.
4. Launch independent runs in parallel when the host supports subagents.
5. Use objective assertions for machine-checkable properties and human review for subjective quality.
6. Record pass/fail evidence, errors, token or timing data when available, and qualitative feedback.
7. Summarize discriminating improvements, regressions, variance, and cost trade-offs.
