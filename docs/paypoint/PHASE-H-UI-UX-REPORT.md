# IMSUTH PayPoint Phase H — UI/UX implementation report

**Date:** 11 October 2026  
**Scope:** PayPoint Django application only. The IMSUTH public website and production infrastructure were not changed.

## Outcome

Phase H delivers a cohesive, server-rendered staff interface over the existing PayPoint financial workflows. The implementation preserves approved-tariff billing, provider-controlled payment confirmation, immutable receipts, audit events, maker-checker controls and role enforcement.

## Initial audit

The starting application had functional login, dashboard, patient/invoice/transaction lists, management totals, reconciliation list and receipt views. It did not provide an integrated patient registration flow, patient profile, invoice creation, cashier payment flow, transaction detail/timeline, finance workspace, audit viewer, password recovery, branded error state, permission-aware application shell or responsive navigation. Existing presentation was a single compact stylesheet and horizontal header rather than a role-specific hospital operations workspace.

### Audited flow health

1. **Staff authentication — partial:** login existed; recovery and consistent secure-state guidance were missing.
2. **Operational dashboard — partial:** only registry/catalogue counts were visible; actions and role priorities were absent.
3. **Patient registration — missing:** API/backend support existed but no staff registration screen or continuation to billing.
4. **Billing — partial:** invoice list existed; guided creation and invoice detail were missing.
5. **Cashier payment — missing:** no integrated payment-method, verification-state or receipt continuation screens.
6. **Finance and management — partial:** basic aggregates/reconciliation existed; approvals, settlements, audit evidence and richer summaries were incomplete.
7. **Administration — partial:** Django Admin existed; the main interface did not route administrators to configuration/API tools.
8. **Receipt — partial:** printable content existed but lacked full service, payment-channel, provider and verification details.

## Implemented experience

### Shared design system

- Institutional navy `#082F49`, medical teal `#0F766E`, neutral background and accessible text palette.
- Collapsible desktop/mobile sidebar, compact top bar, user role, synthetic-data staging marker, breadcrumbs and secure POST logout.
- Reusable cards, metrics, status badges, tables, filters, alerts, forms, pagination, timelines, workflow steps, details lists and empty states.
- Responsive behavior at the requested breakpoint range, touch-friendly controls, visible keyboard focus, skip link and reduced-motion support.
- Permission-aware navigation backed by server-side role mixins; hiding a link is never the access control.

### Authentication

- Professional staff login with audit/authorisation guidance.
- Password reset request, confirmation and completion templates.
- Branded access-denied state.
- Existing Django session expiry behavior returns users to the login view with their intended destination preserved.

### Role-specific workspaces

- Front Desk: patient search, registration, profile, billing history and direct continuation to billing.
- Cashier: pending invoice access, payment method selection, safe initiation, payment state and receipt continuation.
- Accounts/Finance: revenue dashboard, approvals/settlements, reconciliation and transaction evidence.
- Management: confirmed revenue summaries, exceptions, notifications, channels, departments and recent transactions.
- Auditor: read-only transaction, reconciliation and append-only audit evidence views.
- Administrator: user/configuration administration and API documentation links; financial records remain inspection-only in Django Admin.

### Guided workflow

The interface presents the patient → service → invoice → payment → receipt progression. Invoice creation resolves the approved current tariff in the domain model; the form does not expose an amount override. Electronic payments remain pending until the existing signed provider-event service confirms them. The interface provides no manual “mark paid” control.

### Receipts

Receipts now include hospital identification, receipt and invoice references, Patient ID, service lines, total, channel, provider reference, payment reference, date/time, status and verification token. A4 and 80 mm thermal variants use print-specific CSS that removes navigation and controls.

## Security and accessibility findings

- Financial screen access is enforced by server-side role checks; a cashier receives HTTP 403 for patient registry and management reporting.
- REST API URLs are namespaced to prevent their route names resolving in place of staff HTML pages.
- Form fields have programmatic labels, required-state indication and inline errors.
- Status meaning is provided in text, not colour alone.
- Tables retain semantic headers and scroll within their container on narrow screens.
- Keyboard focus is clearly visible; a skip link bypasses repeated navigation.
- The mobile sidebar uses an explicit button with `aria-controls` and updated `aria-expanded` state.
- Screenshot inspection cannot prove WCAG 2.2 AA. Screen-reader, contrast-tool and full keyboard-path testing still require execution in an accessible staging browser.

## Test evidence

- Phase H UI suite: **5/5 passed**.
- Full isolated regression suite: **34 tests passed, 1 PostgreSQL-only test skipped** under SQLite test settings.
- Covered login/password-reset rendering, patient registration, approved-tariff invoice creation, cashier payment initiation, pending electronic-payment state, core template rendering and server-side role denial.
- Existing financial/API/operations regression tests remained green.
- Django system check reported no issues.

The PostgreSQL concurrency test passed in the preceding staging-readiness run; it was not re-claimed from the SQLite execution above.

## Visual verification and screenshots

The local application server started successfully and was reachable from the workstation. The isolated in-app browser could not connect to the workstation listener through localhost or the LAN address, so valid screenshots could not be captured in this run. No screenshots are included or claimed. Desktop/tablet/mobile visual inspection, browser accessibility tooling and physical receipt-printer output remain an explicit UAT gate on the protected staging URL.

## Remaining issues

- Execute visual/device checks at 320, 375, 768, 1024 and 1440 pixels on an authorised HTTPS staging endpoint.
- Run keyboard-only and screen-reader testing, automated contrast/accessibility inspection and representative hospital desktop/browser testing.
- Print one A4 and one 80 mm receipt using synthetic data and obtain cashier sign-off.
- Notification settings and system configuration continue through controlled Django Admin rather than custom duplicate screens.
- Approval decisions, refund/reversal execution and settlement import remain controlled backend/provider workflows; Phase H exposes their evidence and queues but does not invent unsafe mutation controls.

## Status

**Implementation complete for local review. Conditional acceptance for UAT.** Visual/device/printer evidence is still required before Phase H can be signed off for staging users.
