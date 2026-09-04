---
name: web-accessibility
description: "Build and review accessible web interfaces against WCAG 2.2 Level AA. Use when creating or changing HTML, JSX, TSX, Vue, Svelte, forms, navigation, dialogs, menus, tables, interactive components, keyboard behaviour, focus management, ARIA, contrast, motion, touch targets, media alternatives, or screen-reader announcements; also use for WCAG audits and pre-launch web checks. Not for: visual-only screenshot critique (use ui-review), browser automation or accessibility-tree capture alone (use browser-control), backend-only work, APIs, CLIs, native apps, or non-UI code."
---

# Web Accessibility

Treat accessibility as an implementation constraint, not a post-build enhancement. Default to WCAG 2.2 Level AA unless the project specifies a stricter or contractually different target.

## 1. Establish context

1. Read project instructions and inspect the framework, rendering model, component library, design system, lint rules, test setup, and existing accessibility utilities.
2. Identify the affected user journeys, input methods, dynamic states, target devices, content languages, and declared compliance obligations.
3. Reuse accessible primitives already supplied by the project or component library. Verify their documented behaviour rather than assuming conformance.
4. Record baseline evidence for the affected states: known barriers, automated findings by severity, keyboard and screen-reader coverage, and checks not yet performed.
5. If legal conformance is requested, confirm the jurisdiction and required standard from a current authoritative source; do not treat this skill as legal advice.

Complete this phase when the applicable standard, affected flows, existing primitives, available verification tools, and baseline evidence are explicit.

## 2. Design through native semantics

1. Choose native HTML elements and document structure before adding ARIA.
2. Give every control an accessible name that agrees with its visible label.
3. Preserve logical heading, reading, focus, and DOM order.
4. Design every pointer interaction with an equivalent keyboard and non-drag path.
5. Define focus entry, containment, restoration, and announcement for each dynamic state.
6. Reserve space and alternatives for errors, status changes, media, motion, and sensory instructions.

Read [WCAG 2.2 AA baseline](references/wcag-22-aa.md) when mapping requirements or reviewing a page. Read [interaction patterns](references/interaction-patterns.md) when the work includes forms, dialogs, menus, tabs, disclosures, drag operations, authentication, or live updates.

Complete this phase when every interaction has semantics, an accessible name, keyboard behaviour, focus behaviour, and a perceivable state design.

## 3. Implement the smallest native solution

1. Preserve project conventions and use the existing accessible component library where it meets the requirement.
2. Prefer `button`, `a`, `input`, `select`, `textarea`, landmarks, headings, lists, and tables over recreating their behaviour.
3. Add ARIA only when native semantics cannot express the required relationship or state; keep ARIA state synchronized with visible state.
4. Keep labels visible, associate help and errors programmatically, and make recovery instructions specific.
5. Support zoom, reflow, text spacing, reduced motion, high contrast, coarse pointers, and keyboard-only use without hiding content or functionality.
6. Do not add an accessibility overlay as a substitute for correcting source markup and interaction behaviour.

Complete this phase when the implementation exposes the same information, relationships, state, and actions through visual, keyboard, and accessibility APIs.

## 4. Verify in layers

Read [testing accessibility](references/testing.md), then use every layer available in the project:

1. Run existing lint, component, integration, axe, pa11y, or equivalent checks.
2. Exercise the complete flow with keyboard only, including reverse navigation, cancellation, validation, and recovery.
3. Inspect the browser accessibility tree and accessible names where browser tooling is available.
4. Check contrast, focus visibility, target size, zoom/reflow, reduced motion, and forced-colour behaviour.
5. Test representative screen-reader flows when the change is consequential or conformance is claimed.
6. Compare the same states and coverage with the baseline, recording resolved, remaining, and newly introduced barriers rather than relying on a single aggregate score.
7. Re-run project quality gates after fixes.
8. For released user journeys, define the post-release feedback or monitoring signal and observation window appropriate to the product, such as accessibility support reports, failed-flow analytics that collect no sensitive data, or scheduled regression scans.

Automated checks cannot prove conformance. Distinguish observed results from assumptions and list manual checks that were not performed.

Complete this phase when all available checks pass, before/after evidence is recorded, post-release detection is defined where applicable, and every unavailable or inconclusive check is disclosed.

## 5. Report

Summarise:

- standard and scope assessed;
- barriers found, with affected users and WCAG criterion where known;
- changes made and comparable before/after evidence;
- remaining manual checks, limitations, follow-up risks, and post-release detection where applicable.

Do not claim WCAG conformance from automated results alone.

Complete this phase when the report lists standard/scope, barriers with criteria, before/after evidence, and remaining checks.
