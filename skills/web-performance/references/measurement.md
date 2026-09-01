# Measuring web performance

Choose the least invasive existing tool that can answer the question. Inspect project manifests, lockfiles, scripts, CI, and browser tooling before suggesting installation.

## Field and laboratory evidence

- Field data reflects real devices, networks, caches, sessions, geography, and user behavior. Use it to prioritise impact and validate release outcomes.
- Laboratory data is controlled and diagnostic. Use it to reproduce a route and isolate a cause.
- Separate the two in reports. A Lighthouse improvement does not prove a Core Web Vitals field improvement.
- Record percentile, sample size, time range, device class, route grouping, and release boundary for field evidence.

## Reproducible laboratory runs

Record:

- exact URL or local route and application commit/build;
- device/viewport, CPU and network throttling;
- browser/tool version and relevant configuration;
- cold or warm cache, authenticated state, seed data, and consent state;
- number of runs and summary statistic.

Use a production build. Run enough repetitions to identify variance and compare like with like. Preserve traces or reports only when they contain no secrets or personal data.

## Diagnostic sequence

1. Confirm the regression or poor metric under recorded conditions.
2. Identify the affected metric and its phase or subpart.
3. Inspect request waterfalls, main-thread tasks, layout shifts, and the rendered LCP element.
4. Form one causal hypothesis and predict the metric it should change.
5. Apply the smallest change and repeat the same run.
6. Reject changes that improve one selected score while moving cost elsewhere or breaking user behavior.

## Tool boundaries

Use project-provided Lighthouse, Lighthouse CI, WebPageTest, browser performance traces, framework analyzers, resource timing, RUM, or CrUX integrations where available. If none is installed, browser developer tools can establish an initial local diagnosis. Propose new tooling separately rather than installing it globally or adding an unreviewed dependency.

Do not send internal, staging, authenticated, or non-public URLs—or URLs containing credentials, tokens, personal data, or confidential query parameters—to PageSpeed Insights, WebPageTest, or another public audit service. Use local tooling and synthetic data instead.

Keep CSP strict. Performance diagnostics must not require blanket `unsafe-inline`, `unsafe-eval`, wildcard sources, disabled certificate checks, exposed debug endpoints, or embedded API keys. Use environment-variable placeholders for approved service credentials.

## Before-and-after report

For each target metric, report baseline runs, changed runs, central result and variance, test conditions, and whether the data is lab or field. Include regressions checked, uncertainty, rollback condition, and the field signal that should confirm impact after release.
