# Contabo shared VPS pre-deployment audit

Date: 25 October 2026 (Africa/Lagos)  
Project: `/Users/mac/Documents/imsuth/`  
Decision: **NO-GO pending SSH access, remote inventory and capacity evidence**  
Scope: read-only discovery and local deployment configuration review. **No remote connection was attempted and nothing on the VPS was changed.** This is an incomplete infrastructure audit, not a remote inspection certificate.

## Evidence and access limitation

The current user request authorizes read-only inspection. Local `~/.ssh/config` contains only an Include for local Colima configuration; no usable Contabo alias was identified. The SSH agent reports no identities and `~/.ssh/` contains no private-key files. Known-host records were not treated as authorization or used to guess a target.

Requested from the owner: SSH hostname/IP, username, port and authentication method (existing key path, SSH agent or interactive sign-in). Passwords and private keys must not be sent in chat. SSH configuration will not be changed, host-key checking will not be bypassed, and sudo will only be used non-interactively for authorized read-only inspection. Unknown host keys require independent fingerprint verification before connecting.

Local evidence reviewed: `backend/deployment/compose.staging.yaml`, `staging.env.example`, both staging NGINX examples, Dockerfile, Gunicorn configuration, attachment storage model and backup/rollback scripts. The earlier Phase I assessment is historical, not evidence of this VPS's current state.

## 1. Existing server topology

**Unknown.** No remote OS, network, proxy or storage configuration has been inspected.

| Required observation | Result |
| --- | --- |
| Linux distribution/version/kernel | Unverified |
| vCPU, CPU load/steal, RAM/swap pressure | Unverified |
| Disk capacity, inodes, I/O, Docker storage mount | Unverified |
| Docker Engine and Compose versions | Unverified |
| Host/container reverse proxy, ports 80/443 ownership | Unverified |
| PostgreSQL and Redis: host/container/shared/managed | Unverified |
| Firewall, provider firewall and IPv6 exposure | Unverified |
| Certificate manager, renewal timers and ownership | Unverified |
| Deployment directories, backup ownership and monitoring | Unverified |

## 2. Running application inventory

Not collected because the target/access is missing. Container names, images/digests, Compose projects, resource limits, restart policies, network membership, mounts, volumes and published ports must be recorded before choosing a deployment location. No application names or server resources are invented here.

Collect only selected Docker metadata. Do not dump container environments, `docker compose config` with resolved secrets, entire inspect JSON, application logs, private keys, credential files or database contents. Proxy configuration should be parsed on the server to return only server names, listen addresses, upstream names/addresses and certificate paths; raw configuration may contain credentials and must not be printed.

## 3. Port conflicts

No port is confirmed free. The existing Compose example proposes **127.0.0.1:18080 → inner NGINX:8080**, with web:8000, PostgreSQL:5432 and Redis:6379 internal only. Ports 80/443 must remain owned by the existing reverse proxy. Do not publish database, Redis, Gunicorn or Celery ports on the host.

Check TCP/UDP and IPv4/IPv6 listeners, Docker port publications and reserved deployment configuration. If 18080 is occupied or reserved, select a verified unused loopback port in a reviewed override. Do not stop its current owner. If the existing edge is a container, its localhost is not the host loopback: the final topology must use a compatible dedicated ingress network or established host-gateway pattern, not assume 127.0.0.1 works from the proxy container.

## 4. Resource availability and capacity assessment

Actual available capacity is **unknown**. Prefer option A only after measurement. Existing staging Compose limits total **2.875 GiB RAM** and CPU ceilings total **6 vCPU**; ceilings are not reservations or proof of throughput. Add image-build peaks, OS/proxy overhead, page cache, PostgreSQL shared memory, backup compression and co-tenant peaks.

| Component | Initial staging estimate/limit | Assessment |
| --- | --- | --- |
| Django/Gunicorn, 2 workers × 2 threads | 768 MiB; 1.5 CPU ceiling | Measure request/concurrency memory |
| PostgreSQL | 1 GiB; 2 CPU ceiling; 256 MiB shared memory | Tune connections/buffers; assess I/O and WAL growth |
| Redis | 256 MiB; 0.5 CPU ceiling | Example maxmemory 192 MiB/noeviction; AOF rewrites need headroom |
| Celery worker, concurrency 2 | 512 MiB; 1 CPU ceiling | Task memory and queue growth must be measured |
| Optional single Celery Beat | 256 MiB; 0.5 CPU ceiling | Start only if schedules require it; avoid duplicate scheduler |
| Inner NGINX/static assets | 128 MiB; 0.5 CPU ceiling | Static source mounted read-only |

Planning baseline: at least approximately **3–4 GiB incremental usable RAM**, **20 GiB incremental free disk before initial staging**, plus measured database/attachment/WAL/log/image growth, retained releases and backup working space. These are estimates, not acceptance thresholds on an uninspected host. Prefer 30% host RAM and storage headroom after existing peak workloads and IMSUTH's allocation. A 4-vCPU/8-GiB host may be a starting point only if co-tenants leave sufficient capacity; it is not automatically adequate.

Collect several current CPU/memory samples, filesystem/inode usage and existing resource limits; obtain historical peak CPU/RAM/I/O and daily storage growth from the owner. Do not infer long-term spare capacity from a single idle snapshot. Avoid host image builds if their CPU/disk spikes could affect clients; prefer externally built, approved digest-pinned images.

## 5–7. Recommended architecture, directory and isolation

**Provisional preference: A — isolated Compose project with dedicated PostgreSQL and Redis.** Option B is a fallback only if dedicated infrastructure cannot fit and the infrastructure owner confirms sufficient shared-service capacity and supported isolation. With B, use a separate database/role without superuser access, separate credentials, Redis ACLs and key/queue prefixes and dedicated Celery queues. A Redis database number alone is not a security boundary, and shared eviction/restarts/backups remain co-tenant risks. A separate VPS is safer if neither arrangement fits.

Proposed directory (availability/ownership unverified): `/srv/imsuth-paypoint/staging/`, with versioned release directories, an approved dedicated service account, restricted secrets outside the release tree and a separate backup namespace. Keep the repository layout containing **both `backend/` and `website/paypoint/`**: current Compose's NGINX bind mount requires the frontend sibling directory. A backend-only checkout is insufficient for this Compose example.

Proposed Compose project: `imsuth-paypoint-staging` (must confirm absent from existing projects). Do not use fixed `container_name` entries.

Expected project-scoped networks:

- `imsuth-paypoint-staging_app`: web, worker, scheduler and inner NGINX.
- `imsuth-paypoint-staging_data`: internal-only PostgreSQL/Redis plus application consumers.
- Only if required by a container edge: narrowly scoped ingress network linking edge and inner NGINX; never join unrelated data networks.

Expected volumes:

- `imsuth-paypoint-staging_staging_postgres_data`
- `imsuth-paypoint-staging_staging_redis_data`
- `imsuth-paypoint-staging_celerybeat_data`

Confirm names and Docker subnet/IPAM conflicts. Avoid choosing static subnets before inspecting Docker and VPN/host routes. Private attachments are stored as database binary content and must be included in database backup sizing.

## 8. DNS, reverse proxy and TLS plan

Read-only DNS lookup at approximately **03:08 WAT, 25 October 2026**, through resolver 8.8.8.8: `staging-paypoint.imsuth.org` A, AAAA and CNAME queries all returned **NXDOMAIN**. This is a recursive-resolver observation, not proof of authoritative zone ownership.

Later authorized changes:

1. Confirm DNS owner and the actual existing edge's public IP. Add only the staging hostname's A record. Add AAAA only if IPv6 routing, proxy and firewall are verified; leave public website/mail records untouched.
2. Integrate one hostname into the **existing** reverse proxy using its established configuration and reload process. Preserve all other virtual hosts, routes and defaults. Do not install a competing proxy or bind another service to 80/443.
3. Use the existing certificate manager and renewal mechanism. HTTP-01 must use the established challenge route; do not stop the proxy for standalone issuance. DNS-01 may be appropriate if staging is private, using scoped DNS credentials through the owner's secret workflow.
4. Route `/paypoint/` to the isolated inner NGINX and explicitly redirect `/` to `/paypoint/`. Preserve Host and trusted HTTPS forwarding headers; reject spoofed external forwarding headers at the edge. Keep `/healthz` restricted to monitoring.
5. Set exact allowed hosts and CSRF trusted origin to the staging hostname; retain secure session/CSRF cookies. Use approved VPN/IP restrictions and/or individual edge access controls. Certificate issuance precedes enabling certificate references in a live configuration.
6. Validate proxy configuration before its approved reload, then test TLS chain, renewal path, login/API, static assets and every existing client route against a baseline.

Do not run DNS writes, certificate commands or proxy reloads during this audit.

## 9. Backup and rollback

Confirm encrypted off-host backup destination, quota, retention, RPO/RTO, restore owner and a successful restore rehearsal. Docker volumes and VPS snapshots are not sufficient independent backups. Database dumps include attachments and sensitive application information; never print their contents. Redis AOF/queue durability, outstanding tasks and scheduler state require a separately documented recovery strategy.

The current `backup.sh` expects externally supplied PostgreSQL authentication; a Compose password-file secret does not automatically configure pg_dump authentication. Prepare a reviewed secret-safe backup job, not credentials in command arguments. Store image digest, release identity, schema migration history and sanitized edge configuration backup before deployment.

Rollback is scoped to IMSUTH only: revert to the previous approved image/release, preserve data volumes and audit records, and prefer a database forward fix. Restoring a database can lose financial changes and requires explicit approval. Never use `docker system prune`, `docker volume prune`, global container stops or `compose down -v`. Do not restart Docker, PostgreSQL/Redis shared services or unrelated applications. Revalidate all existing client routes after an authorized IMSUTH change.

## 10. Exact commands for a later authorized stage

**Not executed. Not authorization.** Fully executable DNS/proxy/TLS commands cannot be finalized until target, edge software, certificate manager, paths and access policy are known. The following commands use the existing staging Compose file and proposed paths; prerequisites are an approved release at the path, reviewed env/secrets, capacity/conflict checks, corrected configuration issues below and approved backup/access procedures. No copy/clone command is prescribed until the release source is approved.

```sh
cd /srv/imsuth-paypoint/staging/current/backend
# Verify this resolves to the approved immutable release before continuing.
pwd -P
# Validate without printing resolved environment/secret values.
docker compose --project-name imsuth-paypoint-staging --file deployment/compose.staging.yaml config --quiet
# Prefer replacing build sections with approved image digests before this step.
# If on-host build is approved and capacity permits:
docker compose --project-name imsuth-paypoint-staging --file deployment/compose.staging.yaml build web worker beat

docker compose --project-name imsuth-paypoint-staging --file deployment/compose.staging.yaml up -d db redis
docker compose --project-name imsuth-paypoint-staging --file deployment/compose.staging.yaml ps
# Wait for healthy dependencies; do not proceed on errors.
docker compose --project-name imsuth-paypoint-staging --file deployment/compose.staging.yaml run --rm --no-deps web python manage.py check --deploy
docker compose --project-name imsuth-paypoint-staging --file deployment/compose.staging.yaml run --rm --no-deps web python manage.py migrate --plan
# Stop here for reviewed migration plan and verified pre-migration backup.
docker compose --project-name imsuth-paypoint-staging --file deployment/compose.staging.yaml run --rm --no-deps web python manage.py migrate --noinput
docker compose --project-name imsuth-paypoint-staging --file deployment/compose.staging.yaml up -d web worker nginx
# Optional: only if an approved schedule requires exactly one Beat instance.
docker compose --project-name imsuth-paypoint-staging --file deployment/compose.staging.yaml up -d beat

docker compose --project-name imsuth-paypoint-staging --file deployment/compose.staging.yaml ps
curl --fail --silent --show-error -H 'Host: staging-paypoint.imsuth.org' http://127.0.0.1:18080/healthz
curl --fail --silent --show-error -o /dev/null -H 'Host: staging-paypoint.imsuth.org' http://127.0.0.1:18080/paypoint/
# After separately approved DNS, edge and certificate changes:
curl --fail --silent --show-error -o /dev/null https://staging-paypoint.imsuth.org/paypoint/
```

Static collection is already performed in the Docker image build. Do not attempt writes to the read-only running application filesystem. Inspect deployment output locally for sensitive errors before retaining evidence. Record image IDs/digests and dependency health; do not treat the mere presence of containers as acceptance.

## 11. Risks to existing applications and local configuration findings

| Risk/finding | Required resolution before deployment |
| --- | --- |
| Unknown host capacity and co-tenant peaks | Actual inventory and peak workload evidence |
| Port/project/directory/network collision | Verify names, mounts and routes before provisioning |
| Disk or I/O exhaustion from builds, DB/WAL, attachments, AOF and backups | Growth budget, limits, log rotation, off-host backups and alerts |
| Host Docker/proxy/firewall changes disrupting clients | Reuse existing runtime/edge, narrow change window and baseline client tests |
| Unpublished Docker ports still reachable through shared networks | Separate data network, review memberships and Docker firewall behavior |
| Proxy example includes `/etc/nginx/proxy_params` without an explicit supplied mount | Verify file exists in the chosen NGINX image; supply reviewed headers configuration if absent; run NGINX validation in isolated rehearsal |
| Staging Gunicorn forwarded IP setting is `nginx` | Validate the installed Gunicorn accepts/resolves this trust setting and receives correct scheme; choose a verified narrow trust mechanism |
| Current inner static CSP allows self-only scripts while configuration is inline | Browser-rehearse the actual static index/CSP; externalize configuration or approve a nonce/hash; do not broadly enable unsafe-inline |
| Console email backend can log recovery email/code content | Replace with approved delivery and sensitive-data-safe logging before recovery UAT; verify codes never reach retained logs |
| Compose has no explicit container log rotation configuration | Add project-scoped logging limits during a later code/config preparation stage |
| Floating image tags and mutable source builds | Approve digest-pinned deployment artifacts; retain previous images/releases |
| Staging files require sibling frontend tree | Package frontend and backend together for this topology; preserve backend-only repository policy |
| Unknown firewall/TLS/backup owners | Obtain evidence, never assume existing settings are safe |

These are local configuration findings and verification requirements, not claims about the uninspected Contabo host. No configuration fixes were made in this read-only stage.

## 12. GO / NO-GO

**NO-GO for deployment.** Option A is preferred provisionally, but capacity and compatibility cannot be determined without SSH inventory. Option B is not approved as a shortcut. Blocking evidence: target/access, application inventory, spare CPU/RAM/disk/I/O, port/network availability, edge/TLS/firewall ownership, backup/restore capability and resolution of local configuration concerns.

Next action: supply the SSH connection metadata and authentication method through the requested fields, without passwords or private keys. Resume only read-only inspection, replace unknown entries with measured evidence, and then issue a final architecture/capacity recommendation. This report does not authorize deployment, installation, service changes, DNS writes or certificate changes.
