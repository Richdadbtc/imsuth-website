# Revenue Control API security review — 24 October 2026

## Implemented controls

- DRF session authentication and CSRF checks remain enabled; the Django-served shell selects live API mode. Compatibility mounts do not bypass permissions. No bearer token storage or new authentication framework.
- Department-scoped registry/catalogue/invoice/payment/receipt/desk/alert reads. Unassigned operational users receive no department financial records; front desk can still access patients they registered. Finance, management, auditor and super administrator have explicit broader visibility.
- Financial writes remain restricted by their existing role permissions. New cash approvals and tariff decisions forbid the maker from deciding their own request. Cash policy limits require an active management/super-administrator approver and a recorded policy reference; there is no default allowance.
- Row locks serialize invoice-based delivery and cash-point daily reservations. Database uniqueness enforces single delivery, payment idempotency, cash-order idempotency, collection-evidence payment attribution and detector alert attribution.
- Positive monetary database constraints and decimal serializer fields; invoice pricing stays server-side and historical InvoiceItems remain immutable. Financial reporting distinguishes created attempts, confirmed receipts, refunds/reversals and bank settlement.
- User-submitted references are stored separately from authoritative provider references. Unsupported live confirmation returns 503. Cash orders and alert resolution cannot mark payments confirmed or settled.
- Audit API supports no create/edit/delete. Model audit events are append-only through normal save/delete operations. User role changes include before/after metadata. Sensitive metadata keys are redacted recursively; API request logs omit bodies, raw URLs/query strings and secrets. Recovery continues using existing expiring, single-use verification behavior.
- Patient and staff values rendered by the client pass through escaping; receipt HTML uses Django template escaping. API responses are private/no-store. Staff password fields are write-only; hashes and sessions are not serialized.

## Actual verification

Tests exercise unauthenticated denial, seven-role model reuse, scoped department access, self-approval rejection, missing/insufficient cash limits, duplicate delivery, concurrent limit reservations, alert notes and non-confirmation, paid-receipt eligibility, reference submission, audit immutability, redaction and CSRF/session behavior. PostgreSQL concurrency tests run in an isolated synthetic database, not SQLite. This is targeted review and testing, not an independent penetration test.

## Residual risks / incomplete work

- External payment adapters, bank deposit confirmation, hospital-approved insured category rules and policy thresholds are unconfigured. Those workflows must remain unavailable; configuration is not proof of a verified bank integration.
- A number of older administration/report/verification resources predate the new scoped operational APIs. Broader permission review is still needed across the entire legacy API surface before production certification. Restoring archived Django page routes without reviewing those views would reopen an unreviewed path; this increment does not do that.
- Audit immutability is enforced at application/API level. A database owner can still bypass ORM protections; operational DB grants, backups and tamper-evident external retention require deployment-specific controls, not an invented guarantee.
- Free-text notes can contain sensitive material supplied by a user. Do not enter passwords, codes, card details or patient diagnoses into financial audit/resolution notes. This implementation does not claim semantic detection of secrets embedded in arbitrary text.
- Large client directory loaders, incomplete server-filter bindings, and remaining browser workflow tests need completion. Schema alias/enum warnings remain, despite zero schema validation errors.
- Production cookie/TLS/proxy settings, Redis/Celery worker operation, database privileges, monitoring and recovery delivery must be verified in the actual deployment. No production configuration was changed here.

## Release decision

Suitable for continued local/staging integration with synthetic data. **Not certified production-ready** until the integration-report blockers and deployment/security verification are completed.
