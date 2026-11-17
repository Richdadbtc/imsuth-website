# Automatic cash receiver

Record Payment records the signed-in officer's full name as `Payment.cash_receiver` for cash. If the account has no full name, it uses the username. The backend derives the value from the authenticated account and ignores any submitted receiver name. Other payment channels store no cash receiver.

The frontend displays the name in a read-only input when Cash is selected; there is no dropdown. Payment setup exposes `cash_receiver` and `cash_receiver_automatic`; a one-name `cash_receivers` list remains for older clients during deployment.

The stored name is a snapshot: renaming an account does not rewrite historical payments or receipts. The account ID remains tracked independently by `initiated_by`, the recorded-payment context and audit events. This does not grant access or verify funds.

Deploy backend and frontend. Apply payments migration `0005_cash_receiver_full_name`, which widens receiver storage to accommodate the full account name without truncation. The former approved-name list is no longer used for capture validation.
