# Overview calendar and staff collections

Overview replaces its period dropdown with From/To calendar inputs, Apply dates and Last 30 days reset. Every overview metric receives the same explicit `period=custom&date_from=YYYY-MM-DD&date_to=YYYY-MM-DD` range. The default range is 30 inclusive days in Africa/Lagos. Older in-flight filter requests are cancelled when a new valid range is applied.

Administrators (`super_admin`) and auditors see Collections by paypoint staff with staff name, username, confirmed payment count, channel totals and total received, displayed to two decimal places. Staff collection requests load independently of the other charts. Cashiers with no confirmed collections appear with zero; historical collectors remain included even if their account has since been deleted or changed role.

GET `/api/v1/dashboard/collections-by-staff/` is restricted server-side to administrators and auditors. It aggregates confirmed NGN payments by the collecting account (`Payment.initiated_by`), using confirmation dates, not payment creation dates. Cash, POS/card, POS transfer, other channels and deposits count in amounts received. Pending, failed, refunded and reversed states are excluded. This is collected money, not certified bank settlement. Receipt users and entered cash receiver aliases are not used to merge distinct user accounts.

Date bounds are inclusive in Africa/Lagos; invalid or reversed dates return HTTP 400. No passwords or unnecessary staff contact details are returned. Deploy backend and frontend; no migration is required.

## SUB-HEAD totals

Overview summary includes `sub_head_totals` for Over-head, R/F, DRF and Deposit. These sum actual confirmed NGN payment amounts (after any patient discount), grouped by the immutable payment capture SUB-HEAD. They use the same confirmation-date range and department access scope as overall collections. Empty categories return zero. `unclassified` accounts for confirmed payments without a recognized saved SUB-HEAD; it is displayed separately when present so category totals reconcile with overall collections. No category is inferred from service names or the patient's category. This change requires both deployments and no migration.
