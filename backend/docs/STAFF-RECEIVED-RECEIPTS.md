# Receipt issuance at collection

Record Payment supports explicit `payment_received: true` for cash, POS/card and bank-transfer collections. The signed-in collection officer attests funds were received using a required, initially unchecked checkbox. The capture endpoint retains role, cash-point, department, reference, receiver, discount and idempotency checks. Confirmation, paid invoice, official receipt and staff-attributed audit event are committed atomically. Receipt preview opens immediately, with printing as a separate user action.

This is staff confirmation, not independent bank/provider verification or settlement. A reference format by itself does not confirm a payment. Online payments cannot use staff attestation. API requests omitting the flag retain pending behavior. Existing pending payments are not automatically confirmed.

Deploy backend and frontend together. No new database migration is required for this change.
