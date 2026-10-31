# IMSUTH PayPoint staging deployment decision

## Decision

Use a **dedicated staging project on an authorised VPS**, fronted by a host NGINX TLS reverse proxy at a dedicated staging hostname, with the PayPoint application served under `/paypoint/`. Keep it isolated from existing client applications by project directory, Unix account, Compose project name, networks, volumes, secrets, database and Redis instance.

**Current release decision: NO-GO.** This is not a rejection of the application build. It means remote deployment is prohibited until the host and access controls are authorised and evidenced.

## Target architecture

```text
Approved reviewers
  -> HTTPS / IP-or-VPN allow-list / outer basic authentication
  -> host NGINX on dedicated staging hostname
  -> 127.0.0.1:18080
  -> staging NGINX (/paypoint/ prefix)
  -> Django/Gunicorn web ---- PostgreSQL (data network only)
                     |------ Redis (data network only)
                     |------ Celery worker + beat
```

Only ports 80/443 are externally reachable, with 80 redirecting to 443. PostgreSQL, Redis, Gunicorn and the inner NGINX port are not publicly bound. The existing public IMSUTH website and its cPanel/DNS/SSL configuration remain untouched.

## Minimum provisional sizing

Before acceptance, measure the actual VPS and existing workloads. A safe initial isolated UAT allocation is 4 vCPU, 8 GB RAM and at least 80 GB SSD with additional encrypted off-host backup capacity; final limits must be adjusted from observed load. Maintain at least 30% memory and disk headroom and configure alerts before inviting reviewers. Do not co-locate if existing workloads would breach this headroom or cannot be independently isolated.

## Alternatives considered

| Option | Decision | Reason |
|---|---|---|
| Existing shared cPanel/Namecheap web environment | Reject | Poor fit for the six-service container stack, worker/beat, Redis and controlled database isolation; risks the public website. |
| Existing VPS with dedicated reverse-proxy route | Conditional | Acceptable only after written authorisation, capacity inventory and demonstrated tenant isolation. |
| Separate VPS and dedicated staging hostname | Preferred | Clearest security boundary, rollback, resource accounting and preservation of other client/public services. |
| Public staging without network/outer access restriction | Reject | Application login alone does not satisfy the stated staging exposure restriction. |

## Prepared deployment inputs

- `backend/deployment/compose.staging.yaml`: hardened six-service staging topology.
- `backend/deployment/staging.env.example`: non-secret, debug-off staging settings template.
- `backend/deployment/nginx-staging.conf`: inner prefix router/security headers/rate limits.
- `backend/deployment/host-nginx-staging.conf.example`: TLS terminator with access-control placeholders.
- Backup/restore scripts: checksum-verified PostgreSQL custom dump workflow.

These are prepared artifacts, not proof that the target host works. Docker Compose could not be executed locally because the workstation has no available Docker daemon/Compose plugin.

## Authorisation and acceptance gates

| Gate | Accountable approver | Required evidence | Acceptance |
|---|---|---|---|
| VPS selection/capacity | System Administration + project sponsor | Host inventory, workload map, CPU/RAM/disk monitoring snapshot | Approved capacity and isolation; no impact to existing apps |
| Staging exposure | Security + Privacy | Data classification, reviewer list, IP/VPN ranges, outer-auth design | Synthetic-only, least access, no anonymous public reachability |
| Hostname/TLS | System Administration + Security | Approved FQDN, certificate chain/expiry, renewal test | Valid HTTPS; TLS 1.2/1.3; alertable renewal |
| Secrets | Security + System Administration | Secret generation/storage record and file-permission evidence | Unique protected values; none committed/logged |
| Stack deployment | Delivery lead + System Administration | Rendered Compose, health output, ports/networks/volumes inspection | Six healthy services; only approved edge ports reachable |
| Application routing | Delivery/UAT lead | Completed routing portion of UAT plan | Prefix, login, redirects, CSRF, API, static, receipt and docs pass |
| Finance workflow | Finance + UAT lead | Signed synthetic workflow and idempotency evidence | Correct posting, receipt, notification/dashboard and reconciliation |
| Recovery | System Administration + Finance | Backup checksum, restore log, counts/references, measured RTO | Independent restored database validated |
| Security release | Security authority | Closed findings or signed risk acceptances | No open Critical/High; blocking Mediums resolved |

## Rollback

Do not modify public-site configuration. Keep the prior image tag and database backup before each staging release. On failure, remove reviewer access, stop the isolated Compose project, preserve logs/evidence, restore to a new database volume and repoint only after validation. Never overwrite the sole database volume as a rollback technique.

## Final recommendation

Remain **NO-GO** until VPS authorisation/capacity, protected HTTPS exposure, secret provisioning and successful target-host stack validation are documented. Once those gates pass, proceed with controlled synthetic-data UAT; production connectivity, real patient data and real money remain explicitly out of scope.
