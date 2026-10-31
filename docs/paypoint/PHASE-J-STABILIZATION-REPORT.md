# Phase J stabilization report

24 October 2026. **Local stabilization verified; hospital visual acceptance and operational/live integration acceptance remain pending.** No production deployment, live provider call, bank transfer, real patient operation or public website change was performed in this phase. Phase J changes have not been pushed to GitHub.

## Result

The original 23 legacy-route errors are resolved through authenticated compatibility bookmarks and justified retirement of obsolete server-rendered forms. The final PostgreSQL regression suite passed 103 tests, zero failures/errors and zero skips. A separate focused PostgreSQL run passed 54 tests, and all three concurrency tests passed. All eight Revenue Control screens were exercised through actual browser interactions with synthetic accounts and data. See BROWSER-UAT-RESULTS.md for the exact coverage and limitations.

The owner-designated `website/paypoint` folder is the current application; an independent original hospital HTML export could not be identified. Available screenshot structure was compared and remaining visual differences documented in HOSPITAL-UI-FIDELITY-REPORT.md. Exact reproduction and hospital acceptance are not claimed.

## Changes implemented

- Preserved HTML5/CSS3/vanilla ES6 and Django/DRF. No framework, build-system migration or UI redesign.
- Restored 34 legacy URL names as secure bookmark/retirement handlers; current API paths/names remain intact.
- Preserved meaningful legacy test purposes through current API behavior: registration, immutable multi-line billing, patient revisions, correction requests, independent tariff decisions, scoped inbox/import, dashboard scope, official receipt and authentication.
- Added an atomic invoice correction-request endpoint and patient-edit revision/audit handling. Corrections do not mutate issued financial snapshots.
- Fixed API serializer uniqueness validation so identical idempotent invoice/payment retries reach existing domain safeguards instead of failing prematurely. Different-payload conflict controls remain authoritative.
- Added bounded server pages and server filtering for Overview transactions and Departments. Prefetched service summaries/receipts avoid row-by-row queries. Page size defaults to 25 and is capped at 100; UI uses 10.
- Fixed User Edit ID comparison and department option values; saved user edits retain department scope.
- Fixed service metadata clearing; category/unit use supported editable fields. Prices remain separate proposals requiring future effective date, reason and independent decision notes.
- Completed automatic payment status polling, explicit late-status retry and confirmed official receipt navigation. Pending/reference submission never creates a paid receipt.
- Completed private cash evidence attachment upload/download, immutable attachment storage and honest separate bank-deposit status. Closing the dialog refreshes authoritative cash collection totals; attachment retry reuses the evidence record.
- Completed independent tariff approve/reject and alert assignment/review/resolution controls with notes. Resolution never changes payment/reconciliation evidence.
- Fixed persisted delivery/history display and official receipt navigation in Department Desk.
- Replaced the live demo notification badge with scoped unread-count data and a read-only inbox/read action. Unsupported notification preferences remain disabled.
- Added meaningful mobile account/filter labels; retained responsive layout and current-page semantics. Updated asset cache versions and synchronized the Django-served HTML shell.

## Legacy route analysis

Baseline: 91 tests, 23 errors. These were 23 failing test/subtest invocations, not 23 distinct missing names. The first reported missing names were `staff-list`, `department-list`, `billing-correction`, `tariff-create`, `management-dashboard`, `invoice-create`, `patient-list`, `patient-edit`, `notification-list`, `invoice-pay`, `dashboard`, `patient-create`, and `login`. Repeated management-dashboard role subtests accounted for several errors; some tests stopped at their first missing name. All 23 test/subtest-to-name mappings are retained in `phase-j-evidence/legacy-failure-inventory.txt`.

The earlier static frontend migration explicitly archived the old Django screens under `docs/paypoint/legacy-django-ui/`. Re-enabling old financial POST forms would restore obsolete behavior, including the old tariff creation assumption. Instead:

- Supported page bookmarks redirect to the matching current fragment after authentication and role checks.
- Object-specific retired HTML detail/print routes return 410 to authenticated authorized users, rather than silently selecting the wrong patient/invoice/payment.
- Obsolete non-GET/HEAD submissions return 410; CSRF middleware remains active. No legacy submission creates a financial record.
- Anonymous protected bookmarks redirect to login; role-disallowed requests return 403. Public login/reset bookmarks redirect only to their current public forms.
- Tests now exercise current API business behavior, not archived HTML rendering. No test was skipped/disabled and no permission/authentication bypass was introduced.

The compatibility inventory follows. Protected routes retain the role allowlists in `backend/apps/common/legacy_urls.py`; “redirect” below does not mean public access.

| URL name | Historical path | GET/HEAD disposition |
|---|---|---|
| `login` | `/login/` | /paypoint/ |
| `password_reset` | `/password-reset/` | /paypoint/#forgot-password |
| `dashboard` | `/` | /paypoint/#dashboard |
| `management-dashboard` | `/management/` | /paypoint/#dashboard-overview-preview |
| `patient-list` | `/patients/` | /paypoint/#patient-directory |
| `patient-create` | `/patients/new/` | /paypoint/#patient-registration |
| `patient-detail` | `/patients/<uuid:pk>/` | 410; object-specific legacy screen retired |
| `patient-edit` | `/patients/<uuid:pk>/edit/` | 410; object-specific legacy screen retired |
| `invoice-list` | `/invoices/` | /paypoint/#billing |
| `invoice-create` | `/invoices/new/` | /paypoint/#billing-create |
| `invoice-detail` | `/invoices/<uuid:pk>/` | 410; object-specific legacy screen retired |
| `invoice-print` | `/invoices/<uuid:pk>/print/` | 410; object-specific legacy screen retired |
| `invoice-pay` | `/invoices/<uuid:pk>/pay/` | 410; object-specific legacy screen retired |
| `billing-correction` | `/invoices/<uuid:pk>/correct/` | 410; object-specific legacy screen retired |
| `payment-detail` | `/payments/<uuid:pk>/` | 410; object-specific legacy screen retired |
| `receipt-print` | `/receipts/<uuid:pk>/print/` | 410; object-specific legacy screen retired |
| `department-list` | `/departments/` | /paypoint/#admin-departments |
| `department-detail` | `/departments/<uuid:pk>/` | 410; object-specific legacy screen retired |
| `department-create` | `/departments/new/` | /paypoint/#admin-departments |
| `service-list` | `/services/` | /paypoint/#admin-services |
| `service-detail` | `/services/<uuid:pk>/` | 410; object-specific legacy screen retired |
| `service-create` | `/services/new/` | /paypoint/#admin-services |
| `tariff-list` | `/tariffs/` | /paypoint/#admin-tariffs |
| `tariff-create` | `/tariffs/new/` | /paypoint/#admin-services |
| `profile` | `/profile/` | /paypoint/#profile |
| `password_change` | `/password-change/` | /paypoint/#change-password |
| `staff-list` | `/staff/` | /paypoint/#users-audit |
| `finance-workspace` | `/finance/` | /paypoint/#finance |
| `audit-log` | `/audit/` | /paypoint/#admin-audit |
| `notification-list` | `/notifications/` | /paypoint/#notifications |
| `notification-detail` | `/notifications/<int:pk>/` | 410; object-specific legacy screen retired |
| `notification-read` | `/notifications/<int:pk>/read/` | 410; object-specific legacy screen retired |
| `reconciliation-import` | `/reconciliation/import/` | /paypoint/#finance-reconciliation |
| `reconciliation-detail` | `/reconciliation/<uuid:pk>/` | 410; object-specific legacy screen retired |

## Financial workflows A–H

New `apps.common.test_phase_j_workflows.PhaseJFinancialWorkflows` executes seven PostgreSQL tests; B and D share one sequence.

| Workflow | Executed assertion |
|---|---|
| A | Authorized patient lookup → approved tariff → server-priced invoice → pending intent; no receipt while pending. |
| B | HMAC-signed deterministic adapter event → confirmed payment → official paid receipt → department eligibility check → one delivery. Browser repeated this sequence on disposable data. |
| C | Repeated identical API intent returns the same payment; duplicate signed event reports unprocessed; one receipt only. |
| D | Second delivery attempt returns 400; one delivery row. Concurrent browser-independent test also asserts 201/400. |
| E | Finance cannot approve own proposal; independent administrator approval creates future version; advancing the clock changes effective price while the historical invoice remains unchanged. Browser approved one proposal and rejected another with notes. |
| F | Cashier request → independent Finance decision using a clearly marked synthetic policy → confirmed-cash evidence. `bank_settled` remains null; authorization/collection/deposit remain separate. Browser tested upload/download and self-decision rejection. |
| G | Synthetic unmatched reconciliation row → detector-generated alert → assignment → review → documented resolution. Underlying reconciliation item remains unmatched. |
| H | Administrator creates synthetic user/role → authorized login → audit entry; password absent from audit. Browser also created a passwordless user and verified restricted access as Finance. |

Deterministic confirmation is **not live banking certification**. Cash confirmation fixtures are test evidence injection, not an enabled manual cash-confirmation workflow.

## Executed checks and exact commands

Commands ran from `/Users/mac/Documents/imsuth/backend` unless noted. PostgreSQL test commands used this disposable local connection prefix (no password):

```sh
DATABASE_URL=postgresql://revenue_test@127.0.0.1:55439/revenue_control
```

The prefix was set on each command, not exported to a production environment.

| Command after the DATABASE_URL prefix | Final observed result |
|---|---|
| `.venv/bin/python manage.py test --settings=config.settings_test --noinput` | 103 tests in 61.445s; OK; zero failures/errors/skips. |
| `.venv/bin/python manage.py test apps.common.test_revenue_api apps.common.test_staging_readiness apps.common.test_phase_j_workflows apps.common.test_phase_j_security apps.payments apps.billing apps.operations --settings=config.settings_test --noinput` | 54 tests in 18.496s; OK; zero failures/errors/skips. |
| `.venv/bin/python manage.py test apps.common.test_revenue_concurrency apps.common.test_staging_readiness.PostgreSQLPaymentConcurrencyTests --settings=config.settings_test --noinput` | 3 tests in 3.803s; OK; zero failures/errors/skips. |
| `.venv/bin/python manage.py check --settings=config.settings_test` | No issues, zero silenced. |
| `.venv/bin/python manage.py makemigrations --check --dry-run --settings=config.settings_test` | No changes detected. |
| `.venv/bin/python manage.py collectstatic --noinput --settings=config.settings_test` | Completed; final copied/unmodified counts recorded in phase-j-evidence/verification-results.txt. |
| `.venv/bin/python manage.py spectacular --settings=config.settings_test --file /tmp/phase-j-openapi.yaml --validate` | Zero schema errors; 21 warnings, 13 unique. |

From `/Users/mac/Documents/imsuth`:

```sh
node --input-type=module --check < website/paypoint/static/paypoint/frontend.js
node --input-type=module --check < website/paypoint/static/paypoint/revenue-live.js
node --input-type=module --check < website/paypoint/static/paypoint/api.js
git diff --check
```

All exited successfully. These are syntax checks using the installed runtime, not introduction of a Node frontend stack.

Browser UAT used a separate migrated/seeded `phase_j_uat` database and `manage.py runserver 127.0.0.1:8012 --settings=config.settings_test`. No production credentials were used. The browser viewport override was reset after testing. Screenshots, measured widths, keyboard focus results and sanitized command summaries are retained in `phase-j-evidence/`.

An intermediate final-suite run failed one markup assertion because the synchronized shell spelled `demoMode: false` with a space while the test expected `demoMode:false`. The shell was normalized; the test was not weakened. The final run above passed. Initial standalone workflow C also exposed the actual idempotency serializer defect, which was fixed and retested. Tool timing/locator errors during asynchronous browser rendering are documented separately from application failures.

## Security and performance evidence

- Authenticated seven-role API matrix and scoped department/patient/receipt access run on PostgreSQL. Anonymous groups and unauthorized writers are rejected.
- Real session requests without CSRF are rejected. Browser forms use same-origin sessions and the common CSRF client.
- Evidence uploads reject non-PDF/image content and files over 2MB, validate image decoding/dimensions and re-encode images. Downloads require an authorized writer, force attachment/octet-stream and use nosniff/private-no-store. Existing attachment replacement is rejected.
- Audit tests check credentials/codes are not included; browser-fixture persistence check also found no synthetic login password in audit metadata. Browser storage source audit found only display/navigation preferences and opt-in remembered username, no patient/payment/token/password storage.
- Pending attempts do not increase confirmed collections. Cash authorization does not count as a collection; evidence and bank deposit remain separate.
- A bounded-query regression compares 1-row and 25-row transaction pages: the larger page may use at most one extra query, avoiding N+1 service/receipt lookups. Tests also assert stable non-overlapping pages, server search/empty results, invalid status/search rejection and department isolation.
- Three PostgreSQL race tests cover identical intent creation, duplicate service delivery and competing daily-limit cash reservations. Each asserts one accepted financial/delivery result, not duplicate records.
- Test-mode evidence remains explicitly gated. Live adapter/notification preferences were not enabled. The served Django shell has demo mode false; the separate static demonstration remains explicitly configured as demonstration.
- No production-scale throughput benchmark, live penetration test or full accessibility certification is implied.

## Remaining issues and acceptance dependencies

| Class | Remaining item | Impact / next acceptance evidence |
|---|---|---|
| UI mismatch | Independent original HTML and approved crest not uniquely verified; current outer PayPoint shell differs from the newer screenshot's single header | Hospital must identify an immutable baseline or approve current layout/assets. No pixel-perfect claim. |
| Code defect (documentation quality) | OpenAPI generation has 21 warnings: ambiguous custom path types, status enum naming and operation-ID collisions across aliases | Schema validates with zero errors; improve explicit annotations/names before generated-client certification. |
| Code defect (scale limitation) | Some secondary catalogues, recent-five lists and the cash evidence picker still load bounded first pages/all catalogue pages; only the requested main transaction/department lists were converted to server paging | Large-scale acceptance should measure these paths; verified-cash picker currently exposes the first 100 matching payments. |
| Missing hospital policy | Actual cash limits/approval authority, offline verification, insurance/exemption tariffs, retention and close-of-day rules | Synthetic policy values grant no production authority. Unsupported pricing/confirmation controls remain unavailable. |
| External integration dependency | Provider/bank confirmation, settlement/deposit certification and production notification delivery contracts | Signed local test evidence is not live provider certification; deposit stays uncertified. |
| Infrastructure/deployment dependency | Approved hosting/proxy/TLS, production PostgreSQL/Redis/workers, backups/restore, secrets and monitoring acceptance | Local checks do not certify production readiness; no deployment performed. |
| Hardware testing dependency | Hospital devices/browsers, printers, QR readers and network conditions | Browser-width emulation and receipt HTML are not physical print/device certification. |

Local implementation and the eight-screen interaction requirement are fulfilled within the executed coverage. Hospital acceptance remains conditional on the reference and external dependencies above; Phase J must not be represented as production approval.
