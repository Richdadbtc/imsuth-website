# IMSUTH PayPoint Phase I — security results

## Decision

**Security gate: NO-GO for public or hospital-reviewer exposure.** Code/configuration controls are prepared, but the target host, certificate and external access boundary have not been inspected.

| Control | Local result | Staging evidence required |
|---|---|---|
| `DEBUG=false` | Configured in staging template | Runtime settings check |
| Secure cookies/CSRF | Configured | HTTPS response/cookie and negative-CSRF tests |
| Allowed hosts/trusted origins | Proposed hostname configured | Runtime invalid-host/origin tests |
| HTTPS redirect/HSTS | Configured conservatively | External redirect/header/TLS scan |
| Secret handling | Docker secret-file support prepared | Target ownership/mode and leak scan |
| Role access | Automated tests pass | Seven-role manual direct-URL/API denial evidence |
| Login/API rate limiting | NGINX rules prepared | Runtime burst/normal-use test |
| Audit persistence | Append-only tests pass | Restart/backup/restore persistence evidence |
| Database/Redis isolation | Split internal data network prepared | Target port/network inspection |
| Encrypted transport | Host TLS example prepared | Valid certificate, protocols and renewal test |
| Backup permissions | Scripts/checksum prepared | Encrypted off-host ACL and restore drill |
| Dev/internal exposure | No host DB/Redis ports in staging YAML | External scan and route inventory |

## Findings

### Blocking

- **I-SEC-01 — target infrastructure unassessed:** no authorised VPS inventory, firewall, patch, co-tenant, disk-encryption, logging or Docker-daemon evidence.
- **I-SEC-02 — HTTPS/access boundary absent:** proposed hostname has not been authorised; no certificate, reviewer allow-list or outer credentials exist.
- **I-SEC-03 — runtime stack unverified:** Compose, NGINX, Redis, Celery and container restart behavior were not executed on a representative host.
- **I-SEC-04 — browser security validation absent:** cookies, CSRF, redirects, headers, route prefix, rate limits and access denials have not been observed through the intended TLS proxy chain.

### Corrected locally

- Staging hostname is consistent across environment, health check and both NGINX layers.
- Phase H static manifest was rebuilt; deployment must always run `collectstatic` before web health checks.
- README no longer incorrectly instructs staging to enable debug for the deterministic adapter.

### Residual controls

- Use VPN/IP restriction plus independent outer authentication and unique PayPoint accounts.
- Application MFA remains a production requirement; staging compensating controls require written Security acceptance.
- Use synthetic data and test adapters only. No live bank, SMTP/SMS patient or production credentials.
- Require time synchronisation, log rotation, alerting and an access recertification procedure.

## Accessibility/security boundary

No browser screenshot, automated accessibility score or TLS scan is reported because no reachable authorised staging endpoint exists. These omissions are blockers, not passes.
