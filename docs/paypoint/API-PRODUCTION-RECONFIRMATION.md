# API reconfirmation and production application checks

Date: 25 October 2026. Scope: local application/configuration changes only; no VPS, DNS, certificate or external provider changes.

## Result

**Application APIs intact; deployment approval still NO-GO pending infrastructure and external-service verification.** The validated canonical OpenAPI schema exposes **133 paths / 179 operations** under `/api/v1/`. The browser alias `/paypoint/api/v1/` resolves to the same handlers/actions. See [machine-readable inventory](API-AVAILABILITY.json).

The full PostgreSQL regression passed **119 tests**, including endpoint namespace/action resolution, anonymous access denial, authenticated collections for super administrator/finance/cashier/department supervisor, all seven Revenue Control metrics, all eleven report types, payment idempotency, maker-checker/department controls and the previous live UI contracts. These tests confirm registered routes and covered behavior; they do not prove external provider availability or every possible input/role combination.

OpenAPI validation with `--validate --fail-on-warn` passed with **zero warnings/errors**. Documentation emits canonical paths once rather than duplicating both aliases. Syntax checks, migration drift check and static collection passed. No operational database rows were deleted.

## Dynamic UI and safeguards

The active frontend continues to use authenticated backend responses and server-calculated financial values. Demo responders remain removed. Existing empty/loading/error states remain; unsupported integrations do not report false success. Password forms now match the server's 12-character minimum. Expired sessions using DRF's anonymous 403 response return to login without treating permission denials as successful requests.

A browser rehearsal used the separate synthetic UAT database through a temporary local proxy with the exact restrictive production content policy. Login, authenticated API loading, summary totals, current transactions, chart colors/gradients and bars rendered; browser warning/error logs were empty. No live provider transaction occurred. Screenshot: `live-ui-evidence/production-csp-overview.png`. Other workflow acceptance evidence remains in [Live UI connections](LIVE-UI-CONNECTIONS.md).

## Changes made

- Added deployment system checks for debug mode, strong secrets, PostgreSQL, explicit hosts/HTTPS origins, secure cookies/redirects, non-eager Celery, production test-mode prohibition and recovery delivery configuration. Container application processes run checks before serving requests or consuming jobs; startup stops on errors.
- Staging/production default debug is off. All checks can be repeated with `python manage.py check --deploy` against actual deployment secrets/configuration.
- Externalized Django shell configuration so self-only script policy works without unsafe-inline. Chart values are applied through CSSOM rather than HTML style attributes, retaining the strict style policy.
- Supplied the NGINX proxy include explicitly, retained HTTPS forwarding, rate limits and security headers, and added the root-to-application redirect.
- Production Compose now has dedicated data networks/volumes, unpublished database/Redis ports, loopback ingress, non-root application processes, memory/CPU/PID limits, restrictive application filesystems/capabilities and bounded container logs. Its candidate loopback port is **18081**, staging **18080**; neither is verified free on Contabo.
- Both environments use file-backed Django/PostgreSQL secrets. Excluded deployment secret files from Docker build context and Git. Deployment examples do not contain actual credentials.
- Prepared the Celery schedule volume's directory ownership in the image and fixed the invalid hostname-style Gunicorn proxy IP setting. Django handles the explicitly trusted HTTPS header behind the isolated edge.
- Database health failures return a sanitized 503 and no-store header rather than exposing connection details.

## Verification limits / remaining release gates

1. A production settings rehearsal produced **zero errors and two Django warnings**, W005/W021, because HSTS includeSubDomains and preload remain intentionally false. Do not enable either across client/domain infrastructure without the domain owner's policy decision. These warnings are visible and were not silenced; the warnings-as-errors run does not pass.
2. Docker CLI exists locally but the Compose plugin and daemon are unavailable. Compose files were parsed/reviewed, but images, NGINX startup, container resource enforcement, database volume permissions and the full container stack have **not** been runtime-certified. Run these on an approved isolated test environment before deployment.
3. The Contabo SSH target/access, resource inventory and co-tenant impact remain unknown. [Contabo audit](CONTABO-VPS-AUDIT.md) remains NO-GO. Do not assume the candidate ports, networks or directories are free.
4. No production SMTP/payment provider/SMS/QR/2FA/backup service has been invented or activated. Recovery remains unavailable until an approved HTTPS recovery URL and delivery backend are configured. Live provider readiness requires credentials, official sandbox integration/acceptance and explicit activation.
5. Complete dependency/image vulnerability checks, immutable digest approval, representative concurrency/load tests, encrypted off-host backup/restore rehearsal, TLS/renewal/access-control verification and hospital UAT against the final deployment artifacts.
6. No production deployment, GitHub push, live financial operation or existing-client restart was performed.

## Repeatable validation

From `backend/`, using an approved disposable PostgreSQL test database:

```sh
.venv/bin/python manage.py test --settings=config.settings_test --noinput
.venv/bin/python manage.py spectacular --validate --fail-on-warn --file /tmp/paypoint-openapi.yaml
.venv/bin/python manage.py makemigrations --check --dry-run
.venv/bin/python manage.py check --deploy --fail-level ERROR
.venv/bin/python manage.py collectstatic --noinput
```

Supply database/configuration via the approved secret workflow; never paste credentials into reports or shell history. For later isolated container verification, `docker compose ... config --quiet` avoids printing resolved secrets. Review and build only the IMSUTH project. Never use host-wide prune/stop/restart commands.
