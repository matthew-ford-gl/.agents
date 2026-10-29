---
name: itsm-security-docs
description: "Drafts and reviews operational and information-security process documents (incident, major incident, cyber incident response, problem, change, escalation, on-call, post-incident review, BCP/DR, runbooks, playbooks, policies, SOPs) against ISO 27001, ISO 27701 and ITIL 4 good practice, in plain, usable prose. Use when asked to write, draft, improve, review, audit, gap-check or sanity-check an incident management process, cyber incident response plan, escalation matrix, severity model, runbook or similar governance document. Not for: architecture decision records (use adr-drafter), code or API docs, prompt or skill files (use writing-for-agents), or formal certification audits and legal advice."
argument-hint: "<draft|review> <doc type> [path or context]"
---

Task: $ARGUMENTS

Two modes: **Draft** (create or rewrite a document) and **Review** (grade an existing one). Infer the mode from the request; ask only if truly ambiguous.

## 1. Establish context

Gather, from the conversation or the user's files first; ask only for what is missing and changes the output:

- Document type and audience (responders, managers, auditors, all staff)
- Org specifics: roles/titles, tooling (ticketing, paging, comms), service tiers, SLAs, regulators and contractual notification duties
- Existing house template or neighbouring documents. If present, follow their structure, numbering and tone over the defaults here.
- Standards in scope. Default: ISO 27001:2022, ISO 27701, ITIL 4. Confirm the ISO 27701 edition (2019 extension vs 2025 standalone) before citing clause numbers.

Complete when document type, audience, and applicable standards/regulatory duties are stated, and unknowns are listed as explicit assumptions or open questions.

## 2. Load the right reference

- Document structure and required content: read `references/doc-types.md` for the matching type.
- Control mapping and regulatory timers: read `references/standards.md` when citing ISO/ITIL clauses, privacy-breach handling, or notification deadlines.
- Review mode: also read `references/review-checklist.md`.

Complete when the relevant reference files have been read.

## 3a. Draft mode

1. Start from the doc-types skeleton; drop sections that do not apply rather than leaving placeholders.
2. Do not invent facts: names, phone numbers, SLAs, tools, thresholds, legal duties. Mark unknowns `[TBC: owner/question]` and list them at the end.
3. Make every process step operable: who (role, not person), does what, by when, using which tool, producing which record. Severity or priority definitions use observable criteria, not adjectives.
4. Include document control (owner, version, review date, approver) and a short purpose/scope that says what is out of scope.
5. Write for the person using it at 3am: imperative verbs, short sentences, numbered steps for sequences, tables for matrices, one idea per paragraph. Define each acronym once. Put the most time-critical content first. Use British English unless the user's documents use another.
6. Map to standards in a compact traceability table at the end, not scattered through the body. Cite only controls you are sure apply.
7. Run the self-check in `references/review-checklist.md` (sections "Structure" and "Operability") on the draft and fix failures before delivering.

Complete when the file is written, no placeholder text remains except `[TBC]` items, and the self-check passes.

## 3b. Review mode

1. Read the whole document; do not skim.
2. Walk `references/review-checklist.md` in order. Record a finding only with evidence: quote or cite the section, state the defect, state the consequence, give a concrete fix.
3. Grade each finding: **Blocker** (process cannot work or breaks a legal/standard requirement), **Major** (ambiguity or gap likely to cause failure under pressure), **Minor** (clarity, style, consistency).
4. Also list what the document does well, briefly, so the author keeps it.
5. Deliver using the format below. Offer to apply fixes; edit the document only when asked.

```text
VERDICT: <Ready | Ready with changes | Not ready>
Scope reviewed: <doc, version, standards checked against>

Findings
| # | Grade | Location | Issue | Consequence | Fix |

Strengths: <2-4 bullets>
Assumptions / could not verify: <items>
Top 3 actions: <ordered>
```

Complete when every checklist section has been walked, each finding has evidence and a fix, and the verdict is consistent with the highest grade found (any Blocker means Not ready).

## Boundaries

- Treat this as good-practice guidance, not certification or legal advice. Flag regulatory timers (for example GDPR, NIS2) as items to confirm with the DPO or legal.
- Do not paste real incident data, credentials or personal data into documents; use roles and placeholders.
- Do not claim ISO or ITIL compliance for a document; say it is aligned with, or maps to, named controls.
