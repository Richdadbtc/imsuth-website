# IMSUTH PayPoint Phase I — UAT results

## Overall status

**UAT status: NOT STARTED on staging.** There is no authorised HTTPS staging endpoint. Automated local evidence is recorded separately and must not be confused with hospital user acceptance.

| Area | Result | Evidence / reason |
|---|---|---|
| Staff login and recovery templates | Passed locally | Phase H rendering tests |
| Patient lookup/registration/ID | Passed locally | UI and synthetic workflow tests |
| Department/service/approved tariff | Passed locally | Billing model/API tests |
| Invoice generation | Passed locally | Server-calculated tariff and immutability tests |
| Sandbox payment initiation | Passed locally | UI and workflow tests |
| Signed verification and duplicate event | Passed locally | Payment integration tests |
| Receipt generation and uniqueness | Passed locally | Payment workflow/idempotency tests |
| Management notification/dashboard | Passed locally | Synthetic workflow test |
| Reconciliation | Passed locally | Exact-match/mismatch/duplicate-file tests |
| Audit evidence | Passed locally | Append-only audit and UI rendering tests |
| Refund/reversal maker-checker | Passed locally | Operations tests; provider execution intentionally unavailable |
| All seven roles | Passed locally | Role matrix tests; manual navigation remains pending |
| Browser/device screenshots | NOT TESTED | No protected reachable staging URL |
| Accessibility tools/screen reader | NOT TESTED | Requires running browser environment |
| Physical receipt printers | NOT TESTED | No A4/80 mm device supplied |

## Required hospital workflow script

Use unique fictional identifiers and capture tester, role, time, expected result, actual result and evidence for each step:

1. Sign in as each of the seven roles and confirm only authorised navigation/actions appear.
2. Search for a fictional patient before registration; verify useful empty/duplicate states.
3. Register a fictional patient and record the generated Patient ID.
4. Select an active department/service; verify the approved tariff is read-only.
5. Generate invoice and compare service quantity, approved rate, total and payment reference.
6. Initiate each approved test channel without connecting live money.
7. Submit valid, invalid and duplicate signed sandbox verification events.
8. Confirm one payment result, one official receipt number and correct management notification/dashboard change.
9. Print/preview A4 and 80 mm receipts; confirm navigation is absent and margins/content are readable.
10. Import synthetic settlement data, reconcile exact and mismatched entries and review discrepancies.
11. Review audit evidence and test refund/reversal maker-checker separation.

## Device and accessibility matrix

All remain **NOT TESTED** pending protected staging:

- 320 × representative height
- 375 × representative height
- 768 × 1024
- 1024 × 768
- 1440 × 900
- Keyboard-only navigation and visible focus
- Labels, validation association and live announcements
- Table headers/overflow and reading order
- Contrast analysis against WCAG 2.2 AA
- Reduced-motion behavior
- Screen-reader workflow

## Acceptance rule

Hospital UAT cannot be signed until every critical workflow, seven-role denial case, device size, accessibility check and receipt layout has evidence. Physical printing may remain NOT TESTED only if management explicitly accepts that limitation for the staging gate; it cannot be recorded as passed.
