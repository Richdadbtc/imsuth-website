# Live UI connections — 25 October 2026

The frontend remains HTML5, CSS3 and vanilla ES6 JavaScript. Demo responders, fabricated users, sample financial rows and fixed dashboard totals have been removed from the active UI. Pages read authenticated API responses and display real empty, loading and error states. Existing database records were preserved.

## Connected workflows

| UI | Backend integration |
| --- | --- |
| Overview and eight Revenue Control tabs | Session, capabilities, dashboard summaries, department/service catalogues, payment intents, receipt verification, service delivery, cash points/orders, alerts, users and audit APIs |
| Patients and billing | Patient registration/edit/search; invoice creation with server tariffs, invoice details and correction requests |
| Payments and receipts | Invoice lookup, pending payment creation/status refresh, receipt lookup, official A4/thermal print and audited reprint |
| Refunds, reversals and approvals | Requests, approval queue, history and authorized decisions; financial execution remains server controlled |
| Reconciliation | Statement upload/rows, scoped discrepancies and resolution requests |
| Reports | Server summaries, groups, paginated records, date filters, CSV export and print |
| Staff and roles | Staff CRUD, phone persistence, permitted financial role choices and permission groups with server validation |
| Services, tariffs and departments | Live catalogues, tariff/service names, service maintenance and department edit |
| Notifications | In-app notification composition, recipients, editing and publishing |
| Settings and profile | Hospital/receipt/preferences configuration, profile/details/photo, password and account endpoints |
| Help and support | Tickets, replies, status and authorized attachment upload/download |

Financial roles remain distinct from permission groups. User-entered payment dates and remarks are metadata only and cannot confirm payment. Receipt verification and reprints enforce department scope. Profile photo operations cannot remove private cash evidence.

## Local startup

Run Django from `backend/`:

```sh
.venv/bin/python manage.py migrate
.venv/bin/python manage.py runserver 127.0.0.1:8012
```

In a second terminal, from the project root:

```sh
backend/.venv/bin/python backend/dev_proxy.py
```

Open http://127.0.0.1:5500/website/paypoint/index.html. The local-only server forwards API requests to Django on port 8012, preserving same-origin session cookies and CSRF validation. A plain static file server cannot provide these APIs. The alternative Django entry point is http://127.0.0.1:8012/paypoint/.

## Verification

- Full PostgreSQL regression: **111 tests passed**, no failures/errors/skips.
- Django system checks and migration drift check passed.
- Four active JavaScript modules passed syntax checks; whitespace checks passed.
- OpenAPI validation: zero errors, 23 warnings (14 unique); warnings remain to be resolved separately.
- Browser checks covered 18 routes with no displayed API errors. Executed synthetic workflows verified staff phone/profile/settings persistence, a permission group, support ticket, patient registration, server-priced invoice, pending payment, refund request, department edit and CSV export.
- Browser financial records were created only in the separate synthetic UAT database. No real payment provider, settlement or bank transaction was executed.
- The original port 5500 entry point visibly opens login and its session endpoint responds successfully.

See `live-ui-evidence/browser-route-checks.json`, `login.png` and `channel-report.png`. Browser checks do not certify every role/action combination or physical printing device.

## Configuration still required

External payment providers, SMS/email delivery, QR sign-in, two-factor authentication, backup operations and hospital-specific insurance pricing require their corresponding integrations/configuration. The UI states unavailable capabilities truthfully instead of pretending they succeeded. Credentials and recovery codes are never returned as UI demo data. Production deployment was not performed, and these changes were not pushed to GitHub.

Migration: `payments/0003_reported_payment_details.py`. No existing operational records were deleted.
