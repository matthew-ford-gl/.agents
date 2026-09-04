# Asset and code delivery

Apply only sections connected to the measured bottleneck.

## Images

- Serve correctly sized responsive images with intrinsic dimensions and suitable modern formats supported by the project pipeline.
- Keep the LCP image discoverable in initial markup and avoid lazy loading it.
- Lazy-load below-the-fold images and decode them without blocking where supported.
- Use priority hints or preload only for a confirmed critical image; verify that the hint improves request order.
- Preserve meaningful alternatives and do not replace accessible content with CSS backgrounds solely for speed.

## Fonts

- Remove unused families, weights, styles, and character ranges.
- Prefer self-hosting or an approved origin where privacy, reliability, and caching benefit.
- Preload only fonts required for initial rendering and ensure preload attributes match the eventual request.
- Choose `font-display` and fallback metrics based on measured LCP/CLS and product tolerance; verify text remains readable throughout.
- Avoid CSS `@import` for critical fonts because it delays discovery.

## JavaScript and hydration

- Measure parse, compile, execution, and long-task cost rather than bundle bytes alone.
- Remove unused code and unnecessary third-party scripts before adding splitting complexity.
- Split by user journey and defer code that is not needed for initial rendering or interaction.
- Keep server-rendered critical content in initial HTML where the framework supports it.
- Avoid broad client-component boundaries that force static descendants to hydrate.
- Confirm listener, timer, observer, and worker cleanup in long-lived interfaces.

## CSS

- Remove unused rules through the project's existing build pipeline.
- Keep critical styles discoverable using external optimized delivery or nonce/hash-based inline styles where the project's security model permits.
- CSP is a hard safety boundary — see [SKILL.md](../SKILL.md) step 3.6. Do not loosen it to solve a CSS delivery problem.
- Verify asynchronous stylesheet techniques against no-script behavior, content flashes, and browser support.

## Caching and delivery

- Fingerprint immutable assets and give them long-lived immutable cache headers.
- Keep HTML and mutable API responses on policies that match their freshness and personalization requirements.
- Include all representation-changing request headers in cache keys and `Vary` behavior.
- Test invalidation, rollback, and stale-content behavior before extending TTLs.
- Compress text assets and avoid recompressing already compressed media.
- Verify redirect chains, protocol negotiation, connection reuse, CDN geography, and origin shielding only when evidence points there.

## Third-party code

- Inventory transfer, execution, network, privacy, and failure cost by provider.
- Remove scripts without demonstrated value; load remaining scripts after the critical path when product behavior permits.
- Prefer locally installed, lockfile-pinned tooling over CDN snippets. Do not add a remote script to production merely to run an audit.
- If an approved runtime CDN script is unavoidable, pin an explicit version, apply Subresource Integrity where compatible, constrain CSP and permissions, and define failure behavior.
- Test consent and tag-manager paths because nominally deferred scripts can still create long tasks and layout shifts.
