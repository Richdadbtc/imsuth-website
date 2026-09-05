# Content migration preparation

## Inventory fields

For every existing URL record: current URL, page title, content owner, content type, last reviewed date, keep/rewrite/archive decision, destination URL, redirect status, verification owner and approval status.

## Migration rules

- Preserve only accurate, current and owned content.
- Never infer clinician qualifications, schedules, contacts or clinical instructions.
- Confirm copyright and consent for every photograph.
- Convert document-only content to accessible HTML where practical.
- Keep PDFs only when the signed or fixed-format document is authoritative.
- Assign stable IDs and slugs before import.
- Mark imported records `verified: false` until an authorized reviewer approves them.
- Validate headings, link text, alt text, dates and contact information.

## URL and redirect preparation

Capture the production URL inventory before cutover. Map each retained legacy URL to one canonical destination. Use permanent redirects only after stakeholder approval. Never redirect unrelated removed pages to the homepage.

## Acceptance checks

- Record counts reconcile with the approved inventory.
- No unverified record appears publicly.
- Internal and external links resolve.
- Media files have rights, dimensions and alt text.
- Page metadata and canonical URLs are present.
- Owners approve high-risk clinical, recruitment and privacy content.
