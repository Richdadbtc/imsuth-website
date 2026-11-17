# Cashier dashboard

The Cashier Dashboard now uses `GET /api/v1/dashboard/cashier/?period=30`, rather than the management overview. Cashier accounts see only payments they initiated, across departments and cash points, regardless of whether they have an assigned home department. Finance and super administrators see hospital collections. Other roles are denied.

The endpoint returns confirmed NGN amount/count, receipt count, pending amount/count, confirmed channel totals, and the latest ten payment attempts. Confirmation date determines collection totals; creation date determines recent and pending payments. Supported periods follow the existing dashboard date rules. Empty periods show zero totals and empty tables; request failures show an error with retry.

Existing page-access settings still apply. No account permissions or historical payments are changed. Deploy both backend and frontend; no migration is required.
