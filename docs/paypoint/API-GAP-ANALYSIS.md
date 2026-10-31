# Revenue Control API gap analysis — 24 October 2026

Fresh baseline: 68 discovered tests, 44 passed, 23 errors in removed legacy template URL names, 1 PostgreSQL-only test skipped (SQLite). This differs from the earlier 34-pass baseline. No PostgreSQL concurrency pass is claimed.

The audit inventoried 99 Python app files (models, serializers, views, services, permissions, migrations and tests), inspected the current static client, and reviewed IMPLEMENTATION-PROGRESS, TECHNOLOGY-STACK-AUDIT and PHASE-H-UI-UX-REPORT. The hospital HTML source could not be uniquely identified in the workspace; the supplied eight screenshots and current client are the available references. Screenshots do not define accounting policy.

| Screen / endpoint group | Classification | Finding |
|---|---|---|
| dashboard summary, channel/department/status/trend/recent/alert summaries | REUSABLE WITH MODIFICATION | Existing `/dashboard/` aggregates lack date/scoped metric contract; add named subresources. |
| patients search/detail | REUSABLE WITH MODIFICATION | Existing searchable registry; enforce assigned department scope and explicit search action. |
| department/service list/detail/create/update | REUSABLE WITH MODIFICATION | Existing models; add nested resources and disallow historical deletion. |
| invoices create/detail/balance | REUSABLE WITH MODIFICATION | Reuse server tariff snapshots, add balance and scope validation. |
| payments create/list/detail/verify/status | REUSABLE WITH MODIFICATION | Existing idempotency and provider confirmation service. Verification is 503 without evidence adapter; references are never confirmation. |
| receipts detail/print | REUSABLE WITH MODIFICATION | Existing verified receipts and reprint audit; print endpoint must remain authorised. |
| department desk receipt lookup/verify/activity/summary/delivery | NEW | Reuse Receipt/InvoiceItem; add unique delivery record, no new payment ledger. |
| department summary/collections/transactions/services/staff/trends | REUSABLE WITH MODIFICATION | Reuse catalogue, invoice and payment relations. |
| service tariff/history/categories/proposals and tariff proposal decisions | REUSABLE WITH MODIFICATION | Reuse TariffVersion; explicit independent approval proposals needed. |
| cash points/summary/collections | NEW | No point identity/assignment model. Do not infer attribution from department alone. |
| cash orders/create/detail/approve/reject/approval-limits | NEW | No configured policy or order model. No seeded limits; approval is separate from collection/deposit. |
| alerts/list/detail/summary/analytics/assign/review/resolve | NEW | Notifications and reconciliation rows cannot substitute for alert lifecycle. |
| users CRUD/activate/deactivate/permissions | REUSABLE WITH MODIFICATION | Alias existing staff; seven existing role values retained. |
| roles | EXISTING | Current `/roles/` is Django Groups, not authoritative User.Role; preserve compatibility and expose role choices separately. |
| audit logs/list/detail/summary | REUSABLE WITH MODIFICATION | Alias existing immutable audit reader with dates and summary. |

Canonical current prefix `/api/v1/`; retain it and add `/paypoint/api/v1/` compatibility mapping. Existing router names are not duplicated within a namespace. Existing `/dashboard/` and `/audit-events/`, `/staff/` remain available. No production infrastructure changes are authorised or made.

Implementation status and verification are recorded in API-INTEGRATION-REPORT.md; this gap analysis is not a completion claim.
