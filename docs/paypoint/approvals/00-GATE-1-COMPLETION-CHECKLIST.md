# Phase B Gate 1 Completion Checklist

**Overall status:** PENDING / NO-GO  
**Rule:** Gate 1 is complete only when every mandatory row is supported by documentary evidence and accepted by the Gate Reviewer.

## Gate decisions

| Gate item | Required decision | Accountable approver | Required evidence | Acceptance criteria | Status |
|---|---|---|---|---|---|
| G1.1 Architecture | Approve the Phase A architecture in principle for local foundation work. | IMSUTH Executive Sponsor/CMD or formally delegated authority | Signed `01-ARCHITECTURE-APPROVAL.md` plus decision-register reference | Scope, exclusions, trust boundaries and financial-control principles are explicitly accepted; deviations are resolved or documented. | PENDING |
| G1.2 Ownership | Assign named accountable owners for System/Product, Finance, Privacy, Security and System Administration/Operations. | Executive Sponsor/CMD | Signed `02-RESPONSIBILITY-AND-OWNERSHIP.md`; appointment memo or approved minutes | Every mandatory role has one accountable owner, a deputy/escalation path and accepted duties; incompatible duties are not combined without approved mitigation. | PENDING |
| G1.3 Controls | Approve the initial least-privilege, segregation-of-duties and synthetic-data prohibition baseline. | Finance Owner, Privacy Owner, Security Owner and Executive Sponsor | Signed `03-FINANCIAL-AND-ACCESS-CONTROL-POLICY.md` | Every Gate 1 control is accepted; unresolved financial policies remain disabled and do not block generic foundation work. | PENDING |
| G1.4 Hosting direction | Record the preferred production routing direction and authorize only the required provider discovery. | Executive Sponsor and IMSUTH IT/System Owner; Finance/procurement if spending is committed | Signed `04-HOSTING-DECISION.md`; host response and procurement reference where applicable | A preferred option and fallback are selected; no implementation is implied; outstanding evidence, budget owner and decision date are recorded. | PENDING |
| G1.5 Local development | Authorize isolated local development using synthetic data only and list explicit exclusions. | Executive Sponsor/System Owner, Privacy Owner and Security Owner | Signed `05-LOCAL-DEVELOPMENT-AUTHORIZATION.md` | Scope is limited to readiness report Section 8 safe foundation work; real data, payment confirmation and deployment are prohibited. | PENDING |
| G1.6 Repository isolation | Approve and verify a branch/repository isolation method that preserves existing public-site work. | Repository Owner and Technical Delivery Lead | Completed `06-REPOSITORY-ISOLATION-AND-PRESERVATION.md`; status/diff/backup references | Existing changes are inventoried and recoverable; no destructive Git operation occurred; PayPoint work has an approved isolated location. | PENDING |
| G1.7 Technical baseline | Approve local containers, supported dependency policy and CI security gates. | Technical Delivery Lead; Security Owner concurs on gates | Technical decision record linked from local authorization form | PostgreSQL/Redis/Django/Celery are isolated locally; dependencies are locked; tests, migration checks, secret and dependency scanning are required. | PENDING |

## Completion verification

The Gate Reviewer must verify all of the following:

- [ ] All mandatory rows above show approved documentary evidence.
- [ ] Signatories match the owners formally assigned by IMSUTH.
- [ ] Conditional approvals have tracked conditions and do not weaken Gate 1 boundaries.
- [ ] No approval purports to authorize production integration or real data.
- [ ] The approved development scope matches Section 8 of the readiness report.
- [ ] Repository preservation evidence was captured before any Phase B branch/repository action.
- [ ] Every evidence reference is stored in the controlled project decision register.

## Gate determination record

**Decision:** PENDING — select only after evidence review: `CONDITIONAL GO` / `NO-GO`  
**Gate Reviewer name/title:** ______________________________________________  
**Evidence register/reference:** ____________________________________________  
**Decision date:** __________________  
**Signature/digital approval:** _____________________________________________

### Acceptance rule

The only successful Gate 1 outcome is **CONDITIONAL GO for isolated synthetic-data-only Phase B foundation work**. Gate 1 cannot authorize staging, production, real patient/payment data, provider integration, official payment confirmations or infrastructure changes.
