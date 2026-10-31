# IMSUTH PayPoint complete frontend implementation

**Implementation date:** 11 October 2026  
**Scope:** PayPoint application only  
**Technology:** Django templates, HTML5, CSS3 and vanilla JavaScript ES6+

## Outcome

The existing PayPoint interface was extended into a broader connected staff application without introducing a frontend framework or moving financial authority into the browser. New screens use the established navy/teal design system, shared base layout, responsive tables/cards/forms, server-side permissions, Django CSRF protection and backend validation.

The public IMSUTH website and production infrastructure were not modified.

## Implemented work

- Expanded role-aware navigation for catalogue, staff administration, notifications and account management.
- Added user profile and secure password-change screens.
- Added super-administrator staff directory, creation, profile and access-update screens with audit events and self-deactivation protection.
- Added department, service and tariff listings/details plus authorized department/service/tariff creation.
- Preserved tariff history by creating new approved versions instead of editing historical tariff rows.
- Added multi-line invoice entry with vanilla JavaScript row management and server-side service/tariff/quantity validation.
- Added invoice print layout and immutable billing-correction request workflow.
- Added payment pending/failure guidance, receipt continuation and receipt-reprint history.
- Added refund/reversal request and maker-checker approval decision screens backed by existing financial services.
- Added reconciliation CSV upload, validation, matching and batch-detail screens.
- Added user-scoped notification list/detail, unread count and POST-only mark-as-read action.
- Added dismissible Django-message toasts, mobile escape/close navigation, submit loading state and native print controls.
- Added a notification read-state migration and six focused frontend integration tests.

## Screen-by-screen completion matrix

| Area | Screen/control | Status | Backend integration | Test/evidence |
|---|---|---|---|---|
| Authentication | Login, password recovery/reset, logout, access denied | Implemented | Django authentication views, POST logout and permission handling | Existing rendering/role tests |
| Authentication | Profile and password change | Implemented | Authenticated update views; password validator/session preservation; audit events | New rendering test; full regression |
| Authentication | Session expiry | Backend-enforced | 30-minute server session age and login redirect; no fabricated client timer | Settings/source review |
| Dashboard | General role-aware overview | Implemented | Live database counts and role navigation | Existing Phase H tests |
| Dashboard | Management revenue | Implemented | Confirmed payments only; date filters and CSV export | Existing staging/operations tests |
| Patients | Directory, search, registration, profile, history, duplicate warning, ID | Implemented | Django forms/views and generated IDs | Existing patient/UI tests |
| Catalogue | Department list/detail/create | Implemented | Role-protected catalogue models and audit event on creation | New role/render/create tests |
| Catalogue | Service list/filter/detail/create | Implemented | Department-bound model validation and role protection | New create/render tests |
| Catalogue | Tariff list/history/create | Implemented | Finance/admin-only approved version creation; historical records preserved | New immutable-version test |
| Billing | Invoice list/detail/status/balance | Implemented | Persisted invoice and tariff snapshots | Existing billing tests |
| Billing | Multi-line invoice creation | Implemented | JS serializes rows; Django validates services/quantities; model resolves authoritative tariffs/totals | New multi-line total test |
| Billing | Billing correction request | Implemented | Creates review record; does not mutate issued invoice | New immutability test |
| Billing | Invoice printing | Implemented | Server-rendered invoice data and print CSS | Rendering test; physical printing not run |
| Payments | Initiation/channel/status/timeline | Implemented | Backend payment intent and verified-event state | Existing payment tests |
| Payments | Pending/failure states | Implemented | Status-driven server output; no client success simulation | Full rendering regression |
| Receipts | Detail, verification, A4/80 mm, reprint history | Implemented | Confirmed-payment-only receipt model and recorded reprints | Existing integrity tests; printer not run |
| Finance | Revenue, channels, departments, export | Implemented | Confirmed-payment queries and permission-scoped CSV | Existing operations tests |
| Finance | Refund/reversal request | Implemented | Existing service creates maker request; no provider execution claimed | Existing service tests; connected screen |
| Finance | Approval decision | Implemented | Existing maker-checker service blocks self-approval | Existing maker-checker tests; connected screen |
| Reconciliation | List, CSV import, detail/results | Implemented | Digest duplicate protection and server-side exact/mismatch matching | New screen test plus existing matching tests |
| Notifications | Center, unread count, detail, mark read | Implemented | User-scoped query, POST-only read action, persisted read timestamp | New ownership/read test |
| Administration | Staff directory/create/profile/role/status | Implemented | Super-admin-only views and audit events | New role restriction/create test |
| Administration | Department/service/tariff management | Implemented for controlled creation and review | Role-scoped views; historical tariff update is intentionally a new version | New tests |
| Administration | Low-level system configuration | Existing Django admin/read-only controls only | No unrestricted UI introduced | Remaining governance dependency |

## Functional-control rules

- All state-changing forms use POST and CSRF protection.
- Role checks are enforced in Django views; navigation visibility is not treated as authorization.
- Invoice totals are calculated from approved tariffs by the Python model service.
- JavaScript manages presentation, extra invoice rows, messages, navigation and printing only.
- Payment success and receipts remain dependent on backend-verified payment events.
- Refunds and reversals create approval requests and never imply external provider execution.
- Reconciliation imports are parsed, validated, digested and matched on the backend.
- Notifications are restricted to their assigned user.
- Staff role changes require the super-administrator role and generate audit evidence.

## Test results

- Focused complete-frontend suite: **6 passed**.
- Full isolated regression suite: **40 passed, 1 PostgreSQL-only concurrency test skipped**, completed in 32.734 seconds.
- Django system check: passed.
- Migration drift check: passed.
- JavaScript syntax check: passed.
- Expected 400, 403 and 404 responses were produced by negative validation, authorization and ownership tests.

## Remaining blockers and limitations

- Browser/device visual checks at 320, 375, 768, 1024 and 1440 pixels were not executed in this run and are not claimed.
- Automated accessibility tooling, screen-reader testing and physical A4/80 mm printing were not executed.
- The fresh PostgreSQL Phase I run, including concurrency, remains blocked by the separately documented local storage/database contention; the skipped SQLite test is not reported as passed.
- Provider-specific bank-transfer instructions cannot be shown until IMSUTH approves verified account/provider configuration.
- Settlement creation/execution, provider refund execution and production notification preferences remain external/governance-backed capabilities; the UI clearly retains pending states rather than fabricating success.
- A dedicated hospital-approved system-configuration workflow would require approved configuration fields and ownership. Unrestricted generic configuration editing was intentionally not introduced.

## Security preservation

No payment verification, billing calculation, financial approval, reconciliation authority, role authorization or audit control was delegated to JavaScript. No real patient data, bank account, live provider or production secret was used.
