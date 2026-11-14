# Payments without patient registration

Record Payment accepts a required typed patient name instead of looking up a registered patient. The name is stored on the invoice; no registry Patient is created. Capture accepts optional patient UUID for existing API clients and still checks that patient scope when supplied. Empty names without a patient are rejected.

Invoices can now have a null patient link with a required name snapshot. Generic invoice creation still requires a registered patient. Payment responses, printed receipts, latest receipts and department desk views use the invoice display name. Registered-patient report counts exclude unregistered invoices. Financial verification, reference checks, cash receiver selection, discounts and access permissions remain in force.

Apply billing migration 0003_walk_in_invoice_patient and deploy the backend before the frontend. No historical patient links are changed.
