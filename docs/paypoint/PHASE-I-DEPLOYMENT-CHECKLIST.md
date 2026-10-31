# IMSUTH PayPoint Phase I — deployment checklist

Do not execute this checklist until a signed change/deployment authorisation identifies the VPS and accountable owners.

## Gate 1 — authority and target

- [ ] Sponsor authorises synthetic-only staging and confirms no live payment activation.
- [ ] System Administration identifies VPS, service account, SSH method and maintenance window.
- [ ] Existing client services, containers, ports, networks, databases and Redis instances are inventoried.
- [ ] CPU/RAM/disk/inodes and at least 30% operational headroom are evidenced.
- [ ] Security approves hostname, reviewer allow-list/VPN, outer authentication and firewall rules.
- [ ] DNS owner approves proposed `staging-paypoint.imsuth.org`; do not create records before approval.

## Gate 2 — host preparation

- [ ] Supported patched Docker Engine and Compose installed; versions recorded.
- [ ] Dedicated non-root service user/project directory created with restrictive permissions.
- [ ] Only authorised SSH sources accepted; Docker socket not exposed to containers.
- [ ] Unique Compose project name, networks, volumes and backup directory selected.
- [ ] Log rotation, time sync, disk/health monitoring and alert contacts configured.

## Gate 3 — secrets and TLS

- [ ] Generate unique Django, PostgreSQL and test-webhook secrets on the host.
- [ ] Confirm secret file ownership/mode; scan repository/rendered Compose/logs for leakage.
- [ ] Issue valid CA certificate for the approved hostname and configure TLS 1.2/1.3.
- [ ] Configure and test renewal; record expiry alert owner.
- [ ] Create unique outer-auth reviewer accounts and approved IP/VPN rules.

## Gate 4 — deployment

- [ ] Record approved commit/image digest and rollback image.
- [ ] Render Compose configuration and inspect ports, networks, mounts, limits and secret references.
- [ ] Start PostgreSQL/Redis, confirm health and no public listeners.
- [ ] Review migration plan; back up; apply migrations once.
- [ ] Run `collectstatic --noinput` before starting/health-checking web and NGINX.
- [ ] Start web, worker, beat and NGINX; confirm all six services healthy.
- [ ] Verify only 80/443 are externally reachable and port 18080 is loopback-only.

## Gate 5 — security/routing

- [ ] HTTP redirects to HTTPS; certificate chain/hostname/protocols pass inspection.
- [ ] Anonymous network sources and users are denied.
- [ ] `/paypoint/` login, redirects, static assets, API, OpenAPI, receipts and logout preserve prefix.
- [ ] Session/CSRF cookies are Secure, correctly scoped and have approved SameSite/HttpOnly behavior.
- [ ] Missing/invalid CSRF, host and webhook signatures fail safely.
- [ ] Rate limits affect abusive traffic without blocking normal reviewers.
- [ ] `/healthz` exposes no secret or record data; internal services/tools are unreachable publicly.

## Gate 6 — reliability and recovery

- [ ] Run full PostgreSQL suite including patient, invoice and payment concurrency cases.
- [ ] Test duplicate webhook and concurrent payment verification/receipt generation.
- [ ] Test reconciliation duplicate-file/idempotency behavior.
- [ ] Restart each container and reboot host; verify recovery/no duplicate financial effects.
- [ ] Create encrypted backup, verify checksum, restore to a new database and measure RTO.
- [ ] Finance validates restored synthetic invoice/payment/receipt/reconciliation references.

## Gate 7 — UAT and sign-off

- [ ] Complete full fictional-patient workflow for all seven roles.
- [ ] Capture genuine screenshots at 320, 375, 768, 1024 and 1440 widths.
- [ ] Complete automated accessibility scan, keyboard and screen-reader checks.
- [ ] Inspect A4 and 80 mm print preview; record physical printer as PASSED or NOT TESTED.
- [ ] Close Critical/High findings and obtain risk acceptance for residual Medium findings.
- [ ] Finance, Privacy, Security, System Administration and UAT lead sign the evidence pack.

## Stop conditions

Stop and remove reviewer access if real patient data/live credentials appear, another client service is affected, a database/Redis port is public, HTTPS/access restriction fails, financial idempotency fails, audit evidence is missing, or rollback/restore cannot be demonstrated.
