# Revenue Control endpoint reference — 24 October 2026

The existing `/api/v1/` prefix is preserved. `/paypoint/api/v1/` is a second application route with the same implementation, not a second ledger. Set a reverse-proxy script prefix only once; do not combine a stripped `/paypoint` mount with an additional unstripped duplicate prefix. No proxy configuration was changed.

Live schema: `/api/schema/`; Swagger: `/api/docs/`. The validated schema includes exact request/response fields, requiredness, numeric precision and enum values. Existing `/staff/`, `/audit-events/`, `/tariffs/` and `/dashboard/` remain compatible resources. Existing `roles` is Django Groups; `/users/role_choices/` returns the seven authoritative User.Role values.

## Shared contract

- Same-origin session cookies and CSRF token required for authenticated mutations. `GET session/` obtains CSRF cookie. No access tokens in localStorage.
- Lists use `count`, `next`, `previous`, `results`; page size is 25. `page` selects pages. Search uses `search`; declared filter fields are validated. `ordering` is supported by DRF's ordering filter.
- Revenue resource dates: `period=today|yesterday|7|30|all|custom`, optional ISO `date_from` / `date_to`, inclusive Lagos calendar dates. Reversed ranges return 400.
- Read 200, create 201, authenticated denial 403, out-of-scope/absent object 404, validation or conflicting state 400, unsupported method 405. Browser permission errors disclose no financial details. Unconfigured authoritative provider verification returns 503 and does not confirm anything.
- Validation envelope: `{"detail":"Please check the submitted fields.","errors":{"field":["message"]},"status":400}`. Existing error details remain present.
- Payment and cash-order mutations require idempotency keys; invoice keys are supported for compatibility and supplied by the UI. Repeating an identical request returns the original object; changed actor/domain payload is rejected. A concurrent conflicting request may return 400 and can be retried with the same key. Delivery is once per InvoiceItem; repeated delivery returns 400.

## Financial metric definitions

Dashboard verified collections: sum of NGN Payment.amount where current status is confirmed and confirmed_at falls in the period. Attempts, failed and pending metrics use created_at. Pending includes pending, awaiting_offline_verification and review_required; it is never collected revenue. Refund/reversal pending and completed states are excluded from current confirmed collections. This is not a historical net-cash ledger, and not a bank settlement metric. Department analytics explicitly use attempts created in the period and their current state. Confirmed cash-point collections require explicit CashCollectionEvidence; authorization orders are not collection evidence. Deposit/settlement is unknown until an independently verified settlement workflow supplies it.

Invoice totals and immutable line snapshots come from approved effective tariffs on the server. A submitted reference is untrusted evidence only. Only the existing authoritative confirmation service issues paid receipts. Unknown NHIS/IMSHIA pricing is rejected rather than discounted. A fully paid invoice and currently confirmed receipt are required for service delivery, with refund/reversal restrictions.

## Endpoint inventory

The table is generated from the schema. `Action-specific object` endpoints use the bodies in the workflow examples below. Some schema action request bodies inherit a model serializer; those action bodies are explicitly clarified below. All listed resources exist; partial and blocked business integrations are separately recorded in API-INTEGRATION-REPORT.md.

| Endpoint | Purpose / operation | Permission | Query/path parameters | JSON body schema | Documented success |
|---|---|---|---|---|---|
| `GET /paypoint/api/v1/alerts/` | paypoint api v1 alerts list | Authenticated; department-scoped | alert_type, assigned_to, department, ordering, page, search, severity, status | None | 200 |
| `GET /paypoint/api/v1/alerts/{id}/` | paypoint api v1 alerts retrieve | Authenticated; department-scoped | id | None | 200 |
| `POST /paypoint/api/v1/alerts/{id}/assign/` | paypoint api v1 alerts assign create | Finance / management / super administrator; independent decisions | id | Alert | 200 |
| `POST /paypoint/api/v1/alerts/{id}/resolve/` | paypoint api v1 alerts resolve create | Finance / management / super administrator; independent decisions | id | Alert | 200 |
| `POST /paypoint/api/v1/alerts/{id}/start-review/` | paypoint api v1 alerts start review create | Finance / management / super administrator; independent decisions | id | Alert | 200 |
| `GET /paypoint/api/v1/alerts/analytics/` | paypoint api v1 alerts analytics retrieve | Authenticated; department-scoped | None | None | 200 |
| `GET /paypoint/api/v1/alerts/assignees/` | paypoint api v1 alerts assignees retrieve | Authenticated; department-scoped | None | None | 200 |
| `GET /paypoint/api/v1/alerts/summary/` | paypoint api v1 alerts summary retrieve | Authenticated; department-scoped | None | None | 200 |
| `GET /paypoint/api/v1/audit-logs/` | paypoint api v1 audit logs list | Super administrator / finance / management / auditor; read only | action, actor, object_type, ordering, page, search | None | 200 |
| `GET /paypoint/api/v1/audit-logs/{id}/` | paypoint api v1 audit logs retrieve | Super administrator / finance / management / auditor; read only | id | None | 200 |
| `GET /paypoint/api/v1/audit-logs/summary/` | paypoint api v1 audit logs summary retrieve | Super administrator / finance / management / auditor; read only | None | None | 200 |
| `GET /paypoint/api/v1/cash-orders/` | paypoint api v1 cash orders list | Authenticated; department-scoped | cash_point, ordering, page, requested_by, search, status | None | 200 |
| `POST /paypoint/api/v1/cash-orders/` | paypoint api v1 cash orders create | Cashier or financial writer for requests; independent approver with configured limit for approval | None | CashOrder | 201 |
| `GET /paypoint/api/v1/cash-orders/{id}/` | paypoint api v1 cash orders retrieve | Authenticated; department-scoped | id | None | 200 |
| `POST /paypoint/api/v1/cash-orders/{id}/approve/` | paypoint api v1 cash orders approve create | Cashier or financial writer for requests; independent approver with configured limit for approval | id | CashOrder | 200 |
| `POST /paypoint/api/v1/cash-orders/{id}/reject/` | paypoint api v1 cash orders reject create | Cashier or financial writer for requests; independent approver with configured limit for approval | id | CashOrder | 200 |
| `GET /paypoint/api/v1/cash-orders/approval-limits/` | paypoint api v1 cash orders approval limits retrieve | Authenticated; department-scoped | None | None | 200 |
| `GET /paypoint/api/v1/cash-points/` | paypoint api v1 cash points list | Authenticated; department-scoped | assigned_officer, department, is_active, ordering, page, search | None | 200 |
| `POST /paypoint/api/v1/cash-points/` | paypoint api v1 cash points create | Finance / management / super administrator | None | CashPoint | 201 |
| `GET /paypoint/api/v1/cash-points/{id}/` | paypoint api v1 cash points retrieve | Authenticated; department-scoped | id | None | 200 |
| `PATCH /paypoint/api/v1/cash-points/{id}/` | paypoint api v1 cash points partial update | Finance / management / super administrator | id | PatchedCashPoint | 200 |
| `GET /paypoint/api/v1/cash-points/{id}/collections/` | paypoint api v1 cash points collections retrieve | Authenticated; department-scoped | id | None | 200 |
| `POST /paypoint/api/v1/cash-points/{id}/collections/` | paypoint api v1 cash points collections create | Finance / management / super administrator | id | CashPoint | 200 |
| `GET /paypoint/api/v1/cash-points/{id}/summary/` | paypoint api v1 cash points summary retrieve | Authenticated; department-scoped | id | None | 200 |
| `GET /paypoint/api/v1/cash-points/officers/` | paypoint api v1 cash points officers retrieve | Authenticated; department-scoped | None | None | 200 |
| `GET /paypoint/api/v1/dashboard/` | paypoint api v1 dashboard retrieve | Authenticated; department-scoped | None | None | 200 |
| `GET /paypoint/api/v1/dashboard/{metric}/` | paypoint api v1 dashboard retrieve 2 | Authenticated; department-scoped | metric | None | 200 |
| `GET /paypoint/api/v1/department-desk/activity/` | paypoint api v1 department desk activity retrieve | Authenticated; department-scoped | None | None | 200 |
| `GET /paypoint/api/v1/department-desk/receipts/` | paypoint api v1 department desk receipts retrieve | Authenticated; department-scoped | None | None | 200 |
| `GET /paypoint/api/v1/department-desk/receipts/{reference}/` | paypoint api v1 department desk receipts retrieve 2 | Authenticated; department-scoped | reference | None | 200 |
| `POST /paypoint/api/v1/department-desk/receipts/{reference}/verify/` | paypoint api v1 department desk receipts verify create | Department supervisor / finance / super administrator for delivery; scoped receipt checks | reference | Receipt | 200 |
| `POST /paypoint/api/v1/department-desk/service-items/{item_id}/deliver/` | paypoint api v1 department desk service items deliver create | Department supervisor / finance / super administrator for delivery; scoped receipt checks | item_id | Receipt | 200 |
| `GET /paypoint/api/v1/department-desk/services/pending/` | paypoint api v1 department desk services pending retrieve | Authenticated; department-scoped | None | None | 200 |
| `GET /paypoint/api/v1/department-desk/summary/` | paypoint api v1 department desk summary retrieve | Authenticated; department-scoped | None | None | 200 |
| `GET /paypoint/api/v1/departments/` | paypoint api v1 departments list | Authenticated; department-scoped | is_active, ordering, page, search | None | 200 |
| `POST /paypoint/api/v1/departments/` | paypoint api v1 departments create | Authenticated; department-scoped | None | Department | 201 |
| `GET /paypoint/api/v1/departments/{id}/` | paypoint api v1 departments retrieve | Authenticated; department-scoped | id | None | 200 |
| `PATCH /paypoint/api/v1/departments/{id}/` | paypoint api v1 departments partial update | Authenticated; department-scoped | id | PatchedDepartment | 200 |
| `GET /paypoint/api/v1/departments/{id}/collections/` | paypoint api v1 departments collections retrieve | Authenticated; department-scoped | id | None | 200 |
| `GET /paypoint/api/v1/departments/{id}/services/` | paypoint api v1 departments services retrieve | Authenticated; department-scoped | id | None | 200 |
| `GET /paypoint/api/v1/departments/{id}/staff/` | paypoint api v1 departments staff retrieve | Authenticated; department-scoped | id | None | 200 |
| `GET /paypoint/api/v1/departments/{id}/summary/` | paypoint api v1 departments summary retrieve | Authenticated; department-scoped | id | None | 200 |
| `GET /paypoint/api/v1/departments/{id}/transactions/` | paypoint api v1 departments transactions retrieve | Authenticated; department-scoped | id | None | 200 |
| `GET /paypoint/api/v1/departments/{id}/trends/` | paypoint api v1 departments trends retrieve | Authenticated; department-scoped | id | None | 200 |
| `GET /paypoint/api/v1/departments/analytics/` | paypoint api v1 departments analytics retrieve | Authenticated; department-scoped | None | None | 200 |
| `GET /paypoint/api/v1/invoices/` | paypoint api v1 invoices list | Authenticated; department-scoped | currency, department, ordering, page, patient, search, status | None | 200 |
| `POST /paypoint/api/v1/invoices/` | paypoint api v1 invoices create | Front desk / cashier / finance; assigned department required | None | Invoice | 201 |
| `GET /paypoint/api/v1/invoices/{id}/` | paypoint api v1 invoices retrieve | Authenticated; department-scoped | id | None | 200 |
| `GET /paypoint/api/v1/invoices/{id}/balance/` | paypoint api v1 invoices balance retrieve | Authenticated; department-scoped | id | None | 200 |
| `GET /paypoint/api/v1/patients/` | paypoint api v1 patients list | Authenticated; department-scoped | ordering, page, search, sex, status | None | 200 |
| `POST /paypoint/api/v1/patients/` | paypoint api v1 patients create | Authenticated; department-scoped | None | Patient | 201 |
| `GET /paypoint/api/v1/patients/{id}/` | paypoint api v1 patients retrieve | Authenticated; department-scoped | id | None | 200 |
| `PATCH /paypoint/api/v1/patients/{id}/` | paypoint api v1 patients partial update | Authenticated; department-scoped | id | PatchedPatient | 200 |
| `GET /paypoint/api/v1/patients/search/` | paypoint api v1 patients search retrieve | Authenticated; department-scoped | None | None | 200 |
| `GET /paypoint/api/v1/payments/` | paypoint api v1 payments list | Authenticated; department-scoped | channel, currency, ordering, page, provider, search, status | None | 200 |
| `POST /paypoint/api/v1/payments/` | paypoint api v1 payments create | Cashier / finance; assigned department required | None | Payment | 201 |
| `GET /paypoint/api/v1/payments/{id}/` | paypoint api v1 payments retrieve | Authenticated; department-scoped | id | None | 200 |
| `POST /paypoint/api/v1/payments/{id}/retry/` | paypoint api v1 payments retry create | Cashier / finance; assigned department required | id | Payment | 200 |
| `GET /paypoint/api/v1/payments/{id}/verification-status/` | paypoint api v1 payments verification status retrieve | Authenticated; department-scoped | id | None | 200 |
| `POST /paypoint/api/v1/payments/{id}/verify/` | paypoint api v1 payments verify create | Cashier / finance; assigned department required | id | Payment | 200 |
| `POST /paypoint/api/v1/payments/test-webhook/` | paypoint api v1 payments test webhook create | Cashier / finance; assigned department required | None | TestWebhook | 200 |
| `GET /paypoint/api/v1/receipts/` | paypoint api v1 receipts list | Authenticated; department-scoped | invoice, ordering, page, payment, search | None | 200 |
| `GET /paypoint/api/v1/receipts/{id}/` | paypoint api v1 receipts retrieve | Authenticated; department-scoped | id | None | 200 |
| `GET /paypoint/api/v1/receipts/{id}/print/` | paypoint api v1 receipts print retrieve | Authenticated; department-scoped | id | None | 200 |
| `POST /paypoint/api/v1/receipts/verify/` | paypoint api v1 receipts verify create | Authenticated; department-scoped | None | Action-specific object | 200 |
| `GET /paypoint/api/v1/roles/` | paypoint api v1 roles list | Super administrator; Django superuser required to assign super_admin | ordering, page, search | None | 200 |
| `POST /paypoint/api/v1/roles/` | paypoint api v1 roles create | Super administrator; Django superuser required to assign super_admin | None | Role | 201 |
| `GET /paypoint/api/v1/roles/{id}/` | paypoint api v1 roles retrieve | Super administrator; Django superuser required to assign super_admin | id | None | 200 |
| `PATCH /paypoint/api/v1/roles/{id}/` | paypoint api v1 roles partial update | Super administrator; Django superuser required to assign super_admin | id | PatchedRole | 200 |
| `DELETE /paypoint/api/v1/roles/{id}/` | paypoint api v1 roles destroy | Super administrator; Django superuser required to assign super_admin | id | Action-specific object | 204 |
| `POST /paypoint/api/v1/roles/{id}/assign/` | paypoint api v1 roles assign create | Super administrator; Django superuser required to assign super_admin | id | Role | 200 |
| `GET /paypoint/api/v1/services/` | paypoint api v1 services list | Authenticated; department-scoped | department, is_active, ordering, page, search | None | 200 |
| `POST /paypoint/api/v1/services/` | paypoint api v1 services create | Authenticated; department-scoped | None | Service | 201 |
| `GET /paypoint/api/v1/services/{id}/` | paypoint api v1 services retrieve | Authenticated; department-scoped | id | None | 200 |
| `PATCH /paypoint/api/v1/services/{id}/` | paypoint api v1 services partial update | Authenticated; department-scoped | id | PatchedService | 200 |
| `GET /paypoint/api/v1/services/{id}/tariff/` | paypoint api v1 services tariff retrieve | Authenticated; department-scoped | id | None | 200 |
| `POST /paypoint/api/v1/services/{id}/tariff-proposals/` | paypoint api v1 services tariff proposals create | Authenticated; department-scoped | id | Service | 200 |
| `GET /paypoint/api/v1/services/{id}/tariffs/` | paypoint api v1 services tariffs retrieve | Authenticated; department-scoped | id | None | 200 |
| `GET /paypoint/api/v1/services/categories/` | paypoint api v1 services categories retrieve | Authenticated; department-scoped | None | None | 200 |
| `GET /paypoint/api/v1/services/price-history/` | paypoint api v1 services price history retrieve | Authenticated; department-scoped | None | None | 200 |
| `GET /paypoint/api/v1/tariff-proposals/` | paypoint api v1 tariff proposals list | Authenticated; department-scoped | ordering, page, search | None | 200 |
| `GET /paypoint/api/v1/tariff-proposals/{id}/` | paypoint api v1 tariff proposals retrieve | Authenticated; department-scoped | id | None | 200 |
| `POST /paypoint/api/v1/tariff-proposals/{id}/approve/` | paypoint api v1 tariff proposals approve create | Finance / management / super administrator; independent decisions | id | TariffProposal | 200 |
| `POST /paypoint/api/v1/tariff-proposals/{id}/reject/` | paypoint api v1 tariff proposals reject create | Finance / management / super administrator; independent decisions | id | TariffProposal | 200 |
| `GET /paypoint/api/v1/users/` | paypoint api v1 users list | Super administrator; Django superuser required to assign super_admin | department, is_active, ordering, page, role, search | None | 200 |
| `POST /paypoint/api/v1/users/` | paypoint api v1 users create | Super administrator; Django superuser required to assign super_admin | None | Staff | 201 |
| `GET /paypoint/api/v1/users/{id}/` | paypoint api v1 users retrieve | Super administrator; Django superuser required to assign super_admin | id | None | 200 |
| `PATCH /paypoint/api/v1/users/{id}/` | paypoint api v1 users partial update | Super administrator; Django superuser required to assign super_admin | id | PatchedStaff | 200 |
| `POST /paypoint/api/v1/users/{id}/activate/` | paypoint api v1 users activate create | Super administrator; Django superuser required to assign super_admin | id | Staff | 200 |
| `POST /paypoint/api/v1/users/{id}/deactivate/` | paypoint api v1 users deactivate create | Super administrator; Django superuser required to assign super_admin | id | Staff | 200 |
| `GET /paypoint/api/v1/users/{id}/permissions/` | paypoint api v1 users permissions retrieve | Super administrator; Django superuser required to assign super_admin | id | None | 200 |
| `GET /paypoint/api/v1/users/role_choices/` | paypoint api v1 users role choices retrieve | Super administrator; Django superuser required to assign super_admin | None | None | 200 |

## Workflow request and response examples

All examples are synthetic. UUIDs are placeholders returned by earlier API calls; no record IDs, policy amounts or credentials are supplied as defaults.

- `POST invoices/`: `{"patient":"<uuid>","department":"<uuid>","items":[{"service":"<uuid>","quantity":1}],"idempotency_key":"<unique-key>"}` → invoice includes `id`, `total_amount`, `amount_paid`, `outstanding_balance`, immutable `line_items`.
- `POST payments/`: `{"invoice":"<uuid>","channel":"pos","submitted_reference":"<unverified-reference>","idempotency_key":"<unique-key>"}` → payment includes generated reference, server amount and `awaiting_offline_verification`. `POST payments/{id}/verify/` has `{}` body and returns 503 until a trusted verification adapter is configured. `GET .../verification-status/` returns id/status/confirmed_at.
- `GET services/{id}/tariff/?patient_category=self_pay` → approved current tariff amount/currency/effective dates. Unconfigured categories return 400. `POST services/{id}/tariff-proposals/`: `{"amount":"<approved-proposal-amount>","effective_from":"<future-ISO-datetime>","reason":"<business-reason>"}`. Independent approve/reject body: `{"notes":"<review-evidence>"}`. Approval creates a new TariffVersion, never updates invoice snapshots.
- `POST department-desk/receipts/{reference}/verify/`: `{}` → `eligible_for_delivery`, payment status, authorized patient and item quantities/delivery flags. This checks a receipt and does not confirm a pending payment.
- `POST department-desk/service-items/{id}/deliver/`: `{"receipt":"<uuid>","notes":"<permitted-service-notes>"}` → immutable delivery id, item, receipt, responsible staff and timestamp. Duplicate returns 400.
- `POST cash-points/`: `{"name":"<name>","location":"<location>","department":"<uuid>","assigned_officer":123,"daily_limit":"<approved-amount>","is_active":true}`. Officer must be active and assigned to that department. `GET cash-points/officers/` returns permitted assignment options. `POST cash-points/{id}/collections/`: `{"payment":"<confirmed-cash-payment-uuid>","evidence_reference":"<cash-ledger-proof>"}` → evidence id; never changes payment verification or bank settlement.
- `POST cash-orders/`: `{"cash_point":"<uuid>","amount":"<requested-amount>","purpose":"<purpose>","description":"<details>","idempotency_key":"<unique-key>"}` → pending order with server requester. Independent approve/reject: `{"notes":"<review-evidence>"}`. Policy limits have no defaults and are configured by authorized management through Django Admin with a policy reference.
- `GET alerts/`: paginated read-only records. `POST alerts/{id}/assign/`: `{"assigned_to":123}`; choices from `GET alerts/assignees/`. `POST .../start-review/`: `{}`. `POST .../resolve/`: `{"notes":"<resolution-evidence>"}`. Response contains lifecycle timestamps and staff identifiers; no payment mutation occurs. Resolved alerts cannot silently reopen.
- `POST users/`: `{"username":"<username>","first_name":"<name>","last_name":"<name>","email":"<staff-email>","role":"cashier","department":"<uuid>"}` → safe staff record without password material. Without an initial password the account has an unusable password pending secure recovery. PATCH permits authorized staff fields; activate/deactivate use `{}`. Permissions is read-only. Existing role enum is retained.
- `GET audit-logs/`: paginated immutable events. Summary returns `total`, `unique_users`, and per-action counts. No create, update or delete API exists. Passwords, tokens and verification codes must never be passed as audit notes.
- `GET dashboard/summary/`: e.g. `{"currency":"NGN","verified_collections":"0.00","transactions":0,"verified_transactions":0,"pending_transactions":0,"pending_amount":"0.00","active_departments":0,"note":"..."}`. Zero examples illustrate empty authorized data, not supplied financial balances.
- `GET receipts/{id}/print/` returns an authorized HTML paid receipt and audits print-view access. Physical printing is not verified. Existing audited reprint workflow remains at `/receipt-reprints/`.

## Related screens and tests

Dashboard → dashboard resources; Record Payment → patients/catalogue/invoices/payments/receipts; Department Desk → department-desk; Departments → nested departments and analytics; Services and Prices → services/tariffs/proposals; Cash Points and Orders → cash resources; Alerts → alerts; Users and Audit → users/role choices/audit logs.

Coverage: `apps.common.test_revenue_api`, `test_revenue_concurrency`, `test_ui_api`, `test_static_frontend_api`, existing payment lifecycle tests and PostgreSQL payment concurrency. Refer to the integration report for actual runs and limits; schema generation is not browser verification.

## Phase J additions and compatibility

All current versioned paths remain available. The following are additive:

- `POST /api/v1/invoices/{id}/corrections/`: reason and requested_change create an audited pending correction request; issued invoice snapshots are not changed.
- `GET /api/v1/inbox/unread-count/`: scoped authenticated unread count.
- `GET|POST /api/v1/cash-points/{id}/collections/{evidence_id}/attachment/`: authorized private evidence download or one immutable PDF/PNG/JPG attachment up to 2MB. Does not certify a deposit.
- `GET /api/v1/dashboard/recent-transactions/`: bounded `page`, `page_size` (maximum 100), `search`, `status` and period/date filtering. Includes service summary and official receipt identifiers where issued.
- Department list supports server search/status filtering and collection/transaction/pending ordering; analytics uses the same scope/filters.

The `/paypoint/api/v1/` same-origin alias has equivalent behavior. Historical HTML bookmarks use authenticated role checks and redirects; retired object screens/submissions return 410. These compatibility URLs never restore obsolete financial forms. See PHASE-J-STABILIZATION-REPORT.md for the full inventory and verification evidence.


## Live UI additions — 25 October 2026

Under `/paypoint/api/v1/`: `roles/permission-choices/` returns administrator-visible assignable permission choices; `users/role_choices/` returns permitted financial roles. Staff records expose writable `phone` backed by the account profile. Payment intent payloads accept optional `reported_paid_at` and `remarks` (500 characters); these do not confirm payment and participate in idempotency validation. Invoice and payment directories support status inclusion filters; payments support `invoice__patient`. Receipt verification and reprint requests enforce department scope. Official receipt printing accepts `paper=a4` or `paper=thermal`, rejecting other values. Profile responses include `has_photo`; photo operations are isolated from private cash evidence.
