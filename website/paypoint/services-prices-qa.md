# Services and Prices UI QA

Reference: codex-clipboard-63f1c536-a258-4c68-8a95-b1a8ba964260.png.
Route: #admin-services. Previous management details remain at #services-management.

Desktop rendering was inspected at 1536 × 1024. The service summary cards, filters,
service/price table, department information and add/edit panel were visibly present.
The existing application shell is retained. Financial values reflect available
approved tariffs, not the illustrative screenshot's prices. NHIS/IMSHIA prices are
explicitly unconfigured. Category/unit writes are limited to supported metadata.

Functional checks passed: filtering, pagination, editor prefill, draft price saves,
preservation of approved tariffs, invalid-price rejection, form clearing and new
service preview. Live saves use the service API and then a separate unapproved
tariff create. Partial failure reports that service details may already be saved.

Final result: blocked.
Desktop visual inspection is complete. Full reference comparison and browser
end-to-end save verification remain outstanding; no exact fidelity claim is made.
