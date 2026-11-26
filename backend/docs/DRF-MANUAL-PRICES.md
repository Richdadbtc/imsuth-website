# DRF typed drug names and entered prices

The DRF form accepts a typed drug name, positive unit price and integer quantity for each row. Staff can add and remove drug rows. Names are required, up to 200 characters; duplicates use quantity instead. Prices allow at most two decimal places, from NGN 0.01 to NGN 1,000,000,000. The server computes totals and the existing patient discount; the submitted payment total must agree.

POST `drf_items` entries contain `name`, `quantity`, and `unit_amount`. Older clients may continue to send a known catalogue `code` instead of `name`; sending both is rejected. Missing names/prices, invalid prices and duplicate typed names cannot create a payment. Typed names and entered rates are snapshotted on the invoice, audit trail and itemized receipt, using the existing editable-price review alert. Historical receipts retain their recorded names and prices.

Only DRF changes. R/F and Over-head retain their existing pricing rules. Deploy backend and frontend; no database migration is needed for this change.
