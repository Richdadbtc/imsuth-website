# IMSUTH PayPoint Phase I — staging report

**Assessment date:** 11 October 2026  
**Boundary:** local validation only. No VPS credentials, deployment authorisation, DNS approval or target-host inventory were available. No remote or public system was changed.

## Result

**Staging URL:** Not deployed. `https://staging-paypoint.imsuth.org/paypoint/` remains a proposed URL only.  
**Recommendation:** **NO-GO for hospital staff testing.** Local preparation is suitable for an authorised deployment rehearsal, but there is no protected running staging environment on which browser, accessibility, restart and staff UAT can be evidenced.

## Prepared architecture

The preferred architecture is a dedicated Compose project on an authorised VPS:

```text
Approved reviewer network/VPN
  -> HTTPS host NGINX + allow-list + basic authentication
  -> 127.0.0.1:18080
  -> isolated staging NGINX at /paypoint/
  -> Gunicorn/Django
  -> internal-only PostgreSQL and Redis
  -> isolated Celery worker and beat
```

Staging uses separate named volumes, networks, database, Redis, secrets and credentials. Database and Redis have no host-published ports. Inner NGINX is loopback-bound. Resource/PID limits, health checks, restart policies, read-only filesystems, dropped capabilities and `no-new-privileges` are defined.

## Local preparation completed

- Standardised every staging artifact on proposed hostname `staging-paypoint.imsuth.org`.
- Corrected README test-adapter guidance: staging requires a non-production environment, explicit test mode and a protected webhook secret; it does not require debug mode.
- Rebuilt the production-style static manifest after Phase H introduced `app.js`.
- Parsed production and staging Compose YAML successfully; staging contains web, worker, beat, NGINX, PostgreSQL and Redis on separate app/data networks.
- Validated backup/restore shell syntax and confirmed no obsolete staging hostname remains.
- Preserved synthetic-data-only, no-live-payment and no-public-website-change boundaries.

## Test evidence available

- Latest completed isolated regression run: **34 passed, 1 PostgreSQL-only test skipped** using the test settings.
- Earlier staging-readiness PostgreSQL run: **29 passed**, including concurrent payment idempotency and clean teardown.
- Earlier checksum backup/restore drill: passed with one synthetic patient, invoice, payment, receipt and reconciliation batch restored.
- Phase I production-style PostgreSQL attempt identified a missing static manifest entry for the new Phase H JavaScript. Static assets were rebuilt successfully.
- The clean PostgreSQL retry did not reach test execution because the local PostgreSQL service became unresponsive/contended while another unrelated test process was active. It was stopped and is **NOT PASSED** for Phase I.

## Not executed

- Target VPS resource/container/network/port/security inventory
- SSH and deployment permission verification
- Actual Compose build/start/health/restart test
- Redis/Celery recovery and queued-task behavior
- HTTPS certificate issuance, renewal and external TLS inspection
- Real `/paypoint/` two-proxy routing verification
- Genuine browser screenshots and device matrix
- Automated accessibility scan, screen reader and complete keyboard walkthrough
- Physical A4 or thermal receipt printing
- Target-host backup/restore and measured recovery time

## Exact deployment prerequisites

1. Written approval naming the staging VPS, change window, infrastructure owner and rollback authority.
2. SSH access for a dedicated non-root deployment account with narrowly scoped Docker/NGINX permissions.
3. VPS evidence: CPU, RAM, disk/inodes, operating-system patch state, firewall, occupied ports, running containers, Docker networks, PostgreSQL/Redis instances and existing client workload headroom.
4. Approved DNS ownership for `staging-paypoint.imsuth.org` and permission to issue a CA certificate.
5. Approved reviewer IP/VPN ranges and separate outer basic-auth accounts.
6. Protected staging secrets generated on the target host; no example value may be reused.
7. Encrypted off-host backup destination, retention, RPO/RTO and restore authority.
8. Named Finance, Security, Privacy, System Administration and UAT approvers.

Only after these are supplied should the deployment checklist be executed.
