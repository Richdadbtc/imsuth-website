# R/F departmental services

Record Payment now exposes a separate **R/F service department** selector after choosing R/F. The seven source sections contain 238 entries: Rehabilitation (7), Ophthalmology (30), Chemical Pathology (34), Accident and Emergency (30), Microbiology (35), Radiology (83), and Haematology (19).

The supplied updated departmental PDF is a draft transcription. Its SHA-256 and original rate text are preserved in `apps/common/data/rf_services.json`. Nineteen entries with unclear departments, units, prices, marked amendments, variable rates, or a duplicate source row are visible but unavailable for billing. Do not substitute zero or an invented fixed price. Confirm those entries with the hospital before changing `available` and their prices/units. Radiology sections use distinct page-based codes because source numbers overlap.

`GET /api/v1/record-payment/` returns `rf_catalogue`. POST adds `rf_department` (catalogue department code) and `rf_items` (`code`, positive integer `quantity`). Services are restricted to that catalogue department, fixed prices are checked server-side, and unavailable entries cannot be paid. A/E care uses first-day plus subsequent-day rates; quantities for daily, weekly, hourly and pack items use the stated unit. Existing patient discounts apply (regular full price; NHIS/IMSHIA 10% off). R/F has no Over-head surcharge.

The main payment department continues to identify the department paid for. The separate R/F service department is snapshotted in `RecordedPayment.rf_breakdown`, audit metadata and the receipt item heading alongside itemized rates and totals. Existing receipts retain their original data. Legacy manual/configured-service API requests without the new R/F fields remain compatible; the updated frontend uses the departmental catalogue flow.

Deploy both frontend and backend and apply common migration `0016_recordedpayment_rf_breakdown`. No price-list import command or database catalogue activation is required.
