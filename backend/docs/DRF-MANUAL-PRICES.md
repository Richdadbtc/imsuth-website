# DRF drug selection and entered prices

DRF exposes the 322 drug names without preset amounts. Each selected drug requires a positive unit price (maximum NGN 1,000,000,000; at most two decimal places) and an integer quantity. POST `drf_items` entries include `code`, `quantity`, and `unit_amount`. Missing, zero, negative, or malformed prices cannot be recorded. The server computes totals and the existing patient discount; the submitted payment total must agree.

`apps/common/drf.py` converts the source list to an editable-price catalogue and removes source amounts from the API response. The source JSON remains unchanged for provenance. The shared picker shows drug names and an empty price field after selection. Entered prices are captured in the DRF receipt snapshot, invoice and audit trail and use the existing editable-price review alert. Existing receipt snapshots retain their original prices.

Only DRF changes. R/F and Over-head still use their existing pricing rules. Deploy backend and frontend; no database migration is needed for this change.
