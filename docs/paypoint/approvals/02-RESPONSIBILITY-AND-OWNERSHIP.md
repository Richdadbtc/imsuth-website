# Gate 1.2 — Responsibility and Ownership Assignment

**Status:** PENDING  
**Decision requested:** Assign named accountable owners and accepted responsibilities before Phase B begins.

## Assignment matrix

RACI legend: **A** accountable, **R** responsible, **C** consulted, **I** informed. Each activity must have exactly one IMSUTH **A**.

| Activity | Executive Sponsor | System/Product Owner | Finance Owner | Privacy/DPO Owner | Security Owner | System Administrator/Operations | Technical Delivery Lead | Internal Audit |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Approve scope and funding | A | R | C | C | C | I | C | I |
| Approve business requirements | I | A/R | C | C | C | I | C | I |
| Approve tariffs/financial policy | I | C | A/R | I | C | I | C | C |
| Approve role conflicts and maker-checker rules | I | C | A | C | C | I | R | C |
| Privacy basis, minimization and retention | I | C | C | A/R | C | I | C | I |
| Security risk acceptance and incidents | I | C | C | C | A | R | R | I |
| User provisioning operations | I | A | C | C | C | R | C | I |
| Infrastructure operation, backup and restore | I | A | I | C | C | R | C | I |
| Software design, build and test | I | A | C | C | C | C | R | I |
| Production release authorization | A | R | C | C | C | R | C | I |
| Reconciliation control and close-of-day | I | C | A/R | I | C | I | C | C |
| Independent audit access/review | I | I | C | C | C | I | I | A/R |

The proposed RACI itself requires approval. It must be revised if IMSUTH governance assigns these duties differently.

## Named-owner register

| Function | Required decision | Accountable approver | Required evidence | Acceptance criteria | Named owner / deputy | Status |
|---|---|---|---|---|---|---|
| Executive sponsorship | Appoint the authority that owns programme scope, funding and final risk decisions. | CMD/authorized governing authority | Appointment memo or approved management minutes | Name, title, authority limit and escalation route recorded. |  | PENDING |
| System/Product ownership | Appoint the business owner for requirements, acceptance and service outcomes. | Executive Sponsor | Appointment memo/decision record and assignee acceptance | One accountable owner; deputy and availability recorded. |  | PENDING |
| Finance control | Appoint the owner for tariffs, payment policy, reconciliation and financial approvals. | Executive Sponsor/CMD | Appointment memo plus assignee acceptance | Authority covers required decisions; conflicts are disclosed. |  | PENDING |
| Privacy/Data Protection | Appoint the DPO/privacy owner for legal basis, minimization, retention and data-subject processes. | Executive Sponsor/CMD | Formal DPO/privacy designation and acceptance | Independence/access to management documented; escalation defined. |  | PENDING |
| Security | Appoint the owner for security risk, incident response and control acceptance. | Executive Sponsor/CMD | Appointment memo and incident escalation charter | Authority, response contacts and deputy documented. |  | PENDING |
| System Administration/Operations | Appoint operational owner for identity provisioning, infrastructure, backups, monitoring and support. | System Owner with Executive Sponsor confirmation | Operations assignment and runbook ownership record | Duties and on-call/escalation coverage documented; no financial approval authority is implied. |  | PENDING |
| Technical delivery | Appoint technical lead for architecture implementation, quality and secure delivery. | System Owner/contract authority | Project assignment or contract/SOW reference | Scope, reporting line and change authority recorded. |  | PENDING |
| Internal Audit liaison | Appoint independent reviewer for segregation, audit evidence and reconciliation oversight. | Executive Sponsor/Internal Audit authority | Appointment/nomination record | Independent access and reporting route documented. |  | PENDING |

## Minimum duty boundaries

- System administrators may create/disable accounts only through approved requests; they cannot grant themselves financial authority.
- Finance makers cannot approve their own tariffs, refunds, reversals, manual matches or discrepancy resolutions.
- Developers and technical administrators cannot confirm payments, issue official receipts or alter production financial records outside approved support procedures.
- Privacy and Security owners may stop data processing or deployment within their approved mandates.
- Shared accounts are prohibited except an approved, vaulted emergency account with monitored use.

## Acceptance signatures

| Approver | Name/title | Decision | Date | Signature / evidence reference |
|---|---|---|---|---|
| Executive Sponsor/CMD or delegate |  | PENDING |  |  |
| Each named owner (acceptance of duties) |  | PENDING |  |  |
| Internal Audit concurrence |  | PENDING |  |  |

**Document acceptance:** Approved only when all mandatory functions have named owners, each owner accepts their duties, and incompatible assignments are removed or formally mitigated.
