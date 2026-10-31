# Revenue Control API integration — 24 October 2026

## Status: substantial increment implemented; production readiness remains partial

The authored client remains HTML5, CSS3 and vanilla ES6 JavaScript. No frontend framework, TypeScript, Node runtime, JavaScript dependency manifest or build pipeline was introduced. Django serves the existing HTML shell as a template at `/paypoint/` and `/paypoint/index.html`, with live mode fixed false for `demoMode`. Static `/website/paypoint/` remains an explicitly labelled demo preview; it is not the production entry point. Asset sources are shared through Django staticfiles.

## Implemented

- Compatible API mounts `/api/v1/` and `/paypoint/api/v1/`, keeping existing consumer names in the original namespace.
- Dashboard summary/channel/department/status/recent/alert/trend resources with date contracts and server aggregates. Live overview financial totals use server results.
- Patient search, scoped catalogue and invoice/payment/receipt queries; invoice balance; payment verification status; authorized paid receipt HTML print view. Reference submission is stored separately from provider confirmation.
- Existing server-priced invoice snapshots and payment idempotency are reused. Idempotency keys with conflicting payloads/actors are rejected; reference entry cannot confirm a payment.
- Department Desk receipt checks, purchased item details, pending/activity/summary resources, and atomic delivery records linked to existing InvoiceItems and Receipts. The database enforces one delivery per item. The live desk calls these endpoints.
- Department nested resources and server analytics. The current Departments page consumes server aggregates and existing create APIs.
- Service category/unit metadata, approved current tariff lookup/history, tariff proposals and independent decisions. Original tariff creation records the proposer; self-approval and missing-proposer approval are denied. Controlled proposal approval schedules validity windows under the service lock without changing historical invoice unit prices.
- Cash point CRUD without deletion; validated officer/department assignments; explicit verified-cash-payment evidence; confirmed cash point collection summaries. Evidence does not certify bank deposit.
- Cash order requests, idempotency, serialized daily reservations, approval/rejection, immutable decisions, maker-checker separation and configured policy limits. No illustrative limits are seeded. The live cash page supports creation, requests and decisions.
- Alert lifecycle, assignment, read summaries/analytics, notes-required resolution and audit. A Celery reconciliation detector is idempotent and does not mutate payments. Alert resolution cannot confirm a payment.
- User aliases over the existing seven-role custom User model, activation/deactivation, safe permissions reads and immutable audit aliases/summaries. Role changes record before/after roles. The live Users and Audit page submits authenticated account changes.
- Same-origin session/CSRF integration; no access tokens or patient records stored in localStorage. Loading/error states use existing client components. API logs omit request bodies/query strings. Audit metadata redacts sensitive keys recursively. Responses are marked private/no-store.

## Screen connection matrix

| Screen | Connected workflow | Remaining limit |
|---|---|---|
| Overview | Server totals, grouped data and alert counts; authorized transaction reads | Large-directory client loaders still fetch pages for local display; further server-side filtering/performance work is needed. |
| Record Payment | Authorized patient/catalogue lookup, server-priced invoice and unverified payment intent | Live bank/POS/cash confirmation evidence workflow is unconfigured. No live paid receipt is invented. A bounded status poll checks backend status and links an official receipt only after confirmed issuance; this continuation has not been fully exercised in the browser. |
| Department Desk | Authorized receipt check and atomic service delivery | Full browser delivery interaction remains unverified; physical printers not tested. |
| Departments | Authenticated catalogue create/read and server summaries | Some presentation grouping/pagination remains client-side. Staff assignment uses the administrator Users API. |
| Services and Prices | Catalogue save and independent tariff proposals and decisions; current approved prices | The live editor creates proposals and shows independent approve/reject controls with decision notes. Comprehensive browser testing remains pending. NHIS/IMSHIA eligibility/pricing policy is unavailable. |
| Cash Points and Orders | Create point, record authorization request, approve/reject with server limits, read verified collection evidence | Evidence upload/linking exists as an API; a dedicated evidence/deposit UI is pending. Bank deposit certification is unavailable. |
| Alerts | Authorized read, assign, start review and resolve | Notification preference controls explicitly disabled. Only reconciliation detector is implemented; suspicious-activity thresholds and other automatic detectors require policy/configuration. |
| Users and Audit | Live create/edit users, read audit activity, safe role choices | Secure onboarding uses recovery; phone editing is explicitly disabled on this form. Browser edit interaction timed out and is not claimed verified. |

## Verification evidence

- Fresh pre-change SQLite baseline: **68 tests, 44 passed, 23 legacy URL errors, 1 PostgreSQL concurrency skip**. An initial command from the repository root discovered zero tests; the valid baseline was rerun from `backend/`.
- Isolated PostgreSQL test cluster on localhost port 55439, separate temporary data directory and synthetic-only database. No existing/prod database was migrated or modified.
- Final focused PostgreSQL run: **48 passed**, including all three concurrency tests. This included provider lifecycle/duplicate webhook, reference non-confirmation, authorization, scoped reads, server pricing, delivery, cash limits, alerts, safe users, audit immutability/redaction and template/session integration.
- Final full run before the last small validity-window adjustment: **91 tests, 68 passed, 23 errors, no skips**. All errors remain the pre-existing removed legacy Django page URL names. No PostgreSQL-only test was represented as a pass on SQLite.
- PostgreSQL payment-intent, duplicate-delivery and daily cash-limit reservation concurrency tests ran successfully in that full run.
- All eight current screens were opened in the browser from the Django-served live client using synthetic data and real session login. This is a navigation/data-loading smoke test, not comprehensive interaction or design-fidelity certification. The user-edit browser action timed out. No physical printer test was performed.
- JavaScript syntax, Django system checks and migration drift checks passed. OpenAPI validation completed with zero errors; compatibility aliases and enum naming produce warnings.

Post-adjustment targeted checks passed; see the progress log. Tests changed to assign departments to synthetic front-desk/cashier fixtures and require an independent tariff approver, reflecting the enforced policy rather than weakening access checks.

## Remaining blockers and follow-up

1. Hospital-approved channel verification adapters and cash evidence/confirmation procedure; no bank integrations or credentials invented.
2. Approved NHIS/IMSHIA eligibility, coverage and pricing rules. Only configured self-pay tariff behavior is available.
3. Actual approved cash policy references and approval limits. Empty configuration denies approvals.
4. Expanded automatic alert policy, notification configuration, complete evidence UI and payment status continuation.
5. Comprehensive browser interaction/accessibility/performance verification, real supported-printer checks, and resolution or retirement of 23 legacy page-route tests.
6. The original hospital-supplied HTML reference file could not be uniquely identified; the current client and supplied screenshots were preserved as the available references.

No deployment or production infrastructure changes were made. This report does not certify the entire pasted definition of done as complete.
