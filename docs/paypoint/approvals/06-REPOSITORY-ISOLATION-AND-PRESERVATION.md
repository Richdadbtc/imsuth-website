# Gate 1.6 — Git Repository Isolation and Website Preservation Checklist

**Status:** PENDING — no repository operation is authorized by this document  
**Decision requested:** Preserve all current public-website work and approve an isolated location for future PayPoint development.

## Current evidence

At the time of the readiness review, the repository contained numerous modified and untracked public-site files, including deployment files, HTML pages, assets and the Phase A/readiness documents. These changes belong to the project owner and must not be discarded, overwritten or silently combined with PayPoint implementation.

## Isolation options

| Option | Description | Preservation characteristics | Recommendation |
|---|---|---|---|
| Separate private repository | Create a dedicated PayPoint repository with its own access, CI/CD and release approvals. | Strongest separation from the public static deployment; cleanest secret and permission boundary. | Preferred for a patient/financial application. |
| Isolated branch in current repository | Preserve current work first, then create an approved `codex/` or project branch and keep PayPoint under a separate top-level directory. | Easier shared branding/history, but access and CI/CD boundaries are weaker and accidental static deployment must be prevented. | Acceptable for local foundation work with strict allowlists and branch protection. |
| Git worktree from approved branch | Use an additional working directory tied to an isolated branch after current changes are preserved. | Prevents filesystem overlap during development but remains one repository/security boundary. | Useful implementation mechanism, not a substitute for approval. |

## Preservation and isolation checklist

| ID | Required decision/action | Accountable approver | Evidence of approval/completion | Acceptance criteria | Status |
|---|---|---|---|---|---|
| R1 | Identify repository owner and authorized maintainers. | IMSUTH System Owner | Ownership/access record | Named owner and least-privilege maintainer list recorded. | PENDING |
| R2 | Inventory current tracked modifications and untracked files before any branch/repository action. | Repository Owner; Technical Lead responsible | Dated `git status`, diff summary and file inventory stored in decision record | All user changes are visible; no cleanup/reset has occurred. | PENDING |
| R3 | Preserve existing work through an owner-approved commit, patch/archive or other recoverable method. | Repository Owner | Commit ID and/or verified backup/patch location | Preservation can be restored and does not expose secrets; owner confirms completeness. | PENDING |
| R4 | Confirm no credentials, real data or private PayPoint artifacts exist in current history/worktree. | Security Owner | Secret-scan/data review report | Findings resolved or formally contained before new work. | PENDING |
| R5 | Select separate repository, isolated branch or worktree approach. | Repository Owner and System Owner | Signed technical decision | Location, visibility, access and naming are recorded; separate repository is preferred. | PENDING |
| R6 | Prevent PayPoint files from entering the existing cPanel static deployment allowlist. | Technical Delivery Lead | Deployment-boundary review/test | Current `.cpanel.yml` and static workflow cannot publish PayPoint source, secrets or private data. | PENDING |
| R7 | Define branch protection and review rules. | Repository Owner with Security concurrence | Repository settings evidence/policy | Protected main/release branches, required review/checks and restricted force-push/deletion are defined. | PENDING |
| R8 | Define separate PayPoint CI/CD and secret boundary. | Technical Delivery Lead with Security concurrence | Approved CI/CD design | Static-site deployment cannot deploy PayPoint; secrets are environment-scoped and production needs manual approval. | PENDING |
| R9 | Verify public website baseline remains reproducible and unchanged by isolation. | Repository Owner and Website Owner | Baseline commit, validation result and backup reference | Existing site can be restored/deployed; no page, asset, form or routing change resulted from isolation. | PENDING |
| R10 | Approve the isolated development location. | System Owner and Repository Owner | Signed checklist/decision reference | R1–R9 accepted; developers receive only required access. | PENDING |

## Prohibited repository actions before approval

- Do not run destructive reset, clean, checkout/restore or history-rewrite operations.
- Do not discard, overwrite or commit unrelated user changes without owner review.
- Do not add PayPoint code to the cPanel deployment allowlist.
- Do not push a PayPoint foundation directly to the public website's production branch.
- Do not store production secrets, patient/payment data, private keys or provider payloads in Git.

## Selected isolation decision

**Selected option:** PENDING — _______________________________________________  
**Approved repository/path/branch:** _________________________________________  
**Preservation evidence:** ___________________________________________________  
**Baseline public-site commit:** ______________________________________________  
**Access-control reference:** _________________________________________________

| Approver | Decision | Date | Signature / evidence reference |
|---|---|---|---|
| IMSUTH System Owner | PENDING |  |  |
| Repository Owner | PENDING |  |  |
| Website Owner | PENDING |  |  |
| Security Owner concurrence | PENDING |  |  |
| Technical Delivery Lead | PENDING |  |  |

**Document acceptance:** Approved only when current website work is demonstrably recoverable, the isolation boundary is selected, and PayPoint content is prevented from entering the static production deployment.
