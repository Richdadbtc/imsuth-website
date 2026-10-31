# IMSUTH PayPoint — Next.js

PayPoint now runs as an isolated Next.js App Router application at `/paypoint`. The public hospital website and Django backend have not been converted or modified. Django remains the authority for authentication, roles, prices, financial state and audit records.

## Run locally

Requires Node.js 20.9 or newer and a running Django backend. From this directory:

```sh
npm ci
DJANGO_API_ORIGIN=http://127.0.0.1:8012 npm run dev
```

Open **http://127.0.0.1:3000/paypoint**. In a separate terminal run the existing backend from `../../backend` with its normal approved configuration:

```sh
.venv/bin/python manage.py runserver 127.0.0.1:8012
```

The existing Django staff accounts are used. No demo login, generated production accounts or fake API data is included. `DJANGO_API_ORIGIN` is server-only and must contain an HTTP(S) origin without credentials or a path. Production startup without it returns a truthful unavailable API response.

## Production build

```sh
npm test
npm run build
DJANGO_API_ORIGIN=http://127.0.0.1:8012 npm start
```

The build prepares the standalone Node server, compiled assets and public images together. It listens on `127.0.0.1:3000` by default; set `PORT` or `HOSTNAME` explicitly when deploying to an approved container environment. Node is required; this is not a static cPanel export. No VPS deployment or GitHub push was performed by this conversion.

## Structure

- `app/[[...screen]]/page.jsx`: dynamic App Router pages for the existing PayPoint screen IDs, plus login and password recovery. The former `index.html` route and hash links remain compatible.
- `components/paypoint.jsx`: React session state, permission-aware navigation, sidebar, header, inbox count, profile callbacks and logout.
- `components/auth.jsx`: React login and secure token recovery forms. No passwords/tokens are stored in browser storage. Only an opted-in staff username is remembered.
- `components/workspace.jsx`: React lifecycle boundary for the existing financial screens. Each route owns a separate DOM scope with request cancellation and observer cleanup.
- `features/`: complete retained screen controllers, bundled by Next.js as client modules. All financial forms/tables have not been rewritten into individual JSX components; their existing handlers are preserved to avoid removing working workflows. This is a Next.js application conversion, not a claim that every controller has become declarative React.
- `lib/api.js`: same-origin browser API transport with CSRF, cookies, no-store requests and session expiry handling.
- `app/api/v1/[...path]/route.js`, `lib/proxy.js`: bounded streaming Node proxy to the existing Django `/api/v1/` endpoints. It validates the browser origin on writes, routes Host/Origin to the configured API, preserves CSRF/session cookies and streams receipts, attachments and CSV exports without converting them to JSON. Redirects to another upstream origin are rejected; errors do not expose server connection details.
- `proxy.js`: per-request nonce-based CSP for Next.js hydration. Production disallows unsafe-inline scripts and unsafe-eval. Nonce pages are dynamically rendered and not shared in a CDN cache.
- `static/paypoint/*.css`: existing visual design imported into the Next.js build. Original `index.html`, static JavaScript and `config.js` remain rollback sources; Next.js does not execute them.
- `public/images/`: scoped PayPoint hospital imagery.
- `tests/`: route, API isolation, CSRF/cookie transport, binary output, upload limit and error sanitization contracts.

## Same-origin deployment boundary

Route **only `/paypoint` and `/paypoint/…`** to this Node application through the existing edge. Next.js owns `/paypoint/_next/`, frontend routes, images and `/paypoint/api/v1/`. The latter reaches Django internally. Do not route Next.js pages to the old static NGINX alias or expose PostgreSQL/Redis/Gunicorn as public frontend services.

Keep Django's exact allowed host and CSRF trusted HTTPS origin configured for the approved hostname. The edge must preserve Host and trusted HTTPS forwarding, strip untrusted proxy headers, and use an approved TLS certificate. Next.js supplies its nonce CSP: an additional inherited static `script-src 'self'` CSP would block hydration, so the future PayPoint-specific edge configuration must avoid sending a second conflicting policy. Do not loosen policies for other client sites.

This Node service adds CPU/RAM demand to the previous Django-only hosting plan. The shared Contabo VPS inventory, resource assessment, TLS, external providers, backup/restore and final deployment approval are still pending. This conversion does not activate unavailable provider/SMS/QR/2FA/backup integrations.

## Verification

See `verification/RESULTS.md` for executed checks. Build and runtime checks are local only and do not certify the uninspected VPS.

Framework references: [Next.js App Router installation](https://nextjs.org/docs/app/getting-started/installation), [nonce-based content policy](https://nextjs.org/docs/app/guides/content-security-policy).


## Vercel deployment

Import this repository as **Next.js**, with **Root Directory `.`** (the repository already contains PayPoint at its root), production branch `main`, and the default Node runtime supported by Next.js. `vercel.json` selects `npm ci`, `npm run build:vercel` and `.next` output; it redirects the domain root `/` to `/paypoint`. Do not configure this repository as a static HTML site or set the root to `website/paypoint`. The standalone packaging script is used only by the self-hosted build.

Set the server-only `DJANGO_API_ORIGIN` Vercel environment variable to the approved, publicly reachable HTTPS Django API origin. `127.0.0.1` on Vercel is the Vercel function itself, not the Contabo server. Configure Django's allowed hostname, trusted HTTPS frontend origin and secure cookies for the deployed domain. The approved production origin is configured in `vercel.json`; no backend deployment or credentials are included here.

If both `/` and `/paypoint` return Vercel's platform `NOT_FOUND`, confirm that a successful production deployment exists, its source is this repository's `main` branch, the root/framework settings above are correct, and `imsuth-paypoint.vercel.app` is attached to that deployment. A missing backend should produce a clear API-unavailable message, not a page 404.

Production API: `https://api.imsuth.site`, configured as the server-only Vercel `DJANGO_API_ORIGIN`. Browser API requests remain on `/paypoint/api/v1/`. The proxy rejects cross-origin writes before forwarding the API host, Origin and CSRF token to Django.
