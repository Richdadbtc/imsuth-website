# Phase J browser acceptance results

Date: 24 October 2026. Local development only. Tested through the Codex in-app browser against `http://127.0.0.1:8012/paypoint/`, backed by disposable PostgreSQL database `phase_j_uat`. All patients, staff, prices, evidence and policy limits were synthetic. No production server, banking connection, external notification or real financial operation was used.

## Accounts and method

Actual browser sessions used Super Administrator, Finance, Cashier and Department Supervisor test accounts. Additional seven-role and anonymous checks ran through Django/DRF integration tests. Browser credentials are deliberately omitted from this report. Accounts created without a password remain unable to log in until secure onboarding/recovery.

Interactions were performed with the browser's visible forms and navigation, not by injecting application state. Backend persistence was separately checked against the disposable database. Screenshots are unedited browser captures in `phase-j-evidence/`. Desktop captures are 1536px wide; mobile captures are 390px wide. A first attempted mobile capture was actually 1280px; it was discarded and replaced after measuring the DOM viewport. The saved mobile captures are 390px.

## Executed screen results

| Screen | Actual interactions and observed result | Evidence |
|---|---|---|
| Overview | Authenticated load, correct current tab, period change, server pagination 1–10 then 11–20 of 33 initial attempts, unique-reference search, zero-result search, reset, direct refresh and transaction detail dialog. Confirmed collections excluded pending attempts. Final fixture had 35 attempts and four confirmed receipts before the final retry check. | `overview-desktop.png`, `overview-mobile.png` |
| Record Payment | Empty required department validation; missing-patient search; patient selection; assigned department/service and approved ₦2,500 tariff; matching amount; online pending attempt; signed deterministic test confirmation; automatic polling changed to confirmed and displayed the real official receipt link. The receipt endpoint rendered the correct patient, item, amount and reference. A later pending attempt was explicitly rechecked with the new button; after delayed deterministic confirmation, manual retry displayed the official receipt. Administrator payment submission displayed a server authorization error; Cashier submission succeeded. Refresh reloads server payment records and clears unsaved form state. | `record-payment-desktop.png`, `record-payment-mobile.png`, `official-receipt.png` |
| Department Desk | Unknown receipt gave no-match message; verified the browser-created official receipt as Supervisor; selected its item; confirmed delivery; searched it again and refreshed: Delivered persisted and delivery controls were disabled. Pending Receipts tab showed a truthful empty state. View Receipt linked to the server-issued receipt. Assigned department selection contained only the permitted department for Cashier/Supervisor. | `department-desk-desktop.png`, `department-desk-mobile.png` |
| Departments | Server pagination over 31 initial departments; department search; details dialog; empty search/reset; created a synthetic department; refresh retained the resulting 32 departments. Correct current tab. | `departments-desktop.png`, `departments-mobile.png` |
| Services and Prices | Search/no-match/reset; next page 11–20 of 27; edited service description, category and unit and checked persistence; created a synthetic service with a future unapproved price proposal; independently approved a Finance proposal and rejected another with notes. Existing approved price stayed ₦2,500. Maker decision controls were disabled on own proposal. Correct tab; refresh retained catalogue changes. | `services-desktop.png`, `services-mobile.png` |
| Cash Points and Orders | Finance independently approved a Cashier fixture request. Created another request in the browser; self-approval returned “The requester cannot decide their own order.” Recorded evidence for a confirmed cash fixture payment, uploaded synthetic PDF, reopened record, downloaded attachment. Bank deposit remained Not certified; approval did not count as collection. Refresh showed ₦2,500 only after explicit collection evidence. | `cash-desktop.png`, `cash-mobile.png`, `cash-evidence-desktop.png` |
| Alerts | Selected critical exception; assigned Finance reviewer; saved In Review; missing resolution notes rejected; documented resolution succeeded; zero-result search/reset; refresh retained Resolved. Finance could view both synthetic departments; Supervisor scope was tested through API. Disabled Alert Settings explained its unsupported configuration endpoint. | `alerts-desktop.png`, `alerts-mobile.png` |
| Users and Audit | Reproduced silent Edit failure; after fix, edited Cashier name/email while retaining department; saved and refreshed; unique search/no-match/reset; server paging; required-name validation; created synthetic user; reloaded count rose from 29 to 30. Finance direct navigation returned Access restricted. Audit list displayed the resulting events. | `users-desktop.png`, `users-mobile.png` |

Screenshots are snapshots at different times in the same UAT run; counts can differ because approved synthetic operations occurred between captures.

## Defects reproduced and corrected

1. User Edit compared a numeric API ID to a string HTML attribute and silently did nothing. Normalize both to strings. Retest opened the editor and persisted the change.
2. User department select used department labels instead of IDs as option values. Retest preserved `JLAB` after editing.
3. Disabled service metadata fields were omitted from FormData and overwritten with empty strings. Category/unit now use supported editable API fields; saved metadata and description survived refresh.
4. Verification polling stopped after 20 checks without an explicit retry. Added Check verification status; automatic confirmed-path, late manual retry and official receipt rendering were tested.
5. Desk history retained Not recorded after successful delivery. It now uses the persisted delivery result; refresh/recheck showed Delivered.
6. Desk receipt buttons opened a client-generated detail print. Live buttons now navigate to the authenticated official receipt endpoint.
7. Cash point/officer and requester/reviewer names displayed raw IDs. Added read-only serializer names; refreshed browser showed staff/department names.
8. Top notification badge displayed five demo notifications in live sessions. It now reads the authorized unread-count endpoint. Account menu and global filter have meaningful mobile accessible names.
9. Overview/Departments previously fetched entire financial lists. Their live tables now use server filtering and bounded pages; transaction detail service summaries use prefetching.

## Keyboard and responsive verification

All eight horizontal navigation links were activated using Enter. Tab moved focus to the next link, or from Users and Audit to Add User. Each resulting tab had `aria-current="page"`. Exact observed focus results are saved in `keyboard-results.json`. This is a keyboard navigation smoke test, not a full screen-reader certification.

At 390 × 844, all eight pages measured document width = scroll width = 390px. Main panels stack, the sidebar uses the menu toggle, and tables/navigation scroll within their containers. `mobile-metrics.json` records seven screen measurements; Overview's 390/390 measurement was separately observed and captured. Desktop layouts retain the main/aside arrangement. No real phone, touch hardware, printer or QR scanner was tested.

Loading messages were observed during authenticated page loads, receipt checks and evidence fetching. Searchable screens returned explicit empty messages. Record Payment and Department Desk are workflow forms, not list editors: payment editing and a page-level payment paginator are intentionally absent. Their View All links lead to dedicated lists. Cash Points has a recent-five/View All order list and period filter, not a search/pagination control. No nonexistent control is marked tested.

## Browser limitations and remaining acceptance work

- Browser requests and success/error responses were evidenced by rendered results and persisted records; no HAR was captured. Status codes/role matrices were independently verified in integration tests.
- An early receipt-link click with a new-window target did not expose a new IAB tab. Its exact displayed URL was opened in a temporary tab; the official receipt rendered successfully. New-window behavior should also be checked in the hospital's supported browsers.
- Some immediate locator checks raced asynchronous renders. Results above were recorded only after observing the settled screen or persisted state; a timeout alone was not counted as success.
- The complete page-wide filter/form combinations, full assistive-technology audit, real devices and production-scale load have not been certified. Synthetic data covered multiple transaction, department, service and user pages; it was not a volume benchmark.
- Independent original hospital HTML and approved crest/assets remain unverified. See HOSPITAL-UI-FIDELITY-REPORT.md.
