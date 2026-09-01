# WCAG 2.2 Level AA baseline

Use this reference to map requirements and findings. Consult the current W3C WCAG 2.2 recommendation for normative wording; this is an implementation checklist, not a substitute for the standard.

## Perceivable

- Give informative images equivalent text and decorative images an empty text alternative.
- Provide captions for prerecorded synchronized media and the required alternatives for audio or video.
- Encode structure and relationships programmatically: landmarks, headings, lists, labels, table headers, instructions, and reading order.
- Do not rely on colour, shape, position, sound, or another single sensory characteristic alone.
- Meet at least 4.5:1 contrast for normal text, 3:1 for large text, and 3:1 for meaningful UI components and graphics.
- Support 200% text zoom, 400% reflow at an equivalent 320 CSS-pixel width, text-spacing overrides, and content on hover or focus that is dismissible, hoverable, and persistent.

## Operable

- Make all functionality keyboard operable without traps and provide a way to bypass repeated blocks.
- Keep focus order meaningful, ensure focused controls are not entirely obscured (2.4.11), and keep focus indicators visible. As a Level AAA best practice, use an indicator at least equivalent to a 2 CSS-pixel perimeter with at least 3:1 contrast between focused and unfocused states (2.4.13).
- Give pages descriptive titles, links clear purpose, headings and labels descriptive wording, and multiple ways to locate pages where required.
- Avoid flashes, uncontrolled time limits, and motion-only operation; provide pause, stop, extend, or alternatives where applicable.
- Provide single-pointer alternatives to dragging movements (2.5.7).
- Make pointer targets at least 24 by 24 CSS pixels or satisfy the spacing/equivalent-control exceptions (2.5.8). Prefer 44 by 44 for comfortable touch use.
- Ensure the accessible name contains the visible label text (2.5.3) and do not make multipoint gestures, path gestures, or device motion the only control method.

## Understandable

- Declare page language and language changes.
- Keep navigation, identification, and help mechanisms consistent. Repeated help must remain in the same relative order (3.2.6).
- Label inputs, identify errors in text, offer correction suggestions when known, and prevent or confirm consequential submissions.
- Do not require users to re-enter previously supplied information in the same process unless an exception applies (3.3.7).
- Do not make a cognitive function test the sole authentication path; support mechanisms such as password managers and paste, or provide an alternative (3.3.8).

## Robust

- Use valid native roles, names, states, and values; keep custom-control state synchronized.
- Make status messages available to assistive technology without moving focus when the message does not require focus.
- Keep referenced IDs unique and ensure `aria-labelledby`, `aria-describedby`, `aria-controls`, and similar relationships resolve.

## WCAG 2.2 additions to check explicitly

Confirm that reviews do not merely relabel a WCAG 2.1 checklist. WCAG 2.2 Level A/AA adds focus not obscured (minimum), dragging movements, target size (minimum), consistent help, redundant entry, and accessible authentication (minimum). Focus appearance and focus not obscured (enhanced) are Level AAA, not AA; use them as best practice only when the target requires them.
