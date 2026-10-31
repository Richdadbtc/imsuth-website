# PayPoint Next.js conversion verification

Date: 26 October 2026 (Africa/Lagos).

Scope: only `website/paypoint/`. Django, public website source, DNS and VPS settings remain unchanged. Original static entry point retained for rollback. No push/deployment requested or performed.

## Automated checks

- Next.js 16.4.3 / React 19.3.1, pinned with package-lock.
- Production App Router build passed; frontend pages and API proxy are dynamic, standalone assets packaged.
- 12 Node contract tests passed, including an actual HTTP transport check of original Host, Origin, CSRF and distinct session cookies. A real-browser CSRF failure uncovered the need to preserve Host at the HTTP transport layer; the final transport uses Node HTTP(S) with TLS verification enabled.
- npm production dependency audit reported zero vulnerabilities when checked locally. This is a point-in-time registry result, not a security certification.
- No framework or API configuration secret is exposed through NEXT_PUBLIC variables.

## Browser acceptance

Executed against the optimized standalone build, with the strict production nonce CSP active:

- Finance and administrator sign-in and logout succeeded through the Next API proxy with Django CSRF checks enabled.
- App Router client navigation retained the authenticated shell; direct URL reloads also worked.
- Registered a synthetic patient through the migrated form and confirmed the saved record appeared in the directory after navigation (IMSUTH-2026-000002 in the isolated UAT database).
- Record Payment loaded actual patient/service/payment data and current tariff choices; no real payment was submitted.
- Nineteen administration, finance, report, profile and support routes displayed expected headings without API error panels. See `browser-routes.json` for the exact routes.
- Password recovery fragment routing reached Verify Your Identity and removed the synthetic token from the URL. No password was changed.
- Final browser console warning/error collection was empty; live charts rendered under the nonce-based content policy. Screenshot: `next-overview.png`.

Authentication testing used a newly created synthetic SQLite UAT database outside the repository, separate API/frontend ports and synthetic-only accounts. The operational development database was not seeded or changed. No external provider, SMTP delivery or VPS was used.

## Limits

The existing financial page controllers remain scoped client modules inside React lifecycle boundaries. Login/recovery/navigation/session and routing are native React/App Router. Preserving those controllers keeps current screen behavior; this does not claim every financial table/form is individually rewritten into JSX.

Container images were not started locally; the shared VPS remains uninspected and deployment requires its own authorized stage.

## Local entry point

The Next.js app is available at http://127.0.0.1:3000/paypoint with the existing development Django API on port 8012. The old port 5500/static entry point was not replaced or deployed; use the Node app's entry point for the conversion. Original static code is retained for rollback, not loaded as script tags by Next.js.

Final production login and same-origin session API both returned HTTP 200 on port 3000. The final login screenshot is `next-login.png`; its browser console warning/error collection was empty. Temporary UAT frontend/API servers were stopped after verification; the main development API and Next.js app remain running.
