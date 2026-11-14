# User page access

Super administrators can create/edit staff through Users and Audit, Staff Management or Add Staff. Select the role first, then choose Role defaults or a custom subset of pages available to that role. Empty custom selections leave only personal profile, password, help and notifications. Super administrators always retain full access and cannot be restricted through this editor.

User.page_access stores null for role defaults or an explicit list of page identifiers. Validation rejects unknown/out-of-role pages, malformed selections and attempts to restrict the current administrator. Account creation and changes are audited without passwords. Changing roles with incompatible custom pages requires resetting the selection.

Session payloads include effective allowed_pages. Sidebar and quick links use these values. Every workspace navigation rechecks the requested page with the backend session endpoint, including direct links and known aliases. Existing sessions see changes on their next navigation/API request; refresh updates the sidebar.

For custom selections, middleware limits API resource access to resources needed by selected pages, with distinct read/write dependencies. Some screens share data resources, so page selection does not provide field-level data isolation. Existing role, object scope and financial workflow checks remain authoritative. The API currently uses Django session authentication; middleware covers both API prefixes. Personal account/support endpoints remain available under their existing permissions.

Page catalogue: apps/accounts/page_catalogue.json. Presets/dependencies: apps/accounts/page_access.py. To add a new page, update the catalogue and dependency policy with tests.

Apply accounts.0004_user_page_access before starting the updated backend. Existing accounts keep role defaults. Deploy the updated frontend after the backend.
