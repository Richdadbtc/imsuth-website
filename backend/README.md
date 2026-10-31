# IMSUTH PayPoint

Isolated Django application for IMSUTH patient registration, billing, payment tracking, receipts, revenue controls and reconciliation.

The static PayPoint UI is maintained separately under `../website/paypoint/` using HTML, CSS and vanilla JavaScript. It communicates with this backend through authenticated `/api/v1/` endpoints; financial and access-control logic remains in Django.

## Local development

1. Copy `.env.example` to `.env` and replace every local placeholder.
2. Start the services with a Compose-compatible runtime: `docker compose up --build`.
3. Apply migrations inside the web container: `python manage.py migrate`.
4. Create an initial administrator through the controlled local console only.
5. Open `http://localhost:8000/api/docs/` for the API documentation.

Only generated synthetic data is permitted. The deterministic payment adapter is disabled unless the environment is non-production, `PAYMENT_TEST_MODE=true`, and a protected test-webhook secret is configured; it must never be enabled in production.

## Local verification

```text
DJANGO_SETTINGS_MODULE=config.settings_test .venv/bin/python manage.py test apps
.venv/bin/python manage.py makemigrations --check --dry-run
.venv/bin/python manage.py check
```

## Production boundary

The deployment files are preparation artifacts. They have not been applied to Namecheap, DNS, TLS, a VPS or the public IMSUTH website. Review `deployment/DEPLOYMENT.md` before any staging or production action.

### Staff password recovery

Apply the accounts recovery migration before enabling the recovery flow:
`python manage.py migrate`.

Set `PASSWORD_RECOVERY_URL` to the trusted HTTPS PayPoint frontend URL (without
query parameters or a fragment), and configure the SMTP email backend and sender.
Recovery delivery deliberately refuses console/file email backends so reset
secrets do not appear in server output. The default unset URL disables delivery
while preserving the same generic response. Demo mode previews the screens only.

Recovery links expire after ten minutes. Only SHA-256 token digests are stored;
password reset consumes all outstanding challenges for the user and invalidates
existing Django sessions through the changed authentication hash. Request limits
are enforced per identifier and per direct client address using database rows;
verification and completion are also limited by address. Configure the trusted
reverse proxy to pass the correct client address to Django. Do not enable request
body capture in proxies/APM for session or recovery endpoints. Tokens are carried
in the frontend URL fragment, then removed from browser history.


## Backend-only repository

This repository contains the contents of the backend directory at its root. Frontend source, local databases, uploads, environment secrets, virtual environments and collected static output are excluded.

The API works without a sibling website checkout. If the separately maintained PayPoint frontend is available, set `PAYPOINT_FRONTEND_STATIC_DIR` to its `static` directory before collecting assets. The Django HTML shell at `/paypoint/` requires those frontend assets; this backend-only repository does not bundle them. API consumers can use `/api/v1/` or `/paypoint/api/v1/` independently.

The Revenue Control increment adds department service delivery, cash points/orders/evidence, alert management, tariff proposals and user/audit aliases. Apply migrations before enabling these APIs. No production bank verification or insured-category policy is supplied. Cash approval limits have no defaults and require an approved management policy.

Verification at publication: 48 focused PostgreSQL tests passed, including payment, service-delivery and cash-limit concurrency checks. The full suite still contains 23 pre-existing errors referencing removed legacy Django page routes; this is not a production-readiness certification.


## Live frontend and local API

See [Live UI connections](../docs/paypoint/LIVE-UI-CONNECTIONS.md) for connected workflows, local startup and verification. The port 5500 entry point requires `backend/dev_proxy.py` alongside Django on port 8012; it no longer uses demo responses.
