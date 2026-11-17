# Compact bank transfer references

New bank transfer submissions save the first four and last five letters/numbers of the printed reference, separated by a slash. Example: `09FG2611042341124813CY0W7` becomes `09FG/CY0W7`.

The frontend inserts the slash while typing and can extract the two parts when a full supported 25-character TRANS REF is pasted. The API accepts either the compact value (with or without the slash) or a valid legacy full TRANS REF and saves the compact form. Card payments still require the twelve-digit card Reference Number. Cash receiver selection is unchanged.

Existing stored references are not rewritten; legacy transfer receipts remain printable. Record Payment checks for both compact and matching legacy references before accepting another submission. Truncation reduces uniqueness: two real transfers sharing the same first four and last five characters are rejected as duplicates and need administrator review rather than a fabricated reference.

Reference formatting is not payment verification. The existing funds-received attestation and provider-confirmation rules still apply. Deploy backend and frontend; no migration is needed.
