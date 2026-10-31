# API contract for the PayPoint screens

Base path: `/api/v1/` in Django, mounted at `/paypoint/api/v1/` by the deployment proxy.
All endpoints require an authenticated Django session unless explicitly marked public.
All writes require CSRF protection through session authentication. Financial lists and
reports are limited to finance, management, auditor and system administrator roles.
Auditors cannot mutate financial data. Staff and configuration management require
`super_admin`. Existing registry and payment role restrictions remain authoritative.

## Screens and endpoints

| Screen | Endpoints |
|---|---|
| Login/recovery | `GET session/`, `POST session/login/`, `POST session/logout/`, public `POST session/recovery/request/`, `verify/`, `complete/` |
| User account | `GET/PATCH profile/`, `POST profile/password/`, `GET/POST/DELETE profile/photo/`, `POST profile/deactivate/` |
| Staff | `GET/POST staff/`, `GET/PATCH staff/{id}/`, `POST staff/{id}/deactivate/` |
| Roles | `GET/POST roles/`, `GET/PATCH roles/{id}/`, `POST roles/{id}/assign/` with `user` |
| Departments/services | Existing `departments/`, `services/` list/detail/create/update |
| Tariffs | `GET/POST tariffs/`, `GET/PATCH tariffs/{id}/`, `POST tariffs/{id}/approve/` |
| Patients | Existing `patients/` list/detail/create/update |
| Invoices | Existing `GET/POST invoices/`, `GET invoices/{id}/` |
| Payments | Existing `GET/POST payments/`, `GET payments/{id}/`, `POST payments/{id}/retry/`, `POST payments/{id}/verify/` |
| Receipts | Existing `GET receipts/`, `GET receipts/{id}/`, `POST receipts/verify/`, `GET/POST receipt-reprints/` |
| Refunds/reversals | `GET/POST refunds/`, `GET refunds/{id}/`, corresponding `reversals/` paths |
| Approval queue | `GET approvals/`, `GET approvals/{id}/`, `GET approvals/{id}/history/`, `POST approvals/{id}/decide/` |
| Daily settlements | `GET/POST settlements/`, `GET settlements/{id}/` |
| Bank reconciliation | `GET reconciliation-batches/`, `GET reconciliation-batches/{id}/`, `POST reconciliation-batches/import/` |
| Discrepancies | `GET discrepancies/`, `GET discrepancies/{id}/`, `POST discrepancies/{id}/request_resolution/` |
| Notifications admin | `GET/POST notifications/`, `GET/PATCH notifications/{id}/`, `POST notifications/{id}/enqueue/` |
| Personal notifications | `GET inbox/`, `GET inbox/{id}/`, `POST inbox/{id}/read/` |
| Settings | `GET/POST settings/`, `GET/PATCH settings/{section}/` |
| Audit/activity | Read-only `GET audit-events/`, `GET audit-events/{id}/` |
| Help/support | `GET help/`, `GET/POST support-tickets/`, `GET/PATCH support-tickets/{id}/`, `POST support-tickets/{id}/reply/`, `POST support-tickets/{id}/attachments/`, `GET attachments/{id}/` |
| Integration availability | `GET capabilities/`, `POST integrations/{operation}/` |
| Reports | `GET reports/` catalogue, `GET reports/{type}/` with summaries, groups and paginated rows; add `?format=csv` for export |

Report types: `revenue`, `daily-collection`, `department-revenue`, `cashier-collection`,
`payment-channel`, `outstanding-invoices`, `settlements`, `reconciliation`, `audit`,
`patient-registration`, `system-activity`. All accept `from` and `to` (ISO dates,
maximum 366 days). Payment reports accept department/channel/provider/status/cashier;
patient reports accept sex/status; reconciliation accepts status/channel/provider;
settlement reports accept provider; audit reports accept action/user. Only those
filters are supported. Payment service allocations are explicitly rejected instead
of misreporting full invoice totals. Reports return `{count,next,previous,results,
summary,groups,from,to,report}`. CSV is limited to 10,000 records.

## Workflow bodies

- Refund: `{payment, amount, reason}`. Reversal: `{payment, reason}`.
  Pending/completed requests cannot exceed the original payment. A reversal cannot
  overlap an active refund. Maker and approver must differ. Approval only queues
  provider execution; it never claims money has moved.
- Decision: `{approved: true|false, reason}`. A decision is immutable and cannot
  be repeated. Financial approvers retain the existing finance/management role rule.
- Reconciliation import: multipart `file` and `source`, UTF-8 CSV columns
  `reference,amount,currency,transaction_date` (ISO timestamp), maximum 5MB.
- Resolution request: `{reason}`; creates a manual-match approval. A different
  authorised approver must approve it before the discrepancy becomes resolved.
- Payment retry: `{idempotency_key}` creates a new payment intent only for a
  failed/expired payment and checks the current invoice balance.
- Receipt verification: `{receipt_number}`; returns valid only for a confirmed
  payment. Reprint: `{receipt, reason, format: "a4"|"thermal"}` records the audit event.
- Profile PATCH: `{first_name,last_name,email,profile:{phone,address,job_title,
  date_of_birth,gender,qualification,specialization,license_number,bio,preferences}}`.
  Role, employee ID and account status cannot be self-edited. Preferences are
  stored independently from actual provider delivery and browser display behavior.
- Password: `{current_password,new_password}`; validates server password policy,
  rate-limits attempts and invalidates all previous sessions. Deactivation requires
  `{password}`; administrators cannot deactivate themselves.
- Notification enqueue: `{users:[staff_id,...]}`. In-app delivery is implemented;
  external sends fail closed until a dispatcher is configured.
- Support ticket creation: `{subject,category,priority,message}`; staff see only
  their own tickets and attachments. Administrators can manage all tickets.
  Ticket status: open/in_progress/resolved. Reply: `{message}`.

## Deployment and deliberate boundaries

Run `python manage.py migrate` and install requirements before rollout. Profile
images use Pillow and are re-encoded, metadata-stripped, size-limited and privately
served. Attachments are downloaded only after ownership checks and are never
publicly served. Audit records are read-only and exclude request bodies/passwords.
CSV cells escape formula prefixes. Financial decisions are transactional.

The seven built-in User.role financial policies remain authoritative. `roles/`
manages Django groups and non-administrative Django permissions; group assignment
does not override existing financial roles. Do not present the group permission
matrix as a replacement for the financial role policies.

Settlement APIs expose actual recorded provider settlements, not fabricated batch
state, fees or balances. Patient directory data does not imply returning visits.
Overdue totals are null because invoice due dates are not currently recorded.
Audit data does not imply uptime telemetry. `capabilities/` identifies these limits.
Provider payment verification, refund/reversal execution, SMS/email dispatch,
2FA enrollment, QR sign-in, live chat and backup/restore runners require external
integration and return unavailable responses rather than simulating success.

Frontend demo mode is unchanged by this backend task. The UI must be switched to
live mode and its demo-only controls wired to these contracts before production.
