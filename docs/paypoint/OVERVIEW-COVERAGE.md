# Overview coverage

Implemented 26 October 2026. Frontend commit 1787a5f; backend overview endpoint commit 16a8185, followed by the aged-alert scheduling change.

The overview displays confirmed NGN collection totals and channel shares, daily stacked collections with zero-activity days, the top eight permitted departments, approved cash orders (separate from revenue), open alerts, and imported-statement reconciliation progress. Recent transactions, payment status, and quick actions remain available. Bank teller and USSD cards reflect recorded channel values; this change does not add new payment-provider integrations.

GET /api/v1/dashboard/overview-coverage/ accepts the same period/date parameters as the existing dashboard metrics. Confirmation dates determine collections; transaction dates determine statement rows; creation dates determine cash orders. Matched includes resolved rows. Unmatched amounts include manual review, unmatched, and amount mismatch. Unlinked statement rows are accessible only to global roles. No database migration is required.

A Celery Beat entry dispatches the existing idempotent reconciliation alert detector every 15 minutes with a 24-hour age threshold. The worker and scheduler must run; frontend activity does not trigger financial changes or background alert generation.

Verification: production frontend build; 17 frontend contract tests; 30 backend workflow tests; local synthetic-only browser review at desktop and 390px mobile widths; period filter changed daily bars from 30 to 7; no document overflow. Screenshots in website/paypoint/verification. The isolated browser database is outside the repository.

Deployment status: frontend pushed to its separate repository and Vercel deployment succeeded. Backend pushed to its separate repository. Remote SSH password authentication is unavailable to this agent. The VPS still needs an operator to update the existing PayPoint deployment and enable the worker/scheduler using its actual Compose files. Do not replace the shared reverse proxy or restart unrelated projects. Obtain the current Compose project name/config files from the running PayPoint web container labels before issuing deployment commands.
