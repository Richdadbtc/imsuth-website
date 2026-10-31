# Gate 1.4 — Hosting Direction and Discovery Decision

**Status:** PENDING  
**Decision requested:** Select a preferred hosting direction for planning and authorize evidence gathering only. This document does not authorize deployment, purchasing, DNS, TLS, cPanel or public-site changes.

## Current evidence

- The existing public website is deployed as static/PHP content to Namecheap cPanel `public_html`.
- No Django/Python application, PostgreSQL, Redis, supervised Celery worker or `/paypoint/` reverse proxy is evidenced in the repository.
- Valid production TLS for the relevant routes has not been evidenced in the project documents.
- The intended public route is `https://www.imsuth.org/paypoint/`; a subdomain would change that requirement and needs explicit approval.

## Option comparison

| Criterion | Existing Namecheap environment | Dedicated VPS with `/paypoint/` reverse proxy | Dedicated PayPoint subdomain on VPS/managed platform |
|---|---|---|---|
| Intended URL | Potentially `/paypoint/`, only if cPanel supports a secure app mount/proxy | Keeps `/paypoint/` while public site can remain on cPanel | Changes URL, e.g. an approved staff portal hostname |
| Public-site disruption | Low if capability exists | Low to medium; proxy change must be controlled | Low; public site remains separate, but DNS/navigation change is required |
| Django suitability | Unknown; shared-host limitations likely | Strong when correctly managed | Strong when correctly managed |
| PostgreSQL/Redis/Celery | Unknown and not evidenced | Supported under designed private networking/service supervision | Supported under designed private networking/service supervision |
| Routing control | Host-dependent | Strong, but cPanel/edge must proxy the path or both sites share an approved edge | Strong and operationally simpler |
| Isolation | Potentially weaker/shared | Strong with hardened VPS/network | Strong with hardened VPS/network |
| Operations burden | Lower apparent cost, but capability risk | Requires patching, monitoring, backups and incident ownership | Same VPS/managed responsibility; simpler routing boundary |
| TLS | Must be proven and auto-renewed | TLS required at edge and origin as designed | TLS required for subdomain and origin |
| Main risk | Unsupported services or inability to proxy `/paypoint/` | Routing dependency and larger operational responsibility | URL change, DNS approval and anti-phishing/user communication |
| Architecture view | Accept only after a written capability/security review | Preferred if secure path proxying is supported | Preferred fallback if path proxying is unavailable and management accepts URL change |

## Required hosting-provider evidence

Namecheap/hosting provider must answer in writing:

1. Whether Python 3.12+ and cPanel Application Manager/Passenger are available.
2. Whether Django can be mounted at `/paypoint/`.
3. Whether Apache/NGINX can reverse-proxy `/paypoint/` to an external application origin with correct host/protocol/client headers.
4. Whether long-running Celery workers and scheduler processes are supported and supervised.
5. Whether PostgreSQL and Redis are supported with private connectivity, encryption and automated backup.
6. Who controls TLS, renewal, proxy/request limits, WAF, logs and incident support.
7. The document root, authoritative DNS/nameservers, origin/server IPs, backup schedule and restoration SLA.

## Decision table

| Decision | Required decision | Accountable approver | Evidence of approval | Acceptance criteria | Status |
|---|---|---|---|---|---|
| H1 Capability inquiry | Authorize IMSUTH IT to request the written evidence above. | System Owner/IMSUTH IT authority | Signed authorization and provider ticket/reference | Inquiry discloses no credentials/sensitive data and makes no production change. | PENDING |
| H2 Preferred option | Select planning preference: existing Namecheap, VPS reverse proxy, or dedicated subdomain. | Executive Sponsor and System Owner | Signed selection with reasons | Selection acknowledges risks, evidence gaps, budget owner and that implementation is not authorized. | PENDING |
| H3 Fallback option | Select fallback if preferred route is infeasible. | Executive Sponsor and System Owner | Signed fallback decision | Fallback preserves security requirements; any URL change is explicit. | PENDING |
| H4 Technical acceptance criteria | Approve minimum availability, backups/RPO/RTO, monitoring, isolation and support criteria for later procurement. | System Owner, Security Owner and Finance/procurement | Approved requirements record | Criteria are measurable and do not assume unproven host capabilities. | PENDING |
| H5 Later change authority | Identify who can authorize DNS, TLS, proxy/cPanel and deployment changes. | Executive Sponsor/CMD | Delegation/approval workflow | Named authority and rollback/maintenance approval process recorded. | PENDING |

## Recommended decision path

1. Authorize H1 only and obtain the provider response.
2. If secure path proxying is supported, prefer a dedicated VPS/managed application with only `/paypoint/` proxied from the existing site.
3. If path proxying is unavailable, management chooses between moving both properties behind a controlled edge later or approving a dedicated staff subdomain.
4. Do not host the full financial system directly on shared cPanel unless every runtime, isolation, worker, database, backup, monitoring and support requirement is proven.

## Management selection

**Preferred option:** PENDING — _____________________________________________  
**Fallback option:** PENDING — ______________________________________________  
**Rationale:** ______________________________________________________________  
**Budget/procurement owner:** ________________________________________________  
**Required evidence due date:** ______________________________________________

| Approver | Decision | Date | Signature / evidence reference |
|---|---|---|---|
| Executive Sponsor/CMD or delegate | PENDING |  |  |
| System Owner/IMSUTH IT | PENDING |  |  |
| Security Owner concurrence | PENDING |  |  |
| Finance/procurement concurrence | PENDING |  |  |

**Document acceptance:** A planning direction may be approved with outstanding provider evidence, but Gate 3 deployment readiness cannot pass until the selected option is proven. No signature here authorizes infrastructure modification.
