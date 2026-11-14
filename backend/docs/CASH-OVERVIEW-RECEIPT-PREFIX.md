# Cash overview and receipt prefix

The overview Cash received card uses all confirmed cash collections in the selected period and access scope, including cash without a standing order. Cash already participates in total collections, channel split, daily channels and recent transactions. The overview-coverage API now additionally returns cash_received totals; cash_under_orders retains its narrower meaning for compatibility. Pending, failed and reversed payments remain excluded from confirmed collections.

New receipts issued by collection officers or provider confirmation use IMSUTH-RCT-<year>-<sequence>. Existing receipt numbers and QR destinations are not changed.

Deploy backend and frontend. No database migrations required.
