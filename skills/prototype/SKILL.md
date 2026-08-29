---
name: prototype
description: Build a deliberately throwaway prototype to answer a specific product, interaction, UI, state, or technical design question before production implementation. Use when alternatives need direct comparison or uncertainty is cheaper to resolve experimentally.
argument-hint: "<question the prototype must answer>"
model: sonnet
---

# Prototype

Question to answer: $ARGUMENTS

A prototype is an experiment, not an implementation candidate. Optimise for learning speed and comparison while keeping it isolated from production paths.

## 1. Frame the experiment

Establish:

- The single decision the prototype must inform
- Competing hypotheses or variants
- What the human must be able to observe or try
- Success, rejection, and inconclusive criteria
- Constraints that must remain realistic

If the question or decision criteria are unclear, ask before building.

## 2. Choose the smallest medium

Prefer, in order:

1. A self-contained HTML file in the OS temporary directory (`[System.IO.Path]::GetTempPath()` or `$env:TEMP` on Windows; `$TMPDIR` falling back to `/tmp` on macOS/Linux) for interaction, state, layout, or visual comparisons
2. A temporary script or harness for protocol, algorithm, or integration questions
3. An isolated application route only when the real runtime is necessary to answer the question

For UI alternatives, provide meaningfully different variants selectable from one surface. Preserve the same scenario and content across variants so the comparison tests the design rather than different data.

Use existing project dependencies only when prototyping inside the application. Do not add a production dependency for a throwaway experiment without approval.

## 3. Build only the experiment

Use representative but synthetic data. Include enough edge states to expose the decision: loading, empty, error, long content, constrained viewport, or other states relevant to the question.

Do not connect real credentials, customer data, payments, destructive endpoints, or production services. Mark in-repository prototype code clearly through its isolated location and report that it is disposable.

## 4. Make it observable

Run the prototype and provide the human with the local path or browser preview. Explain how to switch variants and which scenarios to try. Capture console errors and correct anything that prevents a fair comparison.

## 5. Record the result

Report:

- Question tested
- Variants or hypotheses
- Observations against the criteria
- Decision supported, rejected, or still inconclusive
- Production constraints deliberately omitted
- Exact temporary or repository paths created
- Recommended next step

Ask before deleting in-repository prototype files. Temporary artifacts may remain for the session and must not be presented as production-ready code.
