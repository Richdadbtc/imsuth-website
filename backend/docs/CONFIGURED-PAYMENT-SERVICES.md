# Configured services in Record Payment

The payment setup response includes active services belonging to permitted active departments, with their current approved NGN tariff (or null if none exists). The cashier shared-point department rules apply to this read-only list.

When a department has active configured services, the frontend displays a required service dropdown. Services without a current approved tariff are disabled and labelled accordingly. Selecting a priced service fills the full service amount; the existing patient-type discount is applied afterward. Catalogue submissions send the service ID, and the backend validates its department, activity and current tariff again.

A department with no active configured services retains manual description and full-price entry. Changing departments clears the previous selection and amount. Existing price-override reason and audit rules remain in place.

Deploy backend and frontend. No database migration is needed for this update.
