# Testing accessibility

Use existing project tools first. Do not introduce or globally install audit packages merely because they appear here.

## Automated checks

- Run the repository's accessibility lint rules and existing axe, pa11y, Lighthouse, component, or end-to-end checks.
- Scope automated scans to every changed state, not only the initial route: opened dialogs, validation errors, expanded menus, loading, empty, success, and failure states.
- Treat zero automated violations as the start of manual testing, not proof of conformance.

If no audit tool exists, use available browser semantics inspection and manual checks. Propose a new dependency separately, with user approval and normal supply-chain review.

## Keyboard checks

1. Reload and operate the complete flow without a pointer.
2. Verify Tab and Shift+Tab order, visible focus, Enter and Space activation, component-specific arrow keys, Escape cancellation, and no keyboard trap.
3. Open and close overlays, then verify initial and restored focus.
4. Trigger every error and asynchronous state and confirm recovery remains operable.

## Visual and responsive checks

- Test text zoom to 200% and reflow at 400% without two-dimensional scrolling for ordinary content.
- Apply text-spacing overrides and confirm content and controls remain available.
- Check normal text, large text, focus indicators, controls, and meaningful graphics against their required contrast.
- Test narrow and wide viewports, coarse pointers, reduced motion, and forced colours where supported.

## Accessibility API and screen-reader checks

- Inspect role, accessible name, description, state, value, hierarchy, and relationships in the accessibility tree.
- Test representative flows with a screen reader when the change affects navigation, forms, authentication, commerce, dialogs, custom widgets, or claimed conformance.
- Verify announcements from live regions and ensure focus movement does not duplicate or omit critical information.

## Security and privacy

- Prefer local, pinned project tooling. Do not inject third-party CDN audit scripts into production pages; if a temporary third-party script is explicitly approved, pin its version and integrity metadata and remove it afterward.
- Never submit internal, staging, authenticated, or non-public URLs—or URLs containing tokens, personal data, or confidential query parameters—to public audit services.
- Use synthetic accounts and data for test flows. Do not put credentials, session values, API keys, or personal data in scenarios, screenshots, reports, or fixtures.

## Evidence

Record the route and state, viewport/input mode, tool and version, checks performed, violations, fixes, and checks not performed. Keep automated, keyboard, visual, and screen-reader evidence distinct.
