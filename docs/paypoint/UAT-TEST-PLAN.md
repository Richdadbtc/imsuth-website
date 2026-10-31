# IMSUTH PayPoint staging UAT test plan

## Rules and evidence

Use synthetic data only. Every tester records date/time, role, browser/device, test-data identifier, expected result, actual result, pass/fail and screenshot or log reference. A test is not passed without execution evidence. Failed financial or access-control tests block sign-off.

## Entry criteria

- Deployment is authorised; HTTPS certificate is valid; IP/VPN allow-list plus outer authentication are active.
- `DEBUG=false`; staging banner is visible; test adapter is enabled; no production credentials or records exist.
- All six containers are healthy and PostgreSQL/Redis have no public ports.
- Synthetic accounts for all seven roles are issued individually; shared administrator credentials are prohibited.

## Core workflow cases

| ID | Actor | Test | Expected result | Current evidence |
|---|---|---|---|---|
| WF-01 | Registration Officer | Register synthetic patient | Unique Patient ID generated; audit event recorded | Automated PostgreSQL test passed |
| WF-02 | Billing Officer | Select active service/tariff and issue invoice | Totals correct; immutable issued invoice; unique number | Automated test passed |
| WF-03 | Cashier | Initiate deterministic sandbox payment | Pending attempt created; no real provider contacted | Automated test passed |
| WF-04 | Test harness | Send correctly signed verification webhook twice | First confirms once; duplicate is idempotent | Automated test passed |
| WF-05 | Cashier | Open/print receipt | One receipt; verification token/URL; no duplicate posting | Automated test passed; physical print pending |
| WF-06 | Management | View notification and dashboard | Payment notification and updated aggregate visible | Automated test passed |
| WF-07 | Finance Officer | Create and complete reconciliation | Confirmed payment included once; discrepancy recorded as applicable | Automated test passed |
| WF-08 | Finance Officer | Attempt invalid refund/void/approval transition | Rejected; original transaction preserved; audit entry created | Execute in staging |

## Role and segregation cases

For each role, verify login, permitted navigation/API operations, direct-URL denial and audit trail.

| Role | Must be able to | Must not be able to |
|---|---|---|
| Administrator | Manage users/system configuration | Perform cashier, approval or reconciliation operations solely because of admin/superuser status |
| Registration Officer | Create/update permitted patient demographics | Price services, confirm payments, reconcile |
| Billing Officer | Create/issue invoices from approved tariffs | Confirm payments, approve adjustments, reconcile |
| Cashier | Initiate/verify payment and issue permitted receipts | Change tariffs, approve own exception, reconcile |
| Finance Officer | Reconcile and perform authorised finance review | Alter patient registration or bypass approval thresholds |
| Auditor | Read reports, audit and financial evidence | Create or change operational/financial records |
| Management | Read dashboard and notifications | Create/change transactions or user access |

Automated PostgreSQL permission tests currently pass for all seven roles, including denial of financial APIs to a Django superuser without a PayPoint financial role. Manual navigation and direct-URL cases remain required.

## Routing and security cases

- `GET /paypoint/login/` renders over HTTPS; an unauthenticated protected URL redirects back under `/paypoint/`.
- Session and CSRF cookies have `Secure`, `HttpOnly` where applicable, `SameSite=Lax` and path `/paypoint/`.
- CSRF rejects missing/incorrect tokens and accepts the approved HTTPS origin.
- API endpoints remain under `/paypoint/api/v1/`; schema and Swagger pages load under `/paypoint/api/schema/` and `/paypoint/api/docs/` for authorised users.
- Static files resolve under `/paypoint/static/`; no mixed-content requests occur.
- Receipt verification/printing URLs preserve the prefix and contain no sensitive details beyond approved minimal verification output.
- HTTP redirects to HTTPS; invalid hosts fail; `/healthz` reveals no secrets.
- Login and API rate limits return the configured response without affecting normal use.
- Test webhook rejects bad signatures, wrong amounts/references and requests when test mode is off.

## Concurrency and resilience cases

- Submit the same payment idempotency key concurrently: one payment is created and all successful responses identify it.
- Submit different keys for the same invoice concurrently: business rules prevent an incorrect double confirmation.
- Deliver the same provider event concurrently/repeatedly: a single ledger effect and receipt result.
- Restart web, worker, beat, Redis and PostgreSQL individually; observe recovery, task behaviour and no duplicated posting.
- Reboot host and verify `unless-stopped` services recover healthy.
- Fill/restrict a resource limit in a controlled exercise and verify service isolation and alerting.

The threaded PostgreSQL payment-idempotency test passed locally. Container restart/failure cases are pending the authorised VPS.

## Device and print matrix

| Surface | Minimum checks |
|---|---|
| Desktop 1440×900 | Navigation, dense tables, modals/forms, dashboard charts, focus order |
| Tablet 768×1024 | Navigation collapse, form labels/errors, table overflow, touch targets |
| Mobile 390×844 | No horizontal page overflow, essential actions reachable, readable status/amounts |
| A4 print | Correct margins, totals, identifiers and verification code; controls/navigation hidden |
| 80 mm thermal | No clipping, readable totals/reference, economical spacing, clean page break |

These cases are **not yet passed**. The in-app browser runtime could not connect to the workstation-local listener; they must be run on the protected staging URL and a representative receipt printer.

## Backup/restore acceptance

Create a custom-format PostgreSQL backup, record checksum/time/size, restore to an empty database, run migrations/checks, compare counts and sample financial references, then have Finance verify a restored synthetic invoice/payment/receipt/reconciliation chain. The local exercise passed with checksum verification and one complete synthetic chain. Repeat on the target host and record recovery time.

## Exit criteria

- All critical workflow, role, routing, security and restore cases pass.
- No open Critical/High security finding; Medium findings have accountable owners and dated remediation/risk acceptance.
- Finance, Security, Privacy, System Administration and UAT lead sign the evidence pack.
- Test-adapter and synthetic-data-only constraints remain enforced for the life of staging.
