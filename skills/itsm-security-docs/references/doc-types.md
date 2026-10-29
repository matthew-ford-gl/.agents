# Document types: structure and required content

Contents: Common frame · Incident management · Major incident · Cyber incident response · Problem management · Post-incident review · Change enablement · Escalation and on-call · BCP/DR · Runbook/playbook · Policy

## Common frame (every type)

1. Document control: owner (role), approver, version, status, last/next review date, change history
2. Purpose and scope (including exclusions)
3. Definitions (only terms the reader may not know)
4. Roles and responsibilities (RACI table where more than two roles)
5. Process or content (type-specific below)
6. Records produced and where kept; retention
7. Metrics and review cadence
8. Related documents
9. Standards traceability table

## Incident management (ITIL 4 incident management practice)

- Definition of incident vs service request vs problem vs security event
- Detection and logging: sources, mandatory ticket fields, who may raise
- Categorisation and prioritisation: impact x urgency matrix with observable criteria and example scenarios per cell
- Response and resolution targets per priority (respond, update cadence, resolve); clock start/stop rules
- Initial diagnosis, functional escalation, hierarchical escalation triggers
- Communication: who is told what, when, via which channel; status-update cadence
- Workaround vs resolution; resolution and closure criteria; user confirmation
- Linkage to problem, change, major incident and security incident processes
- Handoff rule: when an incident is reclassified as major or security, and who decides

## Major incident

- Declaration criteria (observable) and who may declare; anyone can escalate, named roles declare
- Roles: Incident Commander/Major Incident Manager, Technical Lead, Communications Lead, Scribe, Business/Service Owner liaison
- Bridge/war-room logistics, update cadence (for example every 30 min), decision log
- Stakeholder and customer comms templates (initial, update, resolved)
- Stand-down criteria, handover between shifts, mandatory PIR with deadline

## Cyber incident response (NIST SP 800-61 / ISO 27035 lifecycle, mapped to ISO 27001 A.5.24-A.5.28)

- Definitions: event, incident, personal data breach, with examples
- Phases: prepare, detect and report, triage and assess, contain, eradicate, recover, learn
- Severity model tied to confidentiality/integrity/availability impact, data classification, and regulatory exposure
- Reporting channel for all staff and suppliers (single route, 24x7 path), plus no-blame reporting statement
- Decision rights: who can isolate systems, disable accounts, engage external IR/forensics, contact police/regulators, authorise public statements
- Evidence handling: preservation, chain of custody, log retention, who may image or touch affected systems (A.5.28)
- Containment playbook index by scenario (ransomware, phishing/BEC, credential compromise, data exfiltration, insider, DDoS, supplier breach)
- Privacy breach branch: DPO involvement, risk assessment, notification decision and timers (see standards.md)
- Legal, insurer, regulator, customer and law-enforcement notification matrix with owners and deadlines
- Out-of-band comms plan if email/chat is compromised
- Testing: tabletop and technical exercise cadence, and how results feed back

## Problem management

- Problem identification triggers (repeat incidents, major incident, trend analysis)
- Root cause analysis methods allowed (5 Whys, fishbone, fault tree) and when each fits
- Known error record and workaround publication
- Problem ownership, prioritisation, target dates, and link to change for permanent fix
- Closure criteria and recurrence monitoring

## Post-incident review (blameless)

- Trigger thresholds and deadline (for example within 5 working days of resolution)
- Facilitator independent of the response where possible
- Template: summary, impact (duration, users, data, cost), timeline with sources, detection, response, root and contributing causes, what went well, what did not, corrective and preventive actions
- Actions: owner, due date, tracked in a named system, reviewed until closed
- Distribution and confidentiality rules; feeds ISO 27001 A.5.27 and ITIL continual improvement

## Change enablement

- Change types: standard (pre-approved), normal (risk-assessed, CAB or delegated authority), emergency
- Risk assessment criteria, required evidence (test, rollback, comms), approval authority by risk
- Scheduling, freeze periods, emergency retrospective approval rules
- Post-implementation review and failed-change handling
- Security and privacy impact check (ISO 27001 A.8.32, 27701 where PII is touched)

## Escalation and on-call

- Escalation matrix table: trigger, level, role, time to acknowledge, next level if no response
- Rota rules: handover, cover, fatigue limits, contact details source of truth and refresh cadence
- Fallback when primary and secondary do not respond

## BCP / DR (ITIL 4 service continuity, ISO 27001 A.5.29-A.5.30)

- Business impact analysis summary, RTO/RPO per service, dependencies
- Invocation criteria and authority, recovery sequence, alternate working arrangements
- Backup and restore evidence, test cadence and last-test result, security controls maintained during disruption

## Runbook / playbook

- Title, trigger, preconditions, required access, expected duration
- Numbered steps, each with command or click path, expected result, and what to do if it differs
- Rollback, verification, escalation point, and last-tested date
- No narrative; one task per runbook

## Policy

- Statement of intent, mandatory requirements phrased as testable "must", scope, roles, exceptions process, enforcement, review cycle
- Policies state what and why; procedures and runbooks state how. Do not mix.
