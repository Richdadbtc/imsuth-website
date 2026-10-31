# Cash Points and Orders UI QA

Reference: codex-clipboard-17dfba55-e418-4ecd-87db-609897a4454d.png.
Route: #cash-points, also linked from Billing and revenue-control navigation.

Initial desktop rendering was inspected at 1536 × 1024. Summary cards, cash point
table, recent orders, standing-order form, illustrative limits and collection chart
are present within the existing application shell. Figures are derived from the
explicit sample records; the chart total is 490,500 (the supplied screenshot's
point rows do not sum to its illustrative chart total).

Functional checks passed: sample totals, pending-only new requests, signed-in
requester attribution, daily-limit and amount validation, point and order details,
new sample cash points, duplicate names, and unavailable live state.

Final result: blocked.
The initial desktop layout is inspected; final reference-comparison and full
browser form verification remain outstanding. This UI is a demonstration only.
No server cash-point or standing-order write exists, no cash is moved, and sample
approval limits do not grant authority. Live controls remain disabled.
