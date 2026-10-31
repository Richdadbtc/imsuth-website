# IMSUTH PayPoint — Phase B Readiness Report

**Assessment date:** 10 October 2026  
**Source:** `docs/PAYPOINT-PHASE-A-ARCHITECTURE.md` and current repository evidence  
**Scope:** Readiness assessment only; Phase B implementation and production changes are excluded

## 1. Executive assessment

The technical direction is sufficiently defined to estimate and plan Phase B, but Phase A's exit conditions have not been met. The repository contains no evidence of:

- IMSUTH management approval of the architecture or Section 11 policies;
- an approved privacy, security, finance or operations owner;
- a written hosting capability response for `/paypoint/`;
- an approved development/staging infrastructure decision; or
- a signed role and segregation-of-duties baseline.

The current assessment is therefore **NO-GO for beginning Phase B**.

This is an approval and readiness hold, not a rejection of the architecture. A limited, synthetic-data-only local build can become a **CONDITIONAL GO** after the minimum authorization package in section 10 is signed. Production integration remains a separate later approval.

## 2. Decisions already resolved at architecture level

These items are defined well enough for review. They are engineering baselines, not evidence of IMSUTH executive approval unless a signed approval is supplied.

| Resolved baseline | Decision | Status / boundary |
|---|---|---|
| System separation | PayPoint will be an isolated Django application; it will not store private data in public JSON or reuse the static `admin.html`. | Technically resolved. |
| Public-site protection | Existing public pages, SEO, forms and assets remain unchanged except for a later approved staff-login link. | Technically resolved. |
| Target route | Intended staff entry is `https://www.imsuth.org/paypoint/`. | Product requirement resolved; delivery method unresolved. |
| Core stack | Python 3.12+, supported Django/DRF, PostgreSQL, Redis, Celery, Gunicorn and NGINX; Docker for development/supported VPS deployment. | Architecture resolved; exact versions and hosting not selected. |
| Source of truth | PostgreSQL is authoritative; Redis and browser state are not financial sources of truth. | Technically resolved. |
| Money representation | Decimal/PostgreSQL numeric values, never floating point. | Technically resolved. |
| Financial history | Confirmed financial events and audits are append-only; corrections use controlled transitions or compensating records. | Control principle resolved; policy details unresolved. |
| Payment confirmation | Browser claims or cashier clicks cannot confirm electronic payments. Signed provider events and/or server verification are required. | Security principle resolved; provider unresolved. |
| Receipt gate | Official paid receipts are issued only after an authorized confirmed payment transaction commits. | Control principle resolved. |
| Settlement distinction | Payment confirmation and bank settlement are separate facts and reconciliation states. | Accounting principle resolved. |
| Privilege model | Least privilege, role scope, MFA readiness and maker-checker segregation are mandatory; Super Admin cannot override financial approval rules. | Control principle resolved; grants and thresholds unresolved. |
| Environment isolation | Development, staging and production require separate data, credentials and provider accounts. | Technically resolved. |
| Development data | Only synthetic data may be used outside production. | Technically resolved. |
| Production safety | No live DNS, cPanel, TLS, database or website change without explicit approval. | Resolved governing constraint. |

## 3. Decisions requiring IMSUTH management approval

These cannot be safely chosen by the development team because they define hospital policy, legal purpose, clinical identity, accounting treatment or staff authority.

| ID | Required management decision | Recommended resolution | Why management approval is required |
|---|---|---|---|
| M1 | Patient identifier and migration | Approve a configurable `IMSUTH-{year}-{sequence}` display format, permanent UUID internally, a documented legacy-ID crosswalk and a designated Records Officer for duplicate merges. | Changes patient identity and record ownership. |
| M2 | Demographics, privacy basis and retention | Approve only fields necessary for registration/billing; obtain privacy/DPO review; publish correction, access and retention schedules before real data. | Legal/data-governance decision. |
| M3 | Payment channels and authorized locations | Start with only channels for which Finance has written procedures; enable each channel per PayPoint through configuration. | Determines custody of funds and operational exposure. |
| M4 | Partial payments, deposits and allocations | Default to disabled. Enable only after Finance defines allocation priority, receipt wording, balance handling and refund treatment. | Material accounting policy. |
| M5 | Invoice/receipt/adjustment numbering | Approve non-reusable sequences, location/year behavior and handling at financial-year boundaries; retain immutable internal UUIDs. | Official financial-document policy. |
| M6 | Tariff governance | Assign tariff proposer, finance reviewer and management approver; use future-effective versions; define an emergency change process with expiry/review. | Controls hospital pricing. |
| M7 | Maker-checker matrix and thresholds | Finance and Internal Audit must approve incompatible roles, value thresholds, escalation windows and absence cover. | Segregation-of-duties policy. |
| M8 | Refund, reversal, void, write-off and reprint rules | Approve reason codes, evidence, limits, approver roles and closed-period treatment. Prohibit deletion or overwrite. | Financial-control policy. |
| M9 | Cashier shifts and close-of-day | Define till ownership, cash counts, POS terminal mapping, handover, supervisor sign-off and discrepancy escalation. | Physical cash and terminal control. |
| M10 | Data-access scope | Approve minimum access by role, department and PayPoint. Recommend Super Admin administer access without routine patient/finance visibility. | Patient confidentiality and insider-risk decision. |
| M11 | Dashboard definitions | Finance must define gross, net, confirmed, settled, refunded, reversed, outstanding and reporting cut-off/timezone. | Prevents conflicting official figures. |
| M12 | Accountable owners | Name executive sponsor, product/system owner, Finance control owner, DPO/privacy owner, security incident owner and operational support contacts. | The system cannot safely operate without accountable owners. |
| M13 | Receipt devices and formats | Approve A4/thermal formats, printer models, QR disclosure and supported workstations/browsers. | Operational and privacy decision. |
| M14 | Notifications | Approve recipients, escalation rules, content minimization and authorized email/SMS channels. | May disclose patient or transaction information. |
| M15 | Future HMS identity ownership | Name the authoritative patient-identity system and approve integration boundaries/versioning. | Avoids conflicting patient masters. |

## 4. Payment-provider and banking approvals

Provider-specific behavior must not be invented. These items require Finance/procurement approval and official provider evidence.

| ID | Blocker | Required evidence | Recommended resolution |
|---|---|---|---|
| P1 | Payment provider not selected | Contract, official API/webhook docs, supported NGN flows, sandbox, security contacts, uptime/support terms and pricing | Run a documented provider evaluation; select at least one provider before Phase D, not necessarily before the local Phase B foundation. |
| P2 | Webhook authenticity unknown | Signature algorithm, key rotation, retry/replay semantics, event IDs and IP/domain guidance | Require cryptographic webhook verification and server-to-server status lookup; reject providers without adequate controls. |
| P3 | Settlement reporting unknown | Settlement file/API format, transaction IDs, fees, timing, adjustments and dispute process | Obtain sample settlement reports and reconciliation rules before payment model finalization. |
| P4 | Bank/virtual-account capability unknown | Written bank confirmation of APIs/files, reference behavior, account ownership and settlement timing | Treat bank transfer as manual/reconciliation-based until a documented integration is approved. Never infer an API. |
| P5 | Cash/POS verification policy unknown | Terminal register, shift process, settlement reports and supervisor approvals | Keep offline channels disabled in production until Finance signs the verification and reconciliation workflow. |

Provider selection is not required to scaffold identity, audit and environment foundations locally. It is required before implementing real payment confirmation, receipts based on those confirmations, or reconciliation adapters.

## 5. Technical blockers and recommended resolutions

| ID | Technical blocker | Current evidence | Recommended resolution | Decision owner |
|---|---|---|---|---|
| T1 | `/paypoint/` routing capability unconfirmed | Current cPanel configuration deploys static/PHP files to `public_html`; no proxy/application mount exists. | Send the Phase A capability questionnaire to the host and require written answers. Do not add rewrite/proxy rules experimentally on production. | Hosting provider + IMSUTH IT |
| T2 | Current cPanel plan may not support required services | No PostgreSQL, Redis, Celery supervision, Python app or private networking appears in the repository. | Prefer a dedicated VPS/managed app environment. Use cPanel only as public-site origin unless it passes a documented capability/security review. | Technical architecture + IMSUTH IT |
| T3 | Valid production TLS not evidenced | Architecture records recent cPanel evidence of no certificate. | Obtain valid automatically renewed TLS for all relevant origins; validate chain, renewal, HTTPS redirect and secure proxy headers before any staff access. | Hosting provider + IMSUTH IT |
| T4 | Development/staging platform unapproved | No Compose file or isolated environment exists. | Approve local Docker Compose for synthetic development and a separate protected staging environment with no production data. | Technical architecture; budget/hosting approval by management |
| T5 | Backup/restore targets and objectives undefined | No PayPoint data services or RPO/RTO exist. | Management approves RPO/RTO; engineers implement encrypted automated backups and scheduled restore tests in staging before production. | Management for objectives; technical team for design |
| T6 | Monitoring and incident ownership undefined | No PayPoint metrics, log sink, alerting or on-call owner exists. | Select monitoring/logging services, define severity/runbooks and assign named responders before staging contains sensitive data. | Security/operations management + technical team |
| T7 | Application secrets mechanism unselected | Public-site workflow has cPanel/GitHub secrets only; no runtime secret store is defined. | Use environment-injected secrets or a managed secret store with rotation and access logs; never place PayPoint secrets in Git or `public_html`. | Technical decision, security approval |
| T8 | Public repository worktree contains unrelated uncommitted changes | Current Git status shows numerous modified/untracked public-site files. | Preserve and review those changes, commit/stash through the owner's normal process, then create an isolated PayPoint branch or separate repository before Phase B. Do not discard them. | Repository owner + technical lead |
| T9 | Exact dependency versions not pinned | Architecture names supported product families only. | At Phase B authorization, select currently supported releases, lock dependencies and document upgrade/security support policy. | Technical decision |
| T10 | Data model has policy-dependent branches | Partial payments, allocations, numbering and access scopes are unresolved. | Keep optional features feature-flagged and do not finalize migrations for policy-dependent behavior until M1–M11 are approved. | Management policy + technical implementation |
| T11 | No formal threat model/data-flow approval | Principles exist, but no signed review is evidenced. | Complete a data-flow diagram, abuse-case review and privacy/security sign-off before handling real data or connecting providers. | Security/privacy owners |
| T12 | No CI/CD boundary for PayPoint | Existing workflow is static-site rsync. | Create a separate gated pipeline only after Phase B authorization; require tests, migration checks, scans, artifact provenance and manual production approval. | Technical decision; release authority approved by management |

## 6. Infrastructure requirements

### Required for safe local Phase B development

- Supported developer workstation/runtime with container tooling.
- Isolated Django application directory/branch or separate repository.
- Containerized PostgreSQL and Redis using non-production credentials.
- Django web process plus Celery worker and scheduler containers.
- Synthetic test-data factory; explicit prohibition on importing production patient or payment data.
- Local email/SMS sink and a non-financial fake adapter that cannot be mistaken for a successful provider confirmation.
- Version control protections, dependency lock files, automated tests, linting, migration checks and secret scanning.
- Developer documentation for setup, data reset and test execution.

### Required before shared staging

- Isolated private network and access-controlled staging environment.
- Valid TLS, separate hostname/routing approved for staging and no indexing.
- Managed or appropriately secured PostgreSQL/Redis with encrypted backups.
- Private receipt/import storage with malware/file validation controls.
- Central logs, metrics, alerts, time synchronization and named incident contacts.
- Staging-only secrets and provider sandbox credentials.
- Restore testing, vulnerability scanning and controlled administrator access with MFA.

### Required before production

- Approved `/paypoint/` routing architecture and origin restrictions.
- High-availability/maintenance expectations aligned to hospital operations.
- Production PostgreSQL, Redis, supervised Celery and Gunicorn/NGINX capacity.
- Automated encrypted backups, off-host copies, tested restore, approved RPO/RTO and retention.
- WAF/rate limiting where appropriate, monitoring, alerting, incident response and audit-log protection.
- Provider production credentials and webhook endpoints under controlled secret rotation.
- Reconciliation import/storage controls and bank/provider operational contacts.
- Disaster recovery, deployment rollback, migration rollback/forward-repair and business-continuity procedures.
- Privacy/security assessment, UAT, financial reconciliation trial and go-live approvals.

## 7. Safe deployment alternatives

No alternative should be implemented until approved.

| Priority | Alternative | Readiness recommendation |
|---:|---|---|
| 1 | Keep public website on cPanel; proxy only `/paypoint/` to a dedicated VPS/managed app | Best minimal-change option if the hosting provider explicitly supports secure path proxying and preserves host/protocol headers. Restrict the application origin from direct public bypass where practical. |
| 2 | Place both the static website and PayPoint behind one approved NGINX/edge layer | Best control and long-term consistency, but requires a rehearsed migration, DNS/TLS change, backups and rollback approval. |
| 3 | Use an approved staff subdomain backed by the dedicated application environment | Operationally clean contingency if path proxying is impossible. It changes the required URL and needs formal management/DNS approval and clear anti-phishing communication. |
| 4 | Run Django through cPanel Passenger | Accept only if the host proves support for the Python version, path mount, private PostgreSQL/Redis, supervised workers, backups, logs and resource capacity. Otherwise unsuitable. |
| 5 | Use an edge worker to proxy the path | Last-resort architecture requiring specialist review of cookies, cache bypass, headers, request bodies, failure modes and origin authentication. |

**Recommended path:** seek written confirmation for alternative 1. If unavailable, management should choose between alternative 2 and alternative 3. Do not silently change the URL or DNS.

## 8. Features safe to develop locally without production integration

These may begin only after the minimum conditional authorization in section 10. They must use synthetic data and local-only credentials.

### Safe foundation work

- Django project scaffolding and modular application boundaries.
- Docker Compose for local PostgreSQL, Redis, Django and Celery.
- Environment configuration validation with placeholder secrets.
- Custom user model, role/permission framework and scoped authorization tests.
- Login/logout, password reset using a local mail sink, session expiry and MFA-ready interfaces.
- Append-only audit-event foundation and correlation IDs.
- Health checks, structured/redacted logs and error handling.
- CI validation, dependency locking/scanning, tests and migration checks.
- IMSUTH-branded template shell scoped under `/paypoint/`.
- Synthetic factories and fixtures with obvious non-real identities.
- Provider-neutral interface definitions whose test adapters cannot create an official confirmed payment.

### Work that should wait for management policy

- Final patient fields, Patient ID numbering and duplicate merge authority.
- Final permission grants and departmental visibility.
- Tariff approval workflow and emergency changes.
- Invoice/receipt numbering and partial-payment allocation models.
- Cash/POS confirmation, refunds, reversals, voids and close-of-day behavior.
- Official dashboard definitions and export access.

### Work that should wait for provider/infrastructure approval

- Real payment initiation, webhook verification and payment confirmation.
- Production-looking paid receipts driven by provider events.
- Bank/settlement import parsers based on actual external formats.
- SMS/email delivery to real recipients.
- Production URL routing, DNS, TLS, cPanel/NGINX or CI/CD deployment changes.

## 9. Security and financial controls required from the first commit

These are not later hardening tasks. Phase B design and tests must assume them from the beginning.

### Security controls

- Deny-by-default server-side permissions with object/department/PayPoint scoping.
- Custom user model before initial migrations; strong password hashing and MFA-ready privileged flows.
- Secure session lifecycle, CSRF protection, login throttling and authentication-event auditing.
- Secret separation and fail-closed configuration; no secrets or real records in Git, logs, fixtures or screenshots.
- Structured logging with sensitive-field redaction and request correlation IDs.
- Input/schema validation, safe file handling and private storage abstractions.
- Dependency pinning, automated security checks and reviewed migrations.
- Environment isolation and explicit safeguards preventing production credentials/data in development.

### Financial controls

- Decimal money and explicit currency; server-side calculation only.
- Database constraints for positive amounts, valid transitions, uniqueness and referential integrity.
- Transactional sequence/reference generation and collision tests.
- Immutable tariff/invoice snapshots and append-only payment/audit event histories.
- Idempotency keys and unique provider-event constraints.
- Row locking/transaction boundaries for confirmation, allocation and receipt creation.
- No receipt before committed authorized confirmation.
- Separate confirmation, settlement and reconciliation states.
- Maker-checker enforcement in the domain/service layer, not only the user interface.
- No hard deletion of confirmed financial records; compensating records and reasoned transitions only.
- Actor, reason, before/after-safe context and approval chain for sensitive actions.
- Synthetic adapters must never use a status or visual treatment that could be mistaken for production confirmation.

## 10. Readiness gates and blocker resolution path

### Gate 1 — Move from NO-GO to CONDITIONAL GO for local Phase B foundation

All of the following should be documented:

1. IMSUTH approves the Phase A architecture in principle.
2. Named executive/system, Finance, privacy and security owners are assigned.
3. The initial role/segregation principle and development-data prohibition are approved.
4. Management authorizes a synthetic-data-only local Phase B foundation, explicitly excluding production integration and real payment confirmation.
5. The repository owner resolves/preserves the unrelated worktree changes and approves an isolated branch or repository.
6. The technical lead approves the local container baseline, supported dependency policy and CI security gates.

Under this conditional authorization, work is limited to the “Safe foundation work” in section 8.

### Gate 2 — Expand local Phase B beyond generic foundation

Approve M1–M12 sufficiently to finalize identity, data-access and audit behavior. Policy-dependent migrations must not be finalized before the relevant decision is signed.

### Gate 3 — Permit staging integration

Resolve T1–T7 and T11–T12, approve a staging platform, complete privacy/security review, and provide provider sandbox evidence where payment work is in scope.

### Gate 4 — Permit production integration

Complete provider/bank approvals, infrastructure proof, TLS and routing validation, backup restore, UAT, security review, reconciliation trial, pilot, rollback rehearsal and formal go-live authorization.

## 11. Final readiness verdict

# NO-GO

**Phase B must not begin at this time.** The architecture is suitable as a review baseline, but Phase A's explicit exit conditions remain open: management approval, accountable owners, core financial/privacy policies and hosting-route confirmation are not evidenced.

**Recommended next action:** obtain the Gate 1 authorization package. Once signed, the status can become **CONDITIONAL GO** for isolated, synthetic-data-only foundation work. This would still not authorize provider integration, staging deployment, `/paypoint/` routing, DNS/TLS changes, cPanel modifications or use of real patient/financial data.
