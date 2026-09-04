---
name: web-performance
description: "Measure and improve browser loading and interaction performance for websites and web apps. Use when triaging Core Web Vitals, Lighthouse or PageSpeed findings, slow pages, LCP, CLS, INP, TTFB, long main-thread tasks, bundle size, images, fonts, CSS, caching, CDN delivery, hydration, or third-party script impact, including pre-launch web performance checks. Not for: visual-only UI review (use ui-review), browser automation or trace capture alone (use browser-control), backend query or API latency tuning, database optimisation, native apps, algorithmic micro-optimisation, or CI build speed."
---

# Web Performance

Measure before changing code. Optimise the demonstrated bottleneck, then repeat the same measurement under comparable conditions.

## 1. Establish scope and evidence

1. Read project instructions and inspect the framework, rendering model, deployment target, CDN/cache configuration, asset pipeline, browser targets, monitoring, and existing performance tooling.
2. Identify priority routes, user journeys, representative devices and networks, and whether field data or laboratory data is failing.
3. Prefer field data for prioritisation and laboratory tests for diagnosis; see [measurement](references/measurement.md) for when each applies and how to record them.
4. Record the baseline conditions and results, including LCP, CLS, INP where available, TTFB, the LCP element, transfer sizes, long tasks, and relevant diagnostic audits.

Read [Core Web Vitals](references/core-web-vitals.md) when interpreting LCP, CLS, INP, or TTFB. Read [measurement](references/measurement.md) before collecting or comparing evidence.

Complete this phase when target routes, test conditions, baseline metrics, and the most likely bottleneck are explicit.

## 2. Rank the critical path

Trace the user-visible delay through:

1. navigation, redirects, DNS, connection, and server response;
2. discovery, priority, transfer, and decoding of the LCP resource;
3. render-blocking CSS, fonts, client rendering, and hydration;
4. layout shifts from unsized or late content;
5. long main-thread work and interaction handlers;
6. third-party scripts and resource contention.

Do not optimise an image when text, TTFB, CSS, or client rendering is the measured LCP constraint. Do not trade accessibility, security, correctness, or maintainability for a laboratory score.

Complete this phase when each proposed change names the measured symptom, causal mechanism, expected metric, and possible regression.

## 3. Apply the smallest evidence-backed change

Read [asset delivery](references/asset-delivery.md) when the bottleneck involves images, fonts, JavaScript, CSS, caching, or third parties.

1. Fix request and rendering order before adding speculative preloads or caches.
2. Reserve dimensions and stable placeholders before dynamic content arrives.
3. Reduce, defer, split, or remove work from the critical path before micro-optimising it.
4. Keep interaction handlers short; yield or move substantial work where the platform and project support it.
5. Use framework-native production features only after checking the installed version and project conventions.
6. Safety boundary: preserve CSP and other security controls. Never loosen `script-src`, `style-src`, or any other directive — including via blanket `unsafe-inline`, `unsafe-eval`, wildcard sources, or disabling CSP — to obtain a performance improvement.
7. Treat new tools, services, packages, and CDN scripts as separate dependency or security decisions requiring normal approval.

Complete this phase when the implementation is limited to the diagnosed constraint and has a defined rollback.

## 4. Verify under comparable conditions

1. Run project quality gates and relevant functional tests.
2. Repeat the same laboratory scenario, device, network, cache state, route, and build mode used for the baseline.
3. Compare distributions or multiple runs rather than selecting one favourable score.
4. Confirm the target metric improved and check for regressions in the other Core Web Vitals, accessibility, behavior, security, resource use, and cache correctness.
5. Where field monitoring exists, define the post-release signal and observation window; do not present laboratory change as proven field improvement.
6. Restore or remove temporary instrumentation and audit tooling.

Complete this phase when before/after evidence is comparable, regressions are checked, and uncertain field impact is labelled.

## 5. Report

Summarise:

- target routes, users, and measurement conditions;
- baseline and resulting metrics, with field and laboratory data separated;
- diagnosed bottleneck and why the change addresses it;
- changes, trade-offs, rollback, and validation results;
- unavailable evidence, remaining risks, and post-release monitoring.

Do not claim an improvement without comparable evidence.
