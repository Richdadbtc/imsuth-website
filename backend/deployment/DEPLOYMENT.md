# IMSUTH PayPoint Deployment and Rollback Runbook

## Status and authorization boundary

This is a preparation artifact. It does not authorize deployment, DNS/TLS/cPanel changes, use of real patient data, live provider credentials or real payment activation.

Production remains blocked until IMSUTH approves the hosting option and operational readiness evidence. Namecheap path-level proxy capability is unverified.

## Preferred routing

Preferred, subject to provider confirmation:

1. Keep the public static website on its existing origin.
2. Run PayPoint on a dedicated hardened VPS or managed application environment.
3. Proxy only `https://www.imsuth.org/paypoint/` to the PayPoint NGINX service.
4. Restrict direct origin access and preserve `Host`, client IP and HTTPS proxy headers.

If path proxying is not available, obtain written approval for either a controlled edge migration or a dedicated staff subdomain. Do not silently change the URL or DNS.

## Required pre-deployment evidence

- Approved hosting/routing decision and infrastructure owner.
- Valid TLS at every public and origin hop, with renewal monitoring.
- Privacy/security assessment and approved production retention schedule.
- Approved role matrix, maker-checker thresholds and financial policies.
- Production database/Redis/storage design, encrypted backup and successful restore test.
- Monitoring, incident response, on-call contacts and maintenance window.
- Payment provider contracts, official integration documents and sandbox acceptance when payment integration is in scope.
- UAT with synthetic data, security test, reconciliation trial and rollback rehearsal.

## Staging procedure

1. Create a protected staging environment with separate secrets, database, Redis and provider sandbox.
2. Copy `production.env.example` to the secret-management workflow; never commit the completed file.
3. Build immutable application images from an approved commit.
4. Run `python manage.py check --deploy`, dependency checks and the full automated test suite.
5. Back up staging, run `python manage.py migrate --plan`, review the plan, then apply migrations.
6. Run `python manage.py collectstatic --noinput` and start web/worker/beat services.
7. Validate `/healthz`, login, permissions, audit events, patient/billing flows, test-provider callbacks, receipts and reconciliation.
8. Confirm the public website remains unchanged and reachable.

## Production migration procedure

Use an approved maintenance/change record. Take an encrypted backup immediately before migration. Review the migration plan and apply migrations once. Do not run concurrent migration jobs. Smoke-test with approved non-patient operational accounts only. Keep payment channels disabled until their separate activation checklist is signed.

## Monitoring

- HTTP availability and latency for `/paypoint/` and an internally protected health endpoint.
- Gunicorn 5xx/error rate, worker restarts and request saturation.
- PostgreSQL connectivity, storage, locks, slow queries, replication/backup status where applicable.
- Redis availability, queue depth and Celery failure/retry rates.
- Failed logins, permission denials, payment signature failures, duplicate callbacks and reconciliation discrepancies.
- TLS expiry, backup age, restore-test age and time synchronization.
- Alerts must avoid patient data and provider secrets.

## Backup and restore

`backup.sh` creates a PostgreSQL custom-format dump and SHA-256 checksum. Backups must be encrypted off-host, access-controlled and retained under approved policy. `restore.sh` requires an explicit `ALLOW_PAYPOINT_RESTORE=YES` guard and must first be rehearsed in an isolated environment. A backup is not accepted until restoration and application validation succeed.

## Rollback

1. Stop new staff sessions and disable payment initiation at the edge/application configuration.
2. Preserve logs and take a forensic/rollback database backup.
3. For application-only failure, route back to the last approved immutable image without reversing committed financial data.
4. For a database migration failure, prefer an approved forward-fix. Restore only when the migration/runbook owner and Finance/Security approve data-loss implications.
5. Never delete or overwrite confirmed payments, receipts or audit history to make software versions align.
6. Verify the public website, staff authentication, data totals and reconciliation state before reopening.
7. Record the incident, decision, actors, times and validation evidence.

## Unresolved external dependencies

- Namecheap/cPanel path reverse-proxy capability and TLS state.
- Production VPS/managed service selection and ownership.
- Live bank/payment-provider APIs, webhook keys, settlement formats and support contacts.
- Approved SMTP/SMS providers and notification content.
- Production RPO/RTO, backup retention, maintenance schedule and on-call model.
- Final operational policies for cash/POS, partial payments, refunds/reversals and financial close.


## 25 October 2026 — Application production checks

API contracts reverified: 133 canonical paths, 179 operations, 119 PostgreSQL tests passed, OpenAPI zero warnings/errors. Local hardening includes deployment startup checks, file-backed secrets, shared-host container isolation, explicit proxy headers and strict-CSP-compatible UI. Production candidate ingress is 127.0.0.1:18081; staging remains 127.0.0.1:18080. Actual VPS/Docker runtime, TLS, backup/restore and provider acceptance remain release gates. See [API production reconfirmation](../../docs/paypoint/API-PRODUCTION-RECONFIRMATION.md).
