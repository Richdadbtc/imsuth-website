# Deployment and operations

For cPanel GitHub automation and the required GitHub secrets, see `docs/CPANEL-DEPLOYMENT.md`.

## Required environment variables

- `IMSUTH_ALLOWED_ORIGIN=https://www.imsuth.org`
- `IMSUTH_FORM_WEBHOOK_URL` — HTTPS endpoint owned or approved by IMSUTH
- `IMSUTH_FORM_WEBHOOK_TOKEN` — secret stored only in the hosting environment

Change `forms.mode` in `data/settings.json` to `production` only after the secure receiver, retention rules and incident owner are approved and an end-to-end test succeeds.

The form endpoints require PHP 8.1 or newer with the cURL and mbstring extensions. Adjust the PHP-FPM socket in `deployment/nginx.conf.example` to match the production host. Copy the variable names from `deployment/forms.env.example` into the host's protected environment; never publish real tokens in this project.

## Pre-deployment

1. Back up the current website, database, media and DNS records.
2. Export all current URLs and approve the redirect map.
3. Confirm contact, emergency, leadership, clinical, recruitment and privacy content.
4. Confirm image rights and optimize production images.
5. Validate HTML, JSON, JavaScript, PHP and XML.
6. Test forms without real patient data.
7. Run keyboard, screen-reader, contrast and responsive checks.
8. Confirm HTTPS, security headers, CSP, backups and monitoring.
9. Obtain stakeholder approval and document rollback ownership.

## Cutover

Deploy to staging first. Freeze content, take fresh backups, apply approved redirects, deploy during the agreed window, verify DNS/TLS and smoke-test every public route. Keep the previous release available for immediate rollback.

## Post-deployment

Monitor availability, server errors, form-delivery failures, broken links and Core Web Vitals. Do not log form payloads. Review access logs and rate-limit activity without retaining unnecessary personal data.
