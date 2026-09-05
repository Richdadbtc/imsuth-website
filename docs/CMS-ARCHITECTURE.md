# IMSUTH CMS architecture

## Scope

The current JSON files are the canonical staging content source. A future CMS should expose the same shapes through read-only public API endpoints. CMS administration is intentionally outside the public website and must use separate authentication, authorization, audit logging and hosting.

## Content workflow

1. Author creates or imports a draft record.
2. Clinical or departmental reviewer checks institutional and medical accuracy.
3. Communications reviewer checks presentation, accessibility and media rights.
4. An authorized publisher sets `verified: true` and publishes the record.
5. The public API returns only published, verified records.
6. Edits create a new revision and preserve the audit trail.

## Core collections

- Departments and clinical services
- Clinician profiles
- Facilities
- Patient information and FAQs
- Research sections and publications
- News and events
- Careers
- Global settings and emergency information

Every record should include a stable ID, unique slug, verification state, publication state, created/updated timestamps, reviewer identity, revision number and optional scheduled publication/expiry dates.

## API contract

Public responses should preserve the current JSON field names. List endpoints must filter server-side using `verified=true` and `status=published`. Detail endpoints must return 404 for drafts, unverified records and expired content. Cache headers and ETags should be supported.

## Roles

- Author: create and edit drafts
- Reviewer: approve accuracy within assigned collections
- Publisher: publish or unpublish approved records
- Administrator: manage users, roles and configuration

No CMS role should grant access to HMS or EMR data. Clinical-system identity and permissions remain separate.

## Security and governance

- MFA for privileged accounts
- Least-privilege collection permissions
- Immutable audit events
- Media malware scanning and file-type restrictions
- Approved image rights and alt-text fields
- Preview environments blocked from indexing
- Automated backups and tested restoration
- No patient records or form submissions stored in the public CMS

## Migration sequence

Import settings first, then departments/services, facilities, patient information, clinicians, research/publications, news and careers. Run validation before each collection is made public.
