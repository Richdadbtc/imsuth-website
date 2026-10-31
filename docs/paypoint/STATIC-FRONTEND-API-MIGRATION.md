# PayPoint static frontend and API migration

## Result

The active PayPoint interface is now a framework-free static application under `website/paypoint/`:

- `index.html` contains the accessible application shell and staff login interface.
- `static/paypoint/frontend.css` contains static-frontend layout additions.
- `static/paypoint/frontend.js` implements navigation, authenticated data loading, filtering and UI feedback using ES6 modules.
- `static/paypoint/api.js` is the single API client and applies same-origin credentials and CSRF headers.
- `config.js` defines the non-secret API base path.

No Django template syntax exists in the active static frontend. The prior Django templates are retained only as migration evidence under `docs/paypoint/legacy-django-ui/` and are not present in the Django template search path.

## Backend boundary

Django remains authoritative for authentication, roles, permissions, validation, billing, payments, approvals, reconciliation and audit behavior. The active application routes expose JSON APIs rather than PayPoint HTML pages.

New session-facing endpoints:

- `GET /api/v1/session/`
- `POST /api/v1/session/login/`
- `POST /api/v1/session/logout/`
- `GET /api/v1/dashboard/`

Existing patient, catalogue, invoice, payment, receipt, approval and reconciliation endpoints remain under `/api/v1/` with their server-side permissions.

## Deployment boundary

The intended public arrangement is:

```text
/paypoint/          static HTML, CSS and JavaScript
/paypoint/api/      reverse proxy to Django /api/
```

Session cookies and CSRF protection require the UI and API to be presented through the same approved HTTPS origin. `config.js` contains no secret and must point only to the approved API route.

## Verification

- Django system check: pass.
- CSRF-protected login/session/logout API test: pass.
- Authenticated dashboard API test: pass.
- Anonymous dashboard rejection test: pass.
- JavaScript syntax: pass.
- Active PayPoint UI scan for Django template delimiters: pass (none found).
- Compose YAML parsing: pass.

