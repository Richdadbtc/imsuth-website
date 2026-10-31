# Gate 1.3 — Financial and Access-Control Policy Approval Checklist

**Status:** PENDING  
**Decision requested:** Approve the minimum control baseline required from the first Phase B commit. Unresolved operational policies remain disabled.

## Gate 1 control checklist

| ID | Required decision/control | Accountable approver | Evidence of approval | Acceptance criteria | Status |
|---|---|---|---|---|---|
| C1 | Deny access by default; enforce permissions server-side and scope access by role, department and PayPoint. | Security Owner; System Owner accountable for operation | Signed policy/approved minutes | No UI-only authorization; default roles have no implicit financial power. | PENDING |
| C2 | Approve initial separation among system administration, tariff approval, payment capture, financial approval, reconciliation and audit. | Finance Owner with Internal Audit concurrence | Approved role-conflict matrix | A maker cannot approve their own action; administrators cannot bypass financial workflows. | PENDING |
| C3 | Prohibit real patient, staff, bank or transaction data in local development, tests, fixtures, screenshots and logs. | Privacy Owner and Security Owner | Signed local-development/data-handling authorization | Only generated synthetic identities/data; breach escalation is defined. | PENDING |
| C4 | Require decimal currency values, server-side totals, database constraints and transactional reference generation. | Finance Owner and Technical Delivery Lead | Signed architecture/control approval | No floating point or browser-authoritative total; uniqueness/concurrency tests required. | PENDING |
| C5 | Make financial/audit events append-only; prohibit silent deletion or overwrite. | Finance Owner and Internal Audit | Approved financial-record policy | Corrections use approved state transitions/compensating records and retain actor/reason/history. | PENDING |
| C6 | Require authenticated provider evidence for electronic-payment confirmation; distinguish confirmation from settlement. | Finance and Security Owners | Signed control policy; provider evidence later | Browser/cashier action alone cannot confirm electronic payment. | PENDING |
| C7 | Prevent an official paid receipt until authorized confirmation commits successfully. | Finance Owner | Signed receipt control policy | Receipt creation is transactional, unique and blocked for pending/unverified payment. | PENDING |
| C8 | Require idempotency, unique external event IDs, replay protection and locked transitions. | Security Owner and Technical Delivery Lead | Approved technical control record | Duplicate requests/events cannot create duplicate financial effects or receipts. | PENDING |
| C9 | Require named accounts, secure sessions, strong password hashing, MFA readiness and auditable authentication events. | Security Owner | Approved identity baseline | Shared normal accounts prohibited; privileged design supports step-up/MFA. | PENDING |
| C10 | Keep secrets and sensitive exports outside Git and `public_html`; redact sensitive logs. | Security and Privacy Owners | Approved secret/logging standard | Fail-closed configuration; no credentials, full card data, PIN/CVV or unnecessary patient data retained. | PENDING |
| C11 | Require reviewed migrations, automated tests, dependency locking/scanning, secret scanning and protected releases. | Technical Delivery Lead with Security concurrence | Approved engineering standard/CI record | Checks are mandatory before merge; production release remains separately approved. | PENDING |
| C12 | Keep unresolved channels/features disabled by default. | System and Finance Owners | Signed feature-activation rule | Cash/POS, partial payments, refunds, provider confirmation and production receipts cannot activate without later policy/provider approval. | PENDING |

## Policy decisions explicitly deferred beyond generic foundation work

These remain **PENDING** and must not be inferred from Gate 1:

- [ ] Final patient identifier, mandatory demographics, duplicate merge and correction authority.
- [ ] Detailed role grants and department/PayPoint visibility.
- [ ] Approved payment channels and locations.
- [ ] Partial payments, deposits, overpayments and allocation rules.
- [ ] Invoice, receipt and adjustment numbering formats.
- [ ] Tariff proposal/approval and emergency tariff changes.
- [ ] Transaction thresholds, escalation times and absence cover.
- [ ] Refund, reversal, void, write-off, reprint and closed-period policies.
- [ ] Cashier shifts, tills, cash counts, terminal mapping and close-of-day.
- [ ] Official dashboard definitions and export entitlements.
- [ ] Provider/bank integration behavior and settlement formats.

## Approval record

| Approver | Required authority | Decision | Date | Signature / evidence reference |
|---|---|---|---|---|
| Executive Sponsor | Accepts baseline and deferred-feature rule | PENDING |  |  |
| Finance Owner | Accepts C2, C4–C7, C12 | PENDING |  |  |
| Privacy/DPO Owner | Accepts C3 and C10 | PENDING |  |  |
| Security Owner | Accepts C1–C3, C6, C8–C12 | PENDING |  |  |
| Internal Audit | Concurs with C2, C5 and auditability | PENDING |  |  |
| Technical Delivery Lead | Confirms controls are implementable/testable | PENDING |  |  |

**Document acceptance:** Every C1–C12 row must be approved. Deferred items remain disabled and require later documentary approval.
