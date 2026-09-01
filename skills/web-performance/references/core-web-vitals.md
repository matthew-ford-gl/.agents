# Core Web Vitals

Use current metric definitions from web.dev or Chrome documentation when exact reporting rules matter. The thresholds below are the standard “good” targets, assessed at the 75th percentile of eligible page visits and segmented by mobile and desktop where field data permits.

## Metrics

| Metric | User experience | Good | Needs improvement | Poor |
|---|---|---:|---:|---:|
| Largest Contentful Paint (LCP) | Loading | ≤ 2.5 s | > 2.5 s and ≤ 4 s | > 4 s |
| Cumulative Layout Shift (CLS) | Visual stability | ≤ 0.1 | > 0.1 and ≤ 0.25 | > 0.25 |
| Interaction to Next Paint (INP) | Responsiveness | ≤ 200 ms | > 200 ms and ≤ 500 ms | > 500 ms |

INP replaced First Input Delay as a Core Web Vital in March 2024. Do not use FID as the current responsiveness target.

## LCP diagnosis

Split LCP into time to first byte, resource load delay, resource load duration, and element render delay. Identify the actual LCP element before choosing a remedy.

- High TTFB: inspect redirects, server generation, cache misses, geography, and network setup.
- High resource load delay: make the resource discoverable in initial markup, remove accidental lazy loading, and correct priority competition.
- High resource load duration: reduce bytes, improve compression/format, or improve delivery.
- High element render delay: inspect blocking CSS/fonts, hidden elements, client-only rendering, hydration, and main-thread work.

Preload only resources proven to be critical. Excess preloads compete with CSS, fonts, and the LCP resource.

## CLS diagnosis

- Give images, video, embeds, ads, and dynamic regions stable dimensions or aspect ratios.
- Reserve space for late personalization, consent UI, banners, and asynchronous content.
- Avoid inserting content above existing content unless it responds directly to a user action.
- Inspect font metric changes and use compatible fallbacks or font metric overrides where justified.
- Attribute shifts to their source rather than hiding them with fixed heights that clip content.

## INP diagnosis

INP reflects the longest representative interaction latency across a visit, ignoring statistical outliers according to the metric definition. Diagnose input delay, event-processing time, and presentation delay.

- Remove or defer unrelated long tasks that block input.
- Reduce synchronous handler work and DOM/layout scope.
- Avoid layout thrashing from alternating reads and writes.
- Yield between chunks of noncritical work when supported.
- Virtualise or paginate genuinely large rendered collections without harming keyboard or screen-reader access.
- Give immediate visual acknowledgement while preserving honest completion and error states.

## Supporting diagnostics

TTFB, First Contentful Paint, Total Blocking Time, long tasks, resource timing, CPU profiles, bundle analysis, and server timing help explain the Core Web Vitals but are not substitutes for them. Total Blocking Time is a laboratory proxy, not field INP.
