# IMSUTH PayPoint — Dashboard UI Implementation

**Implementation date:** 11 October 2026
**Scope:** PayPoint application only (`/Users/mac/Documents/imsuth/backend/`)
**Technology:** Django templates, HTML5, CSS3, vanilla JavaScript ES6+
**Backend:** Django 6.0, Django REST Framework, Celery (unchanged authority)

## Outcome

The PayPoint staff interface is a complete, navigable, responsive hospital revenue
management dashboard built on the existing secure Django backend. The management
dashboard (Screen 2) and patient management dashboard (Screen 3) are implemented
with native HTML/CSS/SVG/JavaScript charts, server-side data, role-aware navigation
and progressive enhancement. No frontend framework, charting library or build tool
was introduced. The public IMSUTH website and production infrastructure were not
modified.

## Files created

| File | Purpose |
|---|---|
| `docs/paypoint/DASHBOARD-UI-IMPLEMENTATION.md` | This delivery report |

## Files modified

| File | Change |
|---|---|
| `website/paypoint/templates/base.html` | Reusable authenticated shell with official branding, global search, notification count, profile menu, responsive navigation and versioned static assets. |
| `website/paypoint/templates/operations/management_dashboard.html` | Complete management dashboard with live KPIs, native SVG chart targets, transactions, approvals and operational summaries. |
| `backend/apps/operations/views.py` | Efficient confirmed-revenue aggregation for daily, weekly and monthly channel series, department proportions, pending workflows and daily operational counts. |
| `website/paypoint/static/paypoint/app.css` | Institutional dashboard design system, responsive shell, management and patient layouts, chart styling, tables, tabs and mobile drawer behavior. |
| `website/paypoint/static/paypoint/app.js` | Sidebar, search, patient tabs, chart period controls, native SVG rendering, loading states and progressive UI interactions. |
| `backend/config/urls.py` | Added the authorized patient-edit route. |
| `website/paypoint/templates/registry/patient_form.html` | Shared registration/edit form with audit-aware edit messaging and submission feedback. |
| `website/paypoint/templates/includes/pagination.html` | Filter-preserving server-side pagination controls. |
| `backend/apps/common/test_complete_frontend.py` | Patient filter, audited edit and native management-chart regression coverage. |
| `backend/apps/registry/models.py` | Added `full_name` and `initials` properties to `Patient` for clean, whitespace-safe name rendering. |
| `backend/apps/registry/views.py` | `PatientListView`: added department filter (via issued invoices), phone-digit normalisation in search, and active-department context. `PatientUpdateView`: capture persisted values in `get_form_kwargs` before the `ModelForm` mutates the instance, so audit revisions record the true before/after. |
| `website/paypoint/templates/registry/patient_list.html` | Use `patient.full_name`; added Department filter control and clear-filter handling. |
| `website/paypoint/templates/registry/patient_detail.html` | Use `patient.full_name` and `patient.initials` in the profile header and overview. |

## Screens completed

### Global dashboard shell (`website/paypoint/templates/base.html`)

- Top navigation: IMSUTH crest/logo, PayPoint branding, "Hospital Revenue Management
  System" subtitle, global navigation search, notification bell with unread count,
  logged-in staff name and role, profile dropdown and POST-only logout.
- Left sidebar: Dashboard, Patients, Billing, Payments, Finance, Administration,
  Reports, plus a Quick Actions section and IMSUTH footer branding with a service
  status indicator.
- Role-aware visibility driven by `user.role`; authorization remains enforced in
  Django views (hiding navigation is not treated as authorization).
- Sidebar collapse (persisted in `localStorage`), mobile drawer, and keyboard
  escape-to-close.

### Management dashboard — Screen 2 (`website/paypoint/templates/operations/management_dashboard.html`)

- Header: "Welcome, [Authenticated Staff Name]", "Management Dashboard", overview
  subtitle and a date-range selector.
- Five KPI cards: Today's Revenue, This Week's Revenue, This Month's Revenue, Total
  Transactions, Outstanding Invoices — all from authorized backend aggregates.
- Revenue Overview: native SVG stacked bar chart with Daily / Weekly / Monthly
  toggles and Cash / Bank Transfer / POS / Online channel legend, plus an accessible
  table alternative.
- Revenue by Department: native SVG donut chart with legend, total and date-range
  filtering.
- Recent Transactions: reference, patient, department, amount, method, status, date
  and time, with links to authorized transaction detail.
- Pending Approvals: payment verifications, approval requests, refunds, reversals
  and tariff updates, each linking to an existing authorized workflow.
- Bottom summary cards: new patient registrations, invoices created, verified
  payments and reconciliation discrepancies.

### Patient management — Screen 3 (`website/paypoint/templates/registry/patient_list.html`, `patient_detail.html`)

- Page header with title, subtitle and "+ Register Patient" primary action.
- Four statistics cards: Total Patients, New This Month, Active Patients, Pending
  Records — all backed by existing model fields.
- Search by name, patient ID and phone (with digit normalisation); department filter
  (via issued invoices); status filter; clear filters; server-side pagination.
- Patient table: Patient ID, Full Name, Date of Birth, Gender, Phone Number, Status,
  Actions (View / Edit).
- Patient detail panel: initials avatar, name, patient ID, registration status, edit
  action, and Overview / Billing History / Invoices / Payments tabs with keyboard
  arrow navigation.
- Quick actions: Create Invoice, View All Invoices, View All Payments.

### Related screens (existing, connected)

Staff login, password reset, patient registration/profile/edit, invoice list/create/
detail/print, payment processing/verification/success, receipt A4 and 80 mm, finance
dashboard, reconciliation, staff management, audit logs and reports.

## Working interactions (vanilla ES6)

- Sidebar toggle, collapse and mobile drawer.
- Profile dropdown, tab switching, search interactions.
- Date-range controls and chart period toggles.
- Pagination controls, loading indicators, toast messages.
- Notification interactions, confirmation actions, form enhancement.
- Native SVG revenue and department chart rendering.
- Progressive enhancement: forms and navigation remain functional without JavaScript.

## Backend integrations

- Management dashboard uses `Payment` (confirmed only), `Invoice`, `ApprovalRequest`,
  `Refund`, `Reversal`, `TariffVersion`, `ReconciliationBatch` and `Patient` with
  `Sum`/`Count` aggregation and `TruncDate`/`TruncWeek`/`TruncMonth` grouping.
- Patient list uses indexed `patient_id`, `normalized_phone` and name fields with
  server-side filtering and pagination.
- Patient detail prefetches invoices and payments to avoid N+1 queries.
- CSRF protection, authentication, role-based access, pagination, data minimisation
  and audit logging are preserved. No financial calculation or authorization
  decision is made in client-side code.

## Tests executed

| Check | Result |
|---|---|
| Django system check (`manage.py check`) | No issues (0 silenced) |
| Migration drift (`makemigrations --check --dry-run`) | No changes detected |
| Full test suite (`manage.py test`) | **44 tests, OK (1 skipped)** |
| Focused frontend + Phase H UI suites | **15 tests, OK** |
| JavaScript syntax validation (`node --check`) | Passed |
| Static asset collection (`collectstatic`) | 1 copied, 192 unmodified, 485 post-processed |

The skipped test is the PostgreSQL-only concurrency test. It is **not** reported as
passed. The fresh PostgreSQL Phase I run remains blocked by the separately documented
local storage/database contention.

## Browser verification and screenshots

Genuine browser rendering was executed against the local Django application using
synthetic accounts and records:

- Management dashboard: desktop viewport captured and compared with the supplied
  Screen 2 reference. The authenticated shell, five-KPI row, revenue chart, department
  chart, table and approvals structure were visibly verified.
- Patient management dashboard: desktop viewport captured after implementation.
- Patient management dashboard: 375 × 812 mobile viewport captured and checked for
  KPI stacking, drawer navigation, accessible primary action and table containment.
- The oversized footer crest and stale cross-screen header styles found during browser
  QA were corrected. Static asset versioning was added to prevent stale UI caching.

The attempted final 1536 × 1024 recapture timed out in browser automation. The earlier
desktop captures are genuine; exact pixel-for-pixel parity at every requested viewport
is not claimed.

## Remaining blockers

- Browser checks were completed at the default desktop viewport and 375 × 812.
  Dedicated captures at 320, 768, 1024 and 1440 px remain follow-up verification.
- Automated accessibility tooling, screen-reader testing and physical A4/80 mm
  printing were not executed.
- The fresh PostgreSQL Phase I run, including concurrency, remains blocked by the
  documented local database contention; the skipped SQLite test is not reported as
  passed.
- NHIS number is not present in the `Patient` model, so the NHIS column and search
  were intentionally omitted rather than inventing a field.
- Patient notes are not shown because the backend does not provide secured note
  storage with permissions; the section was omitted rather than introducing
  unsecured storage of sensitive information.
- Provider-specific bank-transfer instructions, settlement execution and provider
  refund execution remain governance-backed capabilities; the UI retains pending
  states rather than fabricating success.

## Security preservation

No payment verification, billing calculation, financial approval, reconciliation
authority, role authorization or audit control was delegated to JavaScript. No real
patient data, bank account, live provider or production secret was used. The public
IMSUTH website was not modified and no production deployment was performed.
