# Review checklist

Contents: Structure · Operability · Roles and decisions · Severity and escalation · Communication · Security and privacy · Evidence and learning · Standards alignment · Writing quality · Consistency

Walk in order. A failed item becomes a finding only with evidence from the document.

## Structure
- Document control complete: owner, approver, version, date, next review not overdue
- Purpose, scope and exclusions stated
- Required sections for the doc type present (see doc-types.md)
- Related documents named and the references resolve

## Operability
- Every step names a role, an action, a time bound, a tool and a record
- Someone unfamiliar could execute it under stress without asking the author
- Triggers to start the process are observable, not judgement words ("serious", "significant") without criteria
- Entry, exit and handoff points to other processes defined
- No steps depend on a person rather than a role, or on a contact list that has no owner

## Roles and decisions
- Single accountable owner per activity; RACI consistent with the text
- Decision rights explicit for high-impact actions (isolate systems, declare major incident, notify regulator, public statement)
- Deputies or cover defined; out-of-hours path exists

## Severity and escalation
- Severity/priority criteria are measurable and have examples
- Response, update and resolution targets per level; clock rules defined
- Escalation has time-based triggers and a fallback when contacts do not respond
- Reclassification up and down is possible and owned

## Communication
- Audiences, channels, owners, cadence and templates defined
- Out-of-band channel for when primary tools are down or compromised
- Customer/regulator/legal/insurer communications routed through named owners

## Security and privacy
- Personal data breach branch present, with DPO involvement and timers from awareness
- Evidence preservation and chain of custody covered before containment actions that destroy evidence
- Access needed by responders is pre-arranged (break-glass), logged and reviewed
- Document itself avoids secrets and personal data, and has an appropriate classification marking

## Evidence and learning
- Records produced are listed, with location and retention
- Blameless post-incident review with deadline, owner, tracked actions
- Metrics defined (for example MTTA, MTTR, reopen rate, % PIRs on time) and reviewed
- Testing cadence defined (tabletop, restore, failover) with results fed back into the document

## Standards alignment
- Mapped controls actually implemented by the content; gaps stated
- Edition of each standard stated; clause numbers correct for that edition
- Wording avoids claiming compliance or certification
- ITIL terms used correctly

## Writing quality
- Short sentences, imperative voice, one idea per paragraph, acronyms defined once
- Time-critical content first; reference and background later
- Tables used for matrices, numbered lists for sequences, no wall-of-text
- No filler, hedging, or unexplained jargon; no contradictory "should" vs "must"
- Headings are descriptive and scannable

## Consistency
- Terms, role names, priority labels and timings identical throughout
- Numbers in text match tables and diagrams
- Dates, versions and owners agree between control block and body
