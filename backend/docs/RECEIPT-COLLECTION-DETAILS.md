# Collection details on receipts

A4, thermal, preview and reprint HTML now display the invoice department paid for, the cash point saved in RecordedPayment, and the officer who recorded the collection. The officer is the stored transaction creator, not the current viewer or cash-point assignee. Cash received by remains a separate field for cash payments.

For older payments without collection context, the cash point is explicitly Not recorded and the payment initiator is used for the recording officer. Missing historical information is not invented. Existing access, payment state and slip checks remain unchanged.

Backend-only deployment; no database migration or frontend build is required for these receipt fields.
