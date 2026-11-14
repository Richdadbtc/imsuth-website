# Receipt Reprints register

Receipt Reprints lists the scoped official receipt register rather than only prior reprint events. All issued receipts, including those never reprinted, are available through search and server pagination. Rows show patient name (including unregistered names), department, service, amount, issued time, payment status and reprint count.

View provides preview, audited reprint for authorized cashiers/finance/super administrators, and reprint history. A reason and A4/thermal format are recorded through the existing reprint endpoint. Reprinting retains the original receipt number and does not create another receipt or payment. Current payment state, reference validation and department scope remain enforced by backend endpoints. Pending payment attempts without an issued receipt are not receipt records.

The receipts API now supports explicit payment/invoice filters and patient/department search. Reprint history remains available through receipt-reprints/?receipt=<id>. No database migration is required. Deploy updated backend and frontend.
