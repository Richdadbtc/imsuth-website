# IMSUTH PayPoint staging security review

**Review date:** 11 October 2026  
**Method:** configuration/code review plus local PostgreSQL integration, permission, concurrency and backup/restore execution. No penetration test or remote-host assessment was performed.

## Findings

| ID | Severity | Finding | Disposition |
|---|---|---|---|
| SEC-01 | High | Django superusers could inherit broad PayPoint financial API authority, defeating segregation of duties. | **Fixed and tested.** PayPoint roles now determine financial authority; a superuser without an authorised role is denied. |
| SEC-02 | High | Financial and patient records were editable through Django Admin, providing a parallel uncontrolled mutation path. | **Fixed.** Relevant admin registrations are inspection-only; user administration remains separate. |
| SEC-03 | High | Deterministic test payment verification required `DEBUG=true`, which conflicted with secure staging. | **Fixed and tested.** Adapter is allowed only outside production when explicit test mode and a secret are present; staging keeps debug off. |
| SEC-04 | High | Payment and invoice idempotency checks could race before database locking. | **Fixed and tested.** Keys are rechecked in the serialized transaction; threaded PostgreSQL test passed. |
| SEC-05 | Medium | The explicit test webhook could be shadowed by the router detail route. | **Fixed.** Explicit route now precedes router URLs; signed webhook workflow test passed. |
| SEC-06 | Medium | Inner NGINX could overwrite the original HTTPS scheme from the outer TLS proxy. | **Fixed in staging config.** Original forwarded scheme is preserved; real two-proxy validation is pending. |
| SEC-07 | Medium | Original Compose used a shared default network and lacked staging container limits/hardening. | **Fixed in staging artifact.** Split networks, no host DB/Redis ports, limits, read-only/no-new-privileges/cap drops added; runtime validation pending. |
| SEC-08 | Medium | Role changes are not yet represented by a dedicated, independently reviewed access-certification workflow with periodic recertification evidence. | **Open.** System Administration and Security must approve joiner/mover/leaver and quarterly access-review procedures before operational staging accounts. |
| SEC-09 | Medium | Application-level MFA is not implemented. | **Open.** For staging, require IP/VPN allow-list plus independent outer authentication and unique app passwords. MFA is required before any production deployment or handling real records/money. |
| SEC-10 | Medium | Exact VPS posture, patch level, firewall, disk encryption, monitoring and co-tenant resource risk are unknown. | **Blocking.** Complete host inventory/hardening evidence before deployment. |
| SEC-11 | Medium | End-to-end container, Redis/Celery restart and edge rate-limit behavior has not been executed. | **Blocking for staging sign-off.** Run the deployment/UAT checklist on an authorised disposable VPS. |
| SEC-12 | Low | Notification delivery beyond the in-app channel is not provider-configured. | **Open/non-blocking for isolated UAT.** Use in-app notifications; do not add real hospital SMTP/SMS credentials without approval. |

## Security baseline required on the staging VPS

- Dedicated non-root service account and project directory; no reuse of another client application's database, Redis, network, secrets or volumes.
- Host firewall permits SSH only from administrator sources and HTTPS only from the approved reviewer network/VPN; inner port 18080 remains loopback-only.
- Valid CA TLS certificate, TLS 1.2/1.3, automatic renewal with failure alert, HTTP-to-HTTPS redirect and conservative HSTS for staging.
- Outer IP/VPN restriction and separate basic authentication in addition to PayPoint login.
- Docker daemon socket unavailable to application containers; supported patched engine/Compose; log rotation and disk monitoring.
- Unique high-entropy Django, PostgreSQL and webhook secrets supplied as root/service-readable files, excluded from source, logs, backups where inappropriate and screenshots.
- `DEBUG=false`; production-like secure session/CSRF settings; exact allowed hosts and trusted origin; test mode cannot run in production environment.
- PostgreSQL and Redis attached only to the internal data network, authenticated, persistent, backed up and not host-published.
- Least-privilege role assignment, unique accounts, forced credential replacement, inactive-account disablement and recorded access reviews.
- Central review of login, role, invoice, payment, receipt, approval and reconciliation audit events; system time synchronisation and alerting.
- Encrypted off-host backups, checksum, retention and documented restore test; access restricted and logged.

## Secrets and test data

The provided environment files contain placeholders only. Generate values on the authorised host, set owner/mode before starting containers and never paste them into tickets or screenshots. Staging must use synthetic identities and amounts. No real patient record, bank account, gateway live key, hospital mail/SMS credential or production database copy is permitted.

## Conclusion

The local code-level High findings discovered in this review were remediated and covered by tests. The residual risk is primarily the unassessed remote host and unexecuted edge/container environment. Therefore security does **not** authorise remote staging yet. Approval can be reconsidered after SEC-10 and SEC-11 have evidence and the staging compensating controls for SEC-08/09 are formally accepted.
