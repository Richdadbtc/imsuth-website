# Cash receiver selection

Record Payment setup now returns the approved cash receivers: Nwaele Juliet, Udegbe Egonna, Onuoha Lilian, Ibewuike Blessing, Sabina Mbenaso, Anisa Eze, Emafor Egomau, Obiefule Rachel, Ibemye Senfa, Odimegwu Henrietta, Nwodife Edith, Okonkwo Grace, Chibue Chigozie, Amozie Esther. Selecting Cash replaces the reference input with a required receiver dropdown. Other channels retain their payment reference requirements.

The capture API requires an approved receiver for cash, clears the submitted reference for cash, and rejects a receiver for other channels. Receiver names are reusable across payments; cash submissions are not deduplicated by blank reference. Request-key idempotency remains enforced. The receiver is stored in Payment.cash_receiver, returned in payment responses, included in the capture audit event and displayed on the printed receipt. The authenticated recording officer remains tracked independently. Selecting a name does not verify payment or grant access.

Receiver storage was introduced by payments migration 0004_payment_cash_receiver. This list update requires only a backend deployment; no new migration is needed.

The ten additional names extend the original four receiver choices, giving fourteen options. Previously recorded receiver names remain on historical receipts. The frontend fetches this list from the backend; no frontend change or database migration is required.
