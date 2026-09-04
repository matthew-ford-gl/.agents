# Accessible interaction patterns

Load the sections that match the component being changed. Prefer a proven project or platform primitive over reproducing these behaviours manually.

## Forms and validation

- Associate every control with a persistent visible label; placeholder text is supplementary.
- Use the correct input type and `autocomplete` token for identifiable personal-data purposes.
- Group related choices with `fieldset` and `legend` or an equivalent programmatic group name.
- Express required state in text and programmatically without relying on colour or an asterisk alone.
- Link help and errors with `aria-describedby`; apply `aria-invalid` only while invalid.
- On submission failure, provide an error summary and move focus only when that helps users find the failure. Preserve entered values.

## Dialogs

- Use the native `dialog` element where project support permits, or implement the complete dialog pattern.
- Give the dialog a programmatic name, move focus to a sensible element on open, keep Tab navigation within a modal, support Escape unless closing would be destructive, and return focus to the trigger on close.
- Prevent background content from remaining operable or exposed as part of the active modal context.

## Menus, tabs, and disclosures

- Use ordinary links for site navigation unless application-menu behaviour is genuinely required.
- For custom menus, implement the relevant arrow-key, Home, End, Escape, and type-ahead behaviour and manage focus consistently.
- For tabs, connect each tab to its panel, expose selected state, and choose automatic activation only when panel display has no noticeable delay.
- For disclosures, use a button with synchronized `aria-expanded` and `aria-controls`.

## Dynamic content

- Keep routine status changes in a stable polite live region created before the update.
- Reserve assertive announcements for urgent interruptions.
- Move focus for a true context change that requires immediate action; do not move it merely because content refreshed.
- Announce loading, completion, empty states, validation failures, and asynchronous errors without duplicating messages.

## Drag and pointer interaction

- Add buttons, menus, or direct selection as a single-pointer and keyboard alternative to drag-and-drop.
- Make cancellation and reversal possible before committing consequential reorder or movement.
- Meet the target-size minimum in [WCAG 2.2 AA baseline](wcag-22-aa.md) (2.5.8); prefer 44 by 44 for touch comfort.
- Ensure hover or focus content can be dismissed, hovered, and kept visible until the user dismisses it or removes its trigger condition.

## Authentication

- Allow paste and password-manager operation in credential fields.
- Avoid memory, transcription, puzzle, or object-recognition tests as the only authentication path.
- If CAPTCHA is necessary, provide an accessible alternative and verify the complete flow, including errors and expiry.

## Motion and animation

- Respect `prefers-reduced-motion` and remove nonessential movement rather than merely shortening it.
- Provide controls for autoplaying or persistent animation and avoid unexpected audio.
- Do not make orientation, shaking, tilting, or another device motion the only way to act.
