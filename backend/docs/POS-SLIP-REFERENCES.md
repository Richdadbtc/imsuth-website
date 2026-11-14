# POS slip reference validation

Bank-transfer payments require a complete 25-character TRANS REF: `09FG`, 16 digits, then five alphanumeric characters. Example: `09FG2611042341124813CY0W7`. Whitespace from wrapped slip lines is removed and letters are uppercased. The first 12 digits must represent a valid YYMMDDHHMMSS transaction timestamp.

POS/card payments instead require the 12-digit Reference Number printed on the card purchase slip (for example `631313012611`). The six-digit STAN and Auth Code are not accepted. Transfer TRANS REF strings are not accepted as card references.

The backend enforces this when capturing payments, creating receipts, and opening receipt print views. The frontend guides entry with the same format. Cash and other channels retain their existing rules. Existing POS/transfer receipts with nonconforming references cannot be printed through the print endpoint; historical records are not rewritten.

A matching reference format is not payment verification. Existing authoritative confirmation requirements remain in place before paid receipts can be issued.

Deploy the backend and frontend together. No database migrations are required for this change.
