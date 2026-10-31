# Gate 1.1 — Architecture Approval

**Status:** PENDING  
**Decision requested:** Approve the Phase A architecture in principle as the basis for isolated Phase B foundation work.

## Concise architecture statement

IMSUTH PayPoint will be a separate, server-side Django application. PostgreSQL will be the authoritative source for patient, billing and financial records. Redis will support queues/cache only; Celery will run background work; Gunicorn will serve Django behind an approved NGINX or equivalent edge. The existing static/PHP public website will remain separate and unchanged during Phase B foundation work.

The production route remains intended as `https://www.imsuth.org/paypoint/`, but the routing method is not yet approved. It depends on hosting evidence and a later deployment decision. No private data may be placed in the public website's JSON files, browser storage or static administration page.

### Non-negotiable control principles

- The browser is untrusted; authorization, tariff selection, totals and payment state are enforced server-side.
- Electronic payment is confirmed only by authenticated provider evidence and/or server-to-server verification.
- Payment confirmation, settlement and reconciliation are separate facts.
- Official paid receipts follow only a committed authorized payment confirmation.
- Financial and audit histories are append-only; corrections use controlled transitions or compensating records.
- Least privilege and maker-checker separation apply; System/Super Administrators cannot bypass financial approval rules.
- Development, staging and production remain isolated; only synthetic data is permitted outside production unless separately approved.
- Production/DNS/TLS/cPanel/public-site changes require separate explicit approval.

## Decision record

| Item | Required decision | Accountable approver | Evidence of approval | Acceptance criteria | Status |
|---|---|---|---|---|---|
| A1 | Accept the separate Django/PostgreSQL architecture and public-site separation. | Executive Sponsor/CMD or delegated approving authority | Signed document or controlled decision record | Architecture, system boundary and public-site preservation are accepted. | PENDING |
| A2 | Accept the trust boundaries and non-negotiable controls above. | Executive Sponsor with Finance, Privacy and Security concurrence | Signatures below or linked approved minutes | No control is removed; any clarification is documented without weakening the baseline. | PENDING |
| A3 | Accept local containerized foundation work as the intended Phase B mode, subject to Gate 1 completion. | System Owner and Technical Delivery Lead | Signed authorization and technical decision reference | Work remains local, isolated and synthetic-data-only. | PENDING |
| A4 | Acknowledge that production routing and provider integrations are excluded. | Executive Sponsor and System Owner | Signed acknowledgement | No party interprets architecture approval as deployment or payment-provider approval. | PENDING |

## Deviations or conditions

Record proposed deviations; blank means none proposed, not approved.

____________________________________________________________________________

____________________________________________________________________________

## Approval signatures

| Role | Name/title | Decision | Date | Signature / evidence reference |
|---|---|---|---|---|
| Executive Sponsor/CMD or delegate |  | PENDING |  |  |
| Finance Owner concurrence |  | PENDING |  |  |
| Privacy/DPO concurrence |  | PENDING |  |  |
| Security Owner concurrence |  | PENDING |  |  |
| System Owner concurrence |  | PENDING |  |  |

**Document acceptance:** Approved only when A1–A4 meet their acceptance criteria and all required concurrence is evidenced.
