# Deposit payments

Record Payment includes SUB-HEAD `deposit` (Deposit). Choosing it replaces service selection with a required service description and an editable deposit amount, even when the department has configured services. Deposits use quantity 1 and must be positive NGN amounts with at most two decimal places. Patient type is retained but the amount received is recorded exactly as entered, without a patient discount.

POST `/api/v1/record-payment/` uses `sub_head: "deposit"`, `service_description`, `base_amount`, and matching `amount`. A catalogue service UUID or item basket cannot be submitted as a deposit. The existing cash point, receipt confirmation, permissions, reference validation, duplicate-reference checks and idempotency rules still apply.

The invoice item uses service code `DEPOSIT` and description `Deposit toward: <service>`. Receipt previews and reprints explicitly identify it as a deposit toward that service, not payment of its full cost. Recording a deposit does not settle or apply credit to a separate existing service invoice. Existing receipts remain unchanged.

Deploy backend and frontend. Apply common migration `0017_recordedpayment_deposit_sub_head`.
