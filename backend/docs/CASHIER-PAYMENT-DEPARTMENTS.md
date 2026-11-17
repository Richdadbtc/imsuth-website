# Cashier payment departments

Record Payment returns active department choices directly in its authenticated setup response. Cashiers with access to an active shared hospital cash point can collect for any active department, even without an assigned home department. Department-specific cash points retain their department and assigned-officer restrictions. Inactive departments cannot receive payments.

The frontend uses these payment-specific choices instead of the general department directory, which remains scoped. Older backends retain the previous directory fallback.

Cashiers can preview and reprint receipts they recorded at shared points, including payments for another department. This does not grant access to other officers' out-of-department receipts, patient records, department administration, or other departments' payments.

Deploy backend and frontend together. No database migration is required.
