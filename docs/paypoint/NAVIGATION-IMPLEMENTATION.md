# IMSUTH PayPoint Navigation Implementation

## Architecture decision

The active PayPoint interface is the static client under `website/paypoint/`. It uses HTML5, CSS3 and ES6 modules and communicates with authenticated Django REST endpoints under `/api/v1/`. The earlier Django-rendered screens remain in the backend for compatibility, but this implementation does not create a second template navigation system.

Navigation metadata is centralized in `website/paypoint/static/paypoint/frontend.js`. Django remains authoritative for authentication, role permissions, patient IDs, invoice totals, payment status, approvals and audit data. Hiding a navigation item is only a presentation control; every API request remains subject to backend permission classes.

## Existing roles

The implementation preserves the seven backend roles: Super Administrator, Hospital Management, Accounts / Finance, Auditor, Department Supervisor, Front Desk Officer and Cashier / PayPoint Officer.

## Navigation matrix

`Static route` identifies the client-side route. `Backend source` names the API or protected backend workflow used by the view. An “honest state” does not claim that an unsupported integration or transaction succeeded.

| Section | Dropdown page | Static route | Backend source | Required permission | Status | Test status |
|---|---|---|---|---|---|---|
| Dashboard | Management Dashboard | `#dashboard` | `dashboard/` | Authenticated | Implemented | Browser checked |
| Dashboard | Front Desk Dashboard | `#dashboard-front-desk` | `dashboard/` preset | Authenticated; role redirect pending real login | Implemented | Browser checked |
| Dashboard | Cashier Dashboard | `#dashboard-cashier` | `dashboard/` preset | Authenticated | Implemented | Browser checked |
| Dashboard | Finance Dashboard | `#dashboard-finance` | `dashboard/` preset | Finance-capable role in production | Implemented | Syntax checked |
| Dashboard | Daily Activity Overview | `#dashboard-daily` | `dashboard/` preset | Authenticated | Implemented | Syntax checked |
| Patients | All Patients | `#patients` | `patients/` | Patients | Implemented | Browser checked |
| Patients | Register Patient | `#patient-registration` | Patient create API required for production save | Patients | Demo-safe form implemented | Browser checked |
| Patients | Patient Profiles | `#patient-profile` | Synthetic selected patient; production patient API selection required | Patients | Profile UI implemented | Browser checked |
| Patients | Patient Search | `#patient-search` | `patients/` | Patients | Implemented | Syntax checked |
| Patients | Patient Billing History | `#patient-billing-history` | Patient selection then invoices | Patients + Billing | Selection state implemented | Syntax checked |
| Billing | All Invoices | `#billing` | `invoices/` | Billing | Implemented | Existing regression coverage |
| Billing | Create Invoice | `#billing-create` | Invoice create API required for production submission | Billing write role | Interactive demo-safe builder implemented | Browser checked |
| Billing | Pending Invoices | `#billing-pending` | `invoices/` filtered | Billing | Implemented | Syntax checked |
| Billing | Invoice Details | `#billing-details` | Synthetic selected invoice; production invoice-detail API required | Billing | Detail UI implemented | Browser checked |
| Billing | Paid Invoices | `#billing-paid` | `invoices/` filtered | Billing | Implemented | Syntax checked |
| Billing | Cancelled / Corrected | `#billing-cancelled` | `invoices/` filtered | Billing | Implemented | Syntax checked |
| Billing | Departments & Services | `#billing-services` | Departments/services APIs | Billing | Honest authenticated state | Syntax checked |
| Billing | Service Tariffs | `#billing-tariffs` | Tariff API | Billing | Honest authenticated state | Syntax checked |
| Payments | All Transactions | `#payments` | `payments/` | Payments | Implemented | Existing regression coverage |
| Payments | Process Payment | `#payments-process` | Payment API and provider verification required for production submission | Cashier / Finance | Interactive demo-safe workflow implemented | Browser checked |
| Payments | Verify Payment | `#payments-verify` | Provider verification API required for production decisions | Payments | Interactive demo-safe review implemented | Browser checked |
| Payments | Pending Payments | `#payments-pending` | `payments/` filtered | Payments | Implemented | Syntax checked |
| Payments | Verified Payments | `#payments-verified` | `payments/` filtered | Payments | Implemented | Syntax checked |
| Payments | Failed Payments | `#payments-failed` | `payments/` filtered | Payments | Implemented | Syntax checked |
| Payments | Receipts | `#payments-receipts` | Receipt API | Payments | Honest authenticated state | Syntax checked |
| Payments | Receipt Verification | `#payments-receipt-verification` | Receipt verification workflow | Authorized lookup | Honest secure state | Syntax checked |
| Payments | Receipt Reprints | `#payments-receipt-reprints` | Receipt API + audit | Authorized reprint | Honest secure state | Syntax checked |
| Finance | Finance Overview | `#finance` | Approvals + reconciliation APIs | Finance | Implemented | Existing regression coverage |
| Finance | Revenue Collections | `#finance-collections` | Verified payments | Finance | Implemented | Syntax checked |
| Finance | Settlements | `#finance-settlements` | Provider integration required | Finance | Honest unavailable state | Syntax checked |
| Finance | Bank Reconciliation | `#finance-reconciliation` | Reconciliation API | Finance | Reuses finance workspace | Syntax checked |
| Finance | Reconciliation Discrepancies | `#finance-discrepancies` | Reconciliation API | Finance | Reuses finance workspace | Syntax checked |
| Finance | Refund Requests | `#finance-refunds` | Approval API | Finance | Reuses finance workspace | Syntax checked |
| Finance | Reversal Requests | `#finance-reversals` | Approval API | Finance | Reuses finance workspace | Syntax checked |
| Finance | Approval Queue | `#finance-approvals` | Approval API | Finance | Reuses finance workspace | Syntax checked |
| Administration | Staff Management | `#administration` | Protected staff backend | Administration | Secure state | Syntax checked |
| Administration | Add Staff | `#admin-add-staff` | Staff creation backend | Super Administrator | Honest secure state | Syntax checked |
| Administration | Roles & Permissions | `#admin-roles` | Existing role model | Super Administrator | Read-only explanation | Syntax checked |
| Administration | Departments Management | `#admin-departments` | Catalogue backend | Super Administrator | Honest secure state | Syntax checked |
| Administration | Services Management | `#admin-services` | Catalogue backend | Super Administrator | Honest secure state | Syntax checked |
| Administration | Tariff Management | `#admin-tariffs` | Versioned tariff backend | Super Administrator / Finance | Honest secure state | Syntax checked |
| Administration | Notifications | `#admin-notifications` | Notification backend | Administration | Honest secure state | Syntax checked |
| Administration | System Settings | `#admin-settings` | Protected configuration | Super Administrator | Honest secure state | Syntax checked |
| Administration | Audit Logs | `#admin-audit` | Append-only audit backend | Authorized auditor/admin | Honest secure state | Syntax checked |
| Reports | Revenue Reports | `#reports` | Dashboard reporting API | Reports | Implemented | Browser checked |
| Reports | Daily Collection | `#reports-daily` | Reporting preset required | Reports | Honest server-filter state | Syntax checked |
| Reports | Department Revenue | `#reports-department` | Reporting preset required | Reports | Honest server-filter state | Syntax checked |
| Reports | Cashier Collection | `#reports-cashier` | Reporting preset required | Reports | Honest server-filter state | Syntax checked |
| Reports | Payment Channel | `#reports-channel` | Reporting preset required | Reports | Honest server-filter state | Syntax checked |
| Reports | Outstanding Invoices | `#reports-outstanding` | Reporting preset required | Reports | Honest server-filter state | Syntax checked |
| Reports | Settlement | `#reports-settlement` | Provider settlement source required | Reports | Honest server-filter state | Syntax checked |
| Reports | Reconciliation | `#reports-reconciliation` | Reconciliation API | Reports | Honest server-filter state | Syntax checked |
| Reports | Export Reports | `#reports-export` | Authorized export endpoint required | Reports | Honest server-filter state | Syntax checked |

## Interaction and accessibility

- Parent controls expose `aria-expanded` and `aria-controls`.
- Collapsed child links use the native `hidden` state and cannot receive focus.
- The current child and parent group are highlighted and automatically expanded.
- Expansion state is retained in session storage.
- Transitions respect `prefers-reduced-motion`.
- Hash navigation closes the mobile drawer.
- Account navigation includes My Profile, Change Password and Logout.

## Security controls preserved

- Django API permissions remain authoritative.
- Patient registration cannot save an official record in demo mode.
- Invoice totals and tariff snapshots remain backend-controlled.
- Payments cannot be manually marked verified by the frontend.
- Official receipts are not generated for unverified payments.
- Maker-checker decisions and audit records remain backend-controlled.
- Secrets and sensitive settings are not exposed in frontend source.

## Remaining backend work

- Add dedicated API/report presets for each report route.
- Expose authorized staff, notification and audit list APIs where management approves.
- Add production receipt lookup/reprint endpoints with audit recording.
- Connect role-specific login redirects after demo authentication is removed.
- Add real provider settlement integration before enabling settlement claims.

## Verification results

- JavaScript syntax check: passed.
- Django system check: passed with zero issues.
- Migration drift check: passed; no changes detected.
- Static frontend API tests: 2 passed.
- Browser desktop dropdown expansion, child-route navigation and account menu: passed.
- Full backend regression suite: **not green** — 46 tests ran, 23 errored and 1 skipped. The errors are existing legacy Django-template tests that reverse route names removed when the UI was separated into the static frontend (`login`, `dashboard`, `patient-list`, `invoice-create`, `management-dashboard` and related names). No financial assertion failed before route resolution. These tests must be migrated to the API/static-client architecture or the legacy URL includes must be deliberately restored.
- Mobile browser automation at all five requested widths remains pending; responsive CSS and off-canvas closure behavior are implemented, but passing status is not claimed.
