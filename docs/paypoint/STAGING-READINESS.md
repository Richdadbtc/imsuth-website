# IMSUTH PayPoint staging readiness

**Assessment date:** 11 October 2026  
**Scope:** local preparation and verification only; no remote infrastructure, DNS, cPanel, SSL or public-site changes were made.  
**Decision:** **NO-GO for remote staging deployment at this time.** The application is ready to enter an authorised VPS deployment exercise, but the remote host, HTTPS endpoint and access boundary have not yet been approved or validated.

## Executive status

| Area | Status | Evidence / remaining gate |
|---|---|---|
| Application tests | Pass locally | 29/29 tests passed against PostgreSQL, including threaded payment-idempotency concurrency. |
| Synthetic end-to-end workflow | Pass locally | Registration, Patient ID, invoice, sandbox payment, signed verification, receipt, management notification, dashboard and reconciliation covered by integration test. |
| Seven roles | Pass locally | Administrator, Registration Officer, Billing Officer, Cashier, Finance Officer, Auditor and Management permission cases executed. A Django superuser no longer bypasses PayPoint financial role controls. |
| Backup/restore | Pass locally | Checksum-verified custom PostgreSQL dump restored into a new database; restored counts were 1 patient, 1 invoice, 1 payment, 1 receipt and 1 reconciliation batch. |
| Compose/config static validation | Pass | Both Compose YAML files parse; staging defines six services, split app/data networks, persistent volumes, health checks, restart policies, limits and container hardening. |
| Container runtime exercise | Not run | Docker daemon/Compose are unavailable on this workstation. The exact staging stack still requires execution on an authorised disposable VPS. |
| HTTPS and public routing | Prepared, not run | Host TLS and inner NGINX examples exist; staging hostname, certificate and allow-list have not been approved/provisioned. |
| `/paypoint/` prefix | Automated/code review pass; edge validation pending | Django prefix/cookie settings and NGINX strip/proxy rules are aligned. Login, redirects, API/schema/static/receipt URLs must be exercised through the real two-proxy staging path. |
| Device and printer UAT | Not run | Browser could not reach the workstation-local listener from its isolated runtime. Responsive and print CSS are prepared; physical/browser matrix remains a staging UAT gate. |
| Redis/Celery | Configured; runtime pending | Dedicated Redis, worker and beat services are defined and isolated on the data network. End-to-end container execution remains pending. |

## Local changes prepared for staging

- Added `backend/deployment/compose.staging.yaml`, `staging.env.example`, `nginx-staging.conf` and a host TLS reverse-proxy example.
- Secrets may be supplied through protected Docker secret files; no secret is embedded in Compose or committed examples.
- Staging has `DEBUG=false`, secure cookie controls, trusted proxy handling, HSTS, host validation and a non-production-only deterministic payment adapter.
- PostgreSQL and Redis are not published to the host. Only inner NGINX is loopback-bound (`127.0.0.1:18080`).
- Containers use explicit health checks, restart policies, CPU/memory/PID constraints, dropped capabilities, read-only filesystems where practical and `no-new-privileges`.
- Financial models are inspection-only in Django Admin. PayPoint role checks—not Django superuser status—govern financial APIs.
- Payment confirmation creates management/finance notifications. Receipt output has A4 and thermal print rules.
- Payment and invoice idempotency are rechecked after database locking, closing the concurrent duplicate race.
- A guarded synthetic staging seed command creates only clearly marked test users and records.

## Required pre-deployment gates

- [ ] Written deployment authorisation identifies the VPS, accountable system administrator and maintenance window.
- [ ] VPS inventory proves at least the approved CPU, RAM, storage and backup headroom; existing client workloads and networks are identified.
- [ ] Dedicated staging hostname approved (recommended: `paypoint-staging.imsuth.org`) and not pointed publicly yet.
- [ ] IP/VPN allow-list and separate outer basic-auth credentials approved for reviewers.
- [ ] Valid CA certificate issued for the staging hostname; TLS 1.2/1.3 and renewal monitoring configured.
- [ ] Docker Engine and Compose versions recorded and supported; staging YAML rendered and inspected on the target.
- [ ] Unique secrets generated on the VPS with restrictive permissions; examples are never used as values.
- [ ] Staging database/volumes reside in a dedicated project namespace and encrypted backup destination.
- [ ] Container stack starts healthy; restart and host-reboot behaviour is observed.
- [ ] `/paypoint/` routing matrix in the UAT plan passes through the actual edge proxy.
- [ ] Backup/restore is repeated on the staging host and recovery time recorded.
- [ ] Device/browser and receipt-printer UAT is completed.
- [ ] Security review blockers are closed or explicitly risk-accepted by the named authority.

## Safe staging operating rules

Use synthetic names and identifiers only. Keep `PAYMENT_TEST_MODE=true` and permit only the deterministic test adapter. Do not configure real bank, gateway, SMTP/SMS patient or hospital credentials. Prefix visible test data with `SYNTHETIC`/`TEST`; display a persistent staging banner; prohibit exports to production. Limit access at the host proxy in addition to application authentication. Destroy or archive staging data under an approved retention schedule after UAT.

## Recommendation

**NO-GO now for remote deployment or public exposure.** Grant **GO for a controlled deployment exercise** only after the first eight pre-deployment gates above have documentary evidence. Functional UAT may begin only after HTTPS, outer access restrictions, healthy containers and a verified staging-only database are demonstrated.
