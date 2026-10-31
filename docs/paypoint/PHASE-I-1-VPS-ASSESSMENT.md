# IMSUTH PayPoint Phase I.1 — VPS infrastructure readiness assessment

**Assessment date:** 11 October 2026  
**Scope:** Read-only infrastructure readiness and local configuration review  
**Decision:** **NO-GO** for deployment or hospital UAT on the intended VPS

## Executive conclusion

No authorised PayPoint VPS hostname, IP address, SSH account, SSH approval record, maintenance window or infrastructure owner is present in the repository or supplied project material. The GitHub workflow references inaccessible cPanel secrets for the public static website; those values neither identify the intended VPS nor authorise PayPoint access. No remote connection was attempted.

The local staging design provides a sound isolation baseline, but the actual VPS capacity, co-tenants, Docker state, ports, firewall, NGINX, TLS, backup arrangements and resource headroom remain unknown. Deployment and reviewer access therefore remain blocked.

## Evidence reviewed

- Phase I staging, UAT and security reports
- Phase I deployment checklist
- PayPoint deployment and rollback runbook
- Staging Compose, environment and both NGINX configuration examples
- Dockerfile and Gunicorn configuration
- Local PostgreSQL processes, readiness, configuration and server log
- Local filesystem capacity and concurrent test processes

No production system, container, NGINX file, firewall, DNS record, certificate or remote service was modified.

## Infrastructure inventory

### Intended VPS

| Item | Observed result | Status |
|---|---|---|
| VPS identity and provider | Not supplied | Blocking |
| Written inspection authorisation | Not supplied | Blocking |
| SSH hostname/IP, port and user | Not supplied | Blocking |
| SSH key/account approval | Not supplied | Blocking |
| Operating system and kernel | Unknown | Blocking |
| CPU, RAM, disk and inodes | Unknown | Blocking |
| Docker Engine/Compose | Unknown | Blocking |
| Running containers, networks and volumes | Unknown | Blocking |
| Host NGINX and occupied routes | Unknown | Blocking |
| Listening ports and firewall | Unknown | Blocking |
| TLS manager and renewal ownership | Unknown | Blocking |
| Monitoring, log rotation and time sync | Unknown | Blocking |
| Backup destination, retention and restore evidence | Unknown | Blocking |

### Local configuration inventory

The staging Compose project defines six services: Django/Gunicorn web, Celery worker, Celery beat, PostgreSQL 17, Redis 8 and inner NGINX. It defines three dedicated persistent volumes and two project networks.

| Control | Configuration result |
|---|---|
| External container port | Only inner NGINX, bound to `127.0.0.1:18080` |
| PostgreSQL/Redis exposure | No host-published ports |
| Network split | `app` plus Docker-internal `data` network |
| Persistent data | Separate PostgreSQL, Redis and Celery beat volumes |
| Container hardening | Read-only filesystems where practical, dropped capabilities, `no-new-privileges`, PID/resource limits |
| Restart policy | `unless-stopped` on all services |
| Health checks | Web, PostgreSQL and Redis; inner NGINX depends on healthy web |
| Secrets | File-backed Django, PostgreSQL and test-webhook secrets |
| TLS/access edge | Host NGINX example with TLS, network allow-list and independent basic authentication |
| Application prefix | `/paypoint/` through the two-proxy design |

## Resource assessment

The Compose ceilings total approximately **6 vCPU shares** and **2.875 GiB memory**:

| Service | CPU ceiling | Memory ceiling |
|---|---:|---:|
| Web | 1.5 | 768 MiB |
| Celery worker | 1.0 | 512 MiB |
| Celery beat | 0.5 | 256 MiB |
| Inner NGINX | 0.5 | 128 MiB |
| PostgreSQL | 2.0 | 1 GiB |
| Redis | 0.5 | 256 MiB |

These are limits, not proof of actual utilization. CPU limits may be oversubscribed, but co-tenant capacity must be measured during representative UAT.

### Initial sizing estimate — not load-tested

- Preferred minimum for a shared but demonstrably isolated staging VPS: **4 vCPU, 8 GiB RAM and 80 GiB SSD**, plus encrypted off-host backup capacity.
- Maintain at least **30% sustained RAM and filesystem headroom**, including existing clients, Docker images, logs, backups and database growth.
- Require at least **20 GiB free local disk before deployment** and alert before either disk or inode use reaches 75%; the final threshold belongs to System Administration.
- A smaller host must not be accepted from estimates alone. It requires measured baseline utilization, load testing and written risk acceptance.
- Prefer a separate VPS when existing applications cannot be assigned independent limits, networks, volumes, backups and rollback ownership.

No concurrency or load test has validated these estimates on the target VPS.

## Security and interference findings

### Blocking findings

1. **Unknown co-tenancy:** existing client workloads and their peak CPU, memory, storage I/O and restart requirements are unknown.
2. **Unknown port/routing ownership:** ports 80/443 and loopback port 18080 have not been inventoried. Host NGINX route precedence is unknown.
3. **Unknown Docker namespace:** project names, network subnets and volume names may conflict without an actual host inventory.
4. **Unknown external exposure:** firewall, provider security groups, IPv6 exposure and Docker-created packet-filter rules have not been inspected.
5. **Unknown TLS lifecycle:** certificate manager, renewal hooks, expiry alerts and ownership are unidentified.
6. **Unknown backup safety:** no encrypted off-host destination, retention, RPO/RTO or restore authority is approved.
7. **Docker privilege risk:** membership in the Docker group is effectively root-equivalent; SSH access alone is not deployment authorisation.
8. **Reviewer boundary absent:** VPN/approved IP ranges, individual outer-auth accounts and expiry/revocation process are not decided.

### Local configuration cautions

- Set a unique Compose project name such as `imsuth-paypoint-staging`; do not rely on the directory-derived default.
- Confirm Docker actually enforces the declared limits with the installed Compose version.
- Pin deployable images by approved digest after build/review; floating base tags reduce reproducibility.
- Do not put the deployment account in an unrestricted shared operations group without Security approval.
- Validate host NGINX preserves the complete request URI and `/paypoint/` redirects before reviewer access.
- Protect `/healthz` at the host boundary or restrict it to monitoring sources.
- Configure Docker and NGINX log rotation before starting UAT.

## Recommended staging topology

```text
Approved reviewer VPN/IP ranges
  -> host firewall/security group: 22 from admin ranges, 80/443 as approved
  -> host NGINX: TLS + allow-list + separate basic-auth accounts
  -> 127.0.0.1:18080
  -> dedicated PayPoint inner NGINX on project app network
  -> Django/Gunicorn web
       -> Docker-internal data network
          -> dedicated PostgreSQL
          -> dedicated Redis
       -> dedicated Celery worker and beat
  -> separate named volumes
  -> encrypted off-host backup destination
```

Required isolation boundaries are a dedicated non-root Unix account/project directory, unique Compose project name, separate secrets, networks, database, Redis, volumes, logs and backup path. Database and Redis must remain unpublished. The public IMSUTH website and every existing client application must retain independent routing and rollback.

## Exact read-only manual assessment commands

An authorised administrator should run these on the named VPS and provide the output through an approved secure channel. Review output for secrets before sharing. Do not run these commands until written inspection authority identifies the target and account.

```sh
# Identity, OS and time
hostnamectl 2>/dev/null || hostname
uname -a
cat /etc/os-release
date -Is
timedatectl status 2>/dev/null || true

# Capacity and current utilization
nproc
lscpu
free -h
uptime
df -hT
df -ih
lsblk -o NAME,SIZE,FSTYPE,MOUNTPOINTS
ps -eo pid,user,%cpu,%mem,etime,comm --sort=-%cpu | head -n 30
ps -eo pid,user,%cpu,%mem,etime,comm --sort=-%mem | head -n 30

# Docker runtime and inventory — no inspect output containing environment values
docker version
docker compose version
docker info --format 'Root={{.DockerRootDir}} Driver={{.Driver}} CPUs={{.NCPU}} Memory={{.MemTotal}} Logging={{.LoggingDriver}}'
docker ps --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}'
docker stats --no-stream --format 'table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}\t{{.PIDs}}'
docker network ls
docker volume ls
docker system df

# Network listeners and host routing
ss -lntup
ip -brief address
ip route
nginx -v 2>&1
sudo nginx -T 2>&1 | sed -E 's/(Authorization:|password|secret|token|key)[^;]*/\1 [REDACTED]/Ig'

# Firewall — use whichever manager is installed
sudo ufw status verbose 2>/dev/null || true
sudo firewall-cmd --list-all 2>/dev/null || true
sudo nft list ruleset 2>/dev/null || true

# TLS management metadata; do not print private keys
command -v certbot || true
sudo certbot certificates 2>/dev/null || true
systemctl list-timers --all | grep -Ei 'certbot|acme|letsencrypt' || true
find /etc/letsencrypt/live -maxdepth 2 -name fullchain.pem -print 2>/dev/null

# Services, startup and recent failures
systemctl --failed
systemctl list-units --type=service --state=running
journalctl -p warning --since '24 hours ago' --no-pager | tail -n 200

# Backup discovery: metadata only
systemctl list-timers --all | grep -Ei 'backup|snapshot|restic|borg|pg_dump' || true
find /etc/cron.d /etc/cron.daily /etc/cron.weekly -maxdepth 1 -type f -print 2>/dev/null
```

If `sudo` is not authorised, omit those commands and record the affected controls as unverified. Do not export container environments, secret files, private keys, database rows or application data.

## Deployment prerequisites

1. Written authorisation naming the VPS, inspection/deployment accounts, scope, change window, infrastructure owner and rollback authority.
2. Completed read-only inventory showing no conflicts and at least 30% headroom after the estimated PayPoint allocation.
3. Security-approved hostname, DNS owner, TLS issuance/renewal owner, VPN/IP allow-list and individual outer-auth accounts.
4. Unique secrets generated on the host through the approved secret workflow.
5. Approved immutable commit/image digest, Compose project name, project directory, volumes and backup path.
6. Encrypted off-host backup, retention, RPO/RTO, restore owner and a scheduled restore exercise.
7. Monitoring for availability, resource saturation, disk/inodes, container health, PostgreSQL, Redis/Celery, TLS expiry and backup age.
8. Approved synthetic-data UAT roster and signed confirmation that live patient records, money and provider credentials remain prohibited.

## Controlled deployment sequence

This is a plan, not authorisation:

1. Record baseline host inventory, existing service health and routing; stop if headroom or ownership is unclear.
2. Obtain the approved commit/image digest and verify configuration locally without secrets.
3. Create the isolated account, directories, secrets, networks and volumes during the authorised window.
4. Render Compose configuration and review ports, mounts, limits, networks and secret references.
5. Start only the dedicated PostgreSQL and Redis services; confirm health and absence of public listeners.
6. Take/verify the initial staging backup baseline, review migrations, then apply migrations once.
7. Collect static assets; start web, worker, beat and inner NGINX.
8. Test locally through `127.0.0.1:18080` before adding host routing.
9. Add the separately approved TLS/access-controlled host route; validate denial from unapproved sources.
10. Run PostgreSQL, idempotency, restart, backup/restore, security, browser/accessibility and synthetic UAT gates.
11. Invite reviewers only after Critical/High findings are closed and accountable owners sign the gate.

## Rollback strategy

- Record the existing host NGINX checksum/configuration and client application health before any later approved change.
- If PayPoint containers cause contention, security exposure or client impact, close reviewer ingress first and stop only the dedicated PayPoint Compose project under rollback authority.
- Remove only the approved PayPoint host route after configuration validation; never restart unrelated containers as part of PayPoint rollback.
- Preserve PayPoint volumes, logs and audit evidence. Do not delete or rewrite confirmed synthetic transactions to achieve rollback.
- Revert the application to the last approved immutable image. Prefer a database forward-fix; restore only with the named database, Finance and Security owners.
- Verify every pre-existing client application and public website route against the baseline before closing the change.
- DNS/TLS changes require their own rollback records and owners.

## Phase I PostgreSQL contention investigation

### Observed evidence

- The stale PayPoint test process remained blocked for more than 16 minutes; its PostgreSQL backend was idle in a transaction and later performing an insert after client termination.
- A separate test suite was concurrently running against the same local PostgreSQL service.
- The test database already existed during one retry and had multiple sessions, preventing clean teardown/recreation.
- PostgreSQL stopped responding to readiness probes during the investigation.
- Server logs show checkpoints taking approximately **152 to 301 seconds**, delayed/cancelled autovacuum workers and multi-second file synchronization.
- The local data filesystem was **96% used**, with approximately **9.4 GiB available**.

### Conclusion

The interruption is consistent with local storage-I/O pressure plus concurrent test activity and stale database sessions, not a demonstrated PayPoint application failure. It is also not a pass. Only the stale PayPoint client process started by this work was terminated; the unrelated test process and PostgreSQL service were not stopped or modified.

### Required clean-rerun conditions

1. The unrelated PostgreSQL test workload has completed and no unexpected sessions use the PayPoint test database.
2. PostgreSQL readiness and a simple query respond promptly and logs show normal checkpoint behavior.
3. Safe disk headroom is restored by the workstation owner; no files should be deleted automatically for this purpose.
4. The disposable PayPoint test database is removed only through the normal Django test teardown or with explicit owner approval after confirming no sessions.
5. Run the full PostgreSQL suite once, without parallel database-heavy work, and preserve command, timestamp, versions, duration and result.

Until that clean run succeeds, Phase I PostgreSQL status remains **NOT PASSED**.

## Remaining blockers

- Target VPS and written read-only/deployment authority
- Complete host/co-tenant inventory and resource evidence
- Port, Docker network/volume and NGINX conflict assessment
- Firewall and IPv4/IPv6 exposure assessment
- DNS/TLS ownership and renewal evidence
- Reviewer VPN/IP/authentication decision
- Secret-generation and custody approval
- Backup/RPO/RTO/restore evidence
- Clean Phase I PostgreSQL rerun
- Target-host reliability, security, performance and UAT evidence

## Gate recommendation

**NO-GO.** The existing VPS cannot be declared safe because it has not been identified or inspected under documented authority. The local topology is suitable for a controlled deployment rehearsal after the manual read-only inventory passes, required approvals are evidenced, and the PostgreSQL suite is cleanly rerun. SSH availability, if later supplied, permits only the expressly approved inspection; it does not authorise deployment.
