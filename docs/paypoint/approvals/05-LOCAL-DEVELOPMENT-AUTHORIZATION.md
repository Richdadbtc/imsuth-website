# Gate 1.5 — Synthetic-Data-Only Local Development Authorization

**Status:** PENDING / NOT AUTHORIZED  
**Decision requested:** Authorize only the isolated Phase B foundation activities listed below using generated synthetic data and local-only credentials.

## Authorized scope if approved

- Django project scaffolding and modular application boundaries.
- Local Docker Compose services for Django, PostgreSQL, Redis and Celery.
- Environment validation using placeholder/local secrets.
- Custom user model, role/permission framework and authorization tests.
- Login/logout, session expiry, local password-reset mail sink and MFA-ready interfaces.
- Append-only audit-event foundation and correlation identifiers.
- Health checks, redacted structured logging and safe error handling.
- Dependency locking/scanning, tests, linting, secret scanning and migration checks.
- IMSUTH-branded templates scoped locally under `/paypoint/`.
- Generated fixtures/factories with visibly fictional identities.
- Provider-neutral interface definitions whose local test implementation cannot create an official confirmed payment or receipt.

## Explicitly prohibited

- Real or copied patient, staff, supplier, bank, card, payment or hospital transaction data.
- Production credentials, API keys, webhook secrets, certificates or database copies.
- Real provider/bank integration, real fund movement or a fake workflow presented as successful production payment.
- Official paid receipts or production-like confirmation that could be mistaken for proof of payment.
- Staging or production deployment; public access; DNS, TLS, cPanel, NGINX or public-site changes.
- Modification of production databases, files, forms or deployment pipelines.
- Finalization of policy-dependent behavior before the accountable owner approves it.

## Synthetic-data standard

- Names and identifiers must be generated and clearly fictitious, such as `TEST-PATIENT-0001` and reserved example domains.
- Phone numbers, addresses and emails must not correspond to real individuals.
- Financial scenarios use arbitrary test amounts and must display a non-production marker.
- Local databases and artifacts must be disposable and must never be promoted to staging/production.
- Screenshots, logs, fixtures and test reports must contain synthetic data only.
- Any suspected real-data exposure stops work and is reported immediately to Privacy and Security owners.

## Authorization decisions

| Item | Required decision | Accountable approver | Evidence of approval | Acceptance criteria | Status |
|---|---|---|---|---|---|
| L1 Scope | Authorize only the listed local foundation work. | Executive Sponsor and System Owner | Signed form/controlled decision | Scope matches readiness report Section 8 and excludes policy-dependent functionality. | PENDING |
| L2 Data | Approve synthetic-data standard and prohibition of real data. | Privacy/DPO Owner | Signed form and data-handling standard | Test generation, reporting, incident escalation and disposal are defined. | PENDING |
| L3 Security | Approve local isolation, credential and CI control baseline. | Security Owner | Signed form/security decision record | Local-only secrets, deny-by-default controls and required scans/checks are accepted. | PENDING |
| L4 Technical baseline | Approve container services, supported dependency policy and quality gates. | Technical Delivery Lead | Signed technical decision record | Dependencies will be pinned; tests, migration checks, linting and scans are mandatory. | PENDING |
| L5 Stop conditions | Authorize the named owners to stop work for scope, data or security violations. | Executive Sponsor | Signed form | Privacy, Security and System owners have an explicit stop-work route. | PENDING |

## Development environment register

**Approved repository/branch location:** PENDING — ____________________________  
**Approved developer(s):** ___________________________________________________  
**Local environment owner:** _________________________________________________  
**Synthetic-data generator/reference:** ______________________________________  
**Evidence/decision register ID:** ____________________________________________  
**Authorization expiry/review date:** _________________________________________

## Signatures

| Approver | Decision | Date | Signature / evidence reference |
|---|---|---|---|
| Executive Sponsor/System Owner | PENDING |  |  |
| Privacy/DPO Owner | PENDING |  |  |
| Security Owner | PENDING |  |  |
| Technical Delivery Lead | PENDING |  |  |

**Effective condition:** This authorization becomes effective only after all required signatures and the repository isolation checklist are accepted. Its maximum outcome is **CONDITIONAL GO for local foundation work**.
