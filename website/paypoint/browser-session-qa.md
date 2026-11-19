# Browser session handling

The shared API client now updates its CSRF token from page-level session checks as well as login bootstrap. Malformed or unreadable JavaScript cookies fall back to the same-origin session endpoint. Browser cookies are still required for authentication; this does not bypass blocked cookies, CSRF checks, role permissions or page access.

Network failures display an actionable message. Writes with an uncertain outcome are not retried automatically; check existing records before repeating them. Only an explicit Django CSRF rejection receives the existing single token-refresh retry.

Automated tests cover token rotation during page-level session checks, malformed cookie encoding, denied JavaScript cookie access, Firefox-style network errors, and write retry limits. A live unauthenticated session check returned 200 on www.imsuth.site; the apex host redirects.

The reported Firefox-only failure was not reproduced on an affected laptop, and no actual user account was created during this verification. If it persists, collect only the failing request path, HTTP status, response error text and Firefox version; do not collect passwords, cookies, tokens or request bodies. Use https://www.imsuth.site/paypoint consistently and allow this site's session cookies.

Frontend-only deployment; no backend migration is needed.
