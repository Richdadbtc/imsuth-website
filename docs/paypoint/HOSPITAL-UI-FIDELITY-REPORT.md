# Phase J hospital UI fidelity report

24 October 2026 — local review, no redesign or production deployment.

## Reference provenance

The project owner answered the reference-location question with `website/pay point`. The workspace contains `website/paypoint/`, with `index.html`, CSS, vanilla ES6 modules, images and earlier QA notes. There is no `website/pay point` directory. A filename search under `website/` found only `website/paypoint/index.html` for PayPoint/dashboard HTML. This is the actively maintained implementation, not an independently identifiable, untouched hospital-supplied dashboard export.

The eight Revenue Control screenshots supplied in the conversation establish the intended visual arrangement. They show a dark teal hospital header, eight horizontal navigation sections, pale background, blue actions, white cards, compact tables, charts and right-hand detail/forms. They are visual references, not executable instructions. Earlier PayPoint administration/report screenshots use a different sidebar shell; those are not substituted for the newer eight-section design.

**Conclusion:** compared the current implementation with the available screenshot structure and the owner-designated folder. An independent original HTML baseline is still missing. Exact/pixel-perfect fidelity is not claimed. The earlier question has been answered; this report records the artifact ambiguity rather than repeatedly requesting the same path. Hospital sign-off needs a uniquely identified original export or explicit approval of this current folder as the baseline.

## Comparison

| Element | Available reference | Observed implementation / disposition |
|---|---|---|
| Header | Teal full-width hospital crest/title and period | Teal Revenue Control header and title retained. Existing PayPoint outer toolbar/sidebar also remains; the screenshot has a simpler single shell. Documented UI mismatch; no shell redesign was undertaken in stabilization. |
| Navigation | Eight horizontal sections, underline/current state | All eight sections present with current-page indication. Actual mouse and keyboard navigation tested. Mobile navigation scrolls horizontally. |
| Typography/colors | Navy text, teal header, bright blue controls, pale blue background | Existing visual palette and type hierarchy retained; no new design system/framework introduced. No font-file or pixel measurements against an original HTML export were possible. |
| Cards | Overview five metrics, other management screens four; charts/summary beside tables | Grouping retained. Authoritative labels distinguish confirmed collection, attempts, pending and uncertified bank deposit. Synthetic runtime values deliberately differ from screenshot samples. |
| Tables | Compact financial/directory columns, status, actions, pagination | Corresponding columns and actions retained. Overview service/receipt fields restored through server data; directories use actual counts. Large transaction/department tables now paginate/filter at the server. |
| Forms | Patient/service/payment steps, desk delivery, right-side service/user/cash editors, alert action | Structure retained. User/category/unit edits repaired. Independent price approval, required decision notes and immutable financial state take precedence over illustrative one-click controls. Unsupported insurance prices and alert settings remain explicitly unavailable. |
| Charts | Donuts and departmental bars | Native CSS chart arrangement retained and fed with scoped server aggregates. No third-party chart framework introduced. Blank/zero states are truthful rather than screenshot sample values. |
| Crest/imagery | Hospital crest in the supplied screenshots | Current project image is retained. Its appearance differs from the supplied crest; an approved asset/source needs hospital confirmation. No replacement hospital image was invented. |
| Responsive layout | Desktop screenshot, no independent mobile HTML reference | Actual 1536px desktop and 390px mobile captures saved for all eight screens. Mobile content stays within document width, panels stack and wide tables scroll internally. This verifies the implementation's response, not fidelity to an unavailable mobile reference. |

## Screen evidence

Each pair is in `docs/paypoint/phase-j-evidence/`:

| Section | Desktop | Mobile |
|---|---|---|
| Overview | overview-desktop.png | overview-mobile.png |
| Record Payment | record-payment-desktop.png | record-payment-mobile.png |
| Department Desk | department-desk-desktop.png | department-desk-mobile.png |
| Departments | departments-desktop.png | departments-mobile.png |
| Services and Prices | services-desktop.png | services-mobile.png |
| Cash Points and Orders | cash-desktop.png | cash-mobile.png |
| Alerts | alerts-desktop.png | alerts-mobile.png |
| Users and Audit | users-desktop.png | users-mobile.png |

## Remaining classifications

- **UI mismatch:** independent original HTML not uniquely identified; exact typography/spacing and the outer shell require comparison/sign-off.
- **UI mismatch:** approved hospital crest file is not uniquely verified against the supplied screenshot.
- **Missing hospital policy:** actual category-specific tariffs, cash authority limits and offline verification procedures must be approved; sample screenshot values do not authorize them.
- **Hardware testing dependency:** real mobile devices, supported browser versions, thermal/A4 printing and QR/scanner behavior need hospital UAT.

Functional fixes made in Phase J do not establish hospital design acceptance. The current structure is preserved and documented for that review.
