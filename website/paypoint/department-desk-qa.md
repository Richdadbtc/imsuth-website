# Department Desk UI QA

Reference: codex-clipboard-1326402a-e11b-46db-8788-249175c99d78.png.
Route: #patients. The previous patient directory remains at #patient-directory.

The page follows the reference's receipt search, receipt information, service
delivery, recent verification history, quick lookup and department services layout.
Initial browser rendering confirmed that the route opens Department Desk and that
the patient directory link remains visible. All receipt lists are department-scoped.
A patient or receipt is not preselected with invented information.

Functional checks passed: department-scoped search, current payment confirmation,
demo delivery selection/confirmation, receipt details, department-switch reset,
cross-department guard, invalid date range, and unverified-payment delivery lock.
Live receipt verification calls receipts/verify/. Live service-delivery writes are
not connected; those controls are disabled. Demo delivery state is session-local.

Final result: blocked.
The browser integration invalidated the tab on the next inspection call. Final
full-page screenshot comparison and browser end-to-end verification could not be
completed. No exact visual fidelity or live service-delivery recording is claimed.
