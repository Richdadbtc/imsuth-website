# Payment capture, Department Desk and supplied overview

Implemented 27 October 2026.

## New capture contract

`GET /api/v1/record-payment/` supplies permitted active cash points, approved cash orders, the latest ten official receipts with service-use status, and the caller's recording capability.

`POST /api/v1/record-payment/` atomically creates an invoice, a pending payment attempt and its collection context. It accepts patient, department, service, quantity, cash_point, optional cash_order, amount, override_reason, channel, submitted_reference, reported_paid_at, remarks and a UUID idempotency_key. The same request key and payload return the original result. Reusing a key with different data or an already-recorded channel/reference is rejected.

Only cashier, finance and super_admin roles may capture payments. Cashiers must use their assigned point. Department and patient visibility match existing access rules. Cash orders must be approved, match the cash point and retain sufficient capacity; they may only be linked to cash attempts. Cash capture reserves the point's remaining daily limit until attempts fail, expire, refund or reverse. These capacity checks cover captures made through this endpoint; legacy payments without a capture context cannot be attributed to a point or order automatically.

A reason is required for a changed tariff price. The invoice item is created once with that price, keeping the approved tariff version and original approved total in the capture context; existing issued invoice items remain immutable. The price difference is audited and creates a review alert. No submitted reference or entered amount confirms payment. Official receipts continue to require the authoritative confirmation workflow.

## Department Desk

Receipt list/check endpoints accept a department UUID filter and enforce caller scope. Payloads include department names, payment and persistent service-use status, item-level delivery state and delivery permission. The UI loads paginated department receipts instead of downloading the entire patient/payment/invoice directory. It checks a receipt before enabling authorized service delivery and refreshes state after each update. Disputed invoices and duplicate service deliveries remain blocked. Printing uses the existing official receipt endpoint.

## Overview

The overview section uses the layout and scoped styles from the user-supplied `imsuth-dashboard (2).html`. Its generated sample data, simulated actions and inline event handlers are not imported. Confirmed collections drive the channel cards/charts. Cash under orders includes only confirmed cash payments explicitly linked to a standing order. Reconciliation counts imported statement rows. NHIS/IMSHIA show unconfigured rather than inferring patient categories or applying the file's illustrative ten-percent tariff policy.

## Deployment

Migration `common.0007_recordedpayment` is required. Take the normal database backup first. Use the existing PayPoint Compose project and files (read their labels from `imsuth-paypoint-web-1`); do not substitute another project's configuration or restart the shared edge proxy.

Build the updated PayPoint web image, run `python manage.py migrate --noinput` in the updated image with the existing environment, then replace the PayPoint web service. The earlier overview's alert schedule also requires its worker and Beat services. Confirm migrations, health, authenticated capture metadata and department receipt checks before enabling operational use.

The frontend detects a 404 for the new capture endpoint and retains the previous working Record Payment/Department Desk screens during the rolling update. It does not fall back on authorization, network or server errors. Deploying frontend files alone therefore does not activate the enhanced capture flow.

## Verification

42 backend workflow/billing/payment tests and 17 frontend contract tests pass, and the production Next.js build succeeds. Browser tests used an isolated SQLite database outside the repository and synthetic-only accounts. Capture remained pending without a receipt; an override generated a review flag. Department receipt checking and service delivery succeeded, and the delivered service became unavailable for duplicate use. No production account, transaction, database, provider or VPS was modified.
