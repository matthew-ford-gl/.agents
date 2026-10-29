# Standards mapping and regulatory timers

Contents: ISO 27001:2022 · ISO 27701 · ITIL 4 · Regulatory timers · Citation rules

## ISO/IEC 27001:2022

Management-system clauses
- 5.2 Policy, 5.3 Roles and authorities
- 7.5 Documented information (control of documents: identification, version, approval, availability, retention)
- 8.1 Operational planning and control
- 9.1 Monitoring and measurement, 9.2 Internal audit, 9.3 Management review
- 10.2 Nonconformity and corrective action

Annex A controls most relevant to these documents
| Control | Topic |
|---|---|
| A.5.5 / A.5.6 | Contact with authorities / special interest groups |
| A.5.24 | Incident management planning and preparation |
| A.5.25 | Assessment and decision on security events |
| A.5.26 | Response to security incidents |
| A.5.27 | Learning from incidents |
| A.5.28 | Collection of evidence |
| A.5.29 | Information security during disruption |
| A.5.30 | ICT readiness for business continuity |
| A.5.31 | Legal, statutory, regulatory and contractual requirements |
| A.5.37 | Documented operating procedures |
| A.6.8 | Information security event reporting |
| A.8.15 / A.8.16 | Logging / Monitoring activities |
| A.8.13 | Information backup |
| A.8.32 | Change management |

## ISO/IEC 27701

- 2019 edition is an extension to 27001/27002 (PIMS). Incident and breach handling for PII sits in the 27002 extension guidance (clause 6.13) and controller/processor controls (Annex A and B).
- 2025 edition is a standalone management-system standard with a different structure. Confirm which edition the organisation certifies to before citing clause numbers; if unknown, cite the topic ("PII breach handling") rather than a number.
- Controller vs processor role changes duties: a processor must notify the controller without undue delay and support its obligations; a controller assesses and notifies.
- Documents touching PII should record: whether PII is affected, the DPO or privacy lead engaged, breach risk assessment, and decision rationale (including a decision not to notify).

## ITIL 4 practices to align with

Incident management; problem management; change enablement; service request management; service desk; monitoring and event management; service level management; service continuity management; information security management; continual improvement.
- Use ITIL 4 vocabulary: "change enablement" not "change management" for the ITIL practice; "known error"; "workaround"; "service owner".
- Guiding principles worth reflecting: focus on value, start where you are, progress iteratively, collaborate, keep it simple and practical, optimise and automate.
- Priority = impact x urgency; SLAs/targets are agreed in service level management, not invented in the incident document.

## Regulatory timers (confirm applicability and current wording with legal or the DPO)

| Regime | Trigger | Deadline |
|---|---|---|
| UK/EU GDPR Art. 33 | Personal data breach likely to result in risk to individuals | Notify supervisory authority (ICO in UK) without undue delay and where feasible within 72 hours of becoming aware |
| UK/EU GDPR Art. 33(2) | Processor becomes aware of breach | Notify controller without undue delay |
| UK/EU GDPR Art. 34 | High risk to individuals | Inform affected individuals without undue delay |
| UK/EU GDPR Art. 33(5) | Any breach | Record it, including facts, effects, remedial action, even if not notified |
| NIS2 (where in scope) | Significant incident | Early warning within 24h, incident notification within 72h, final report within one month |
| Contracts and insurers | Per contract/policy | Often 24-72h; check each. Missing it can void cover |

Write timers as "from awareness" with a named owner for the decision and a record of when awareness occurred.

## Citation rules

- Cite a control only when the document content actually implements it.
- Use a traceability table: Control | Where addressed (section) | Notes/gaps.
- Say "aligned with" or "maps to"; never "compliant with" or "certified".
- If unsure of a clause number, cite the topic and mark `[verify clause]`.
