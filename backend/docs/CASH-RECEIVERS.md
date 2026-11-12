# Cash receiver selection

Record Payment setup now returns the approved cash receivers: Nwaele Juliet, Udegbe Egonna, Onuoha Lilian, and Ibewuike Blessing. Selecting Cash replaces the reference input with a required receiver dropdown. Other channels retain their payment reference requirements.

The capture API requires an approved receiver for cash, clears the submitted reference for cash, and rejects a receiver for other channels. Receiver names are reusable across payments; cash submissions are not deduplicated by blank reference. Request-key idempotency remains enforced. The receiver is stored in Payment.cash_receiver, returned in payment responses, included in the capture audit event and displayed on the printed receipt. The authenticated recording officer remains tracked independently. Selecting a name does not verify payment or grant access.

Apply payments migration 0004_payment_cash_receiver before starting the updated backend. Historical payments remain unchanged with a blank receiver. Deploy the backend and frontend together.
