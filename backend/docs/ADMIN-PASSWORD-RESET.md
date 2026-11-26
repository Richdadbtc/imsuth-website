# Administrator password reset

Users and Audit has a **Reset password** action for other user accounts. A centered dialog collects a new password and matching confirmation. On confirmed server success it clears the password fields and shows **Password reset successfully**. Errors remain errors and do not display success. Duplicate submissions are disabled while the request is pending.

`POST /api/v1/users/{id}/reset-password/` accepts `new_password` and `confirm_password`. It uses the existing administrator-only permission and CSRF protection, validates Django password rules, hashes the password, sets `must_change_password`, and revokes the target's existing sessions. It does not change roles, permissions or active/banned status. Deleted accounts cannot be reset. Administrators use Change Password for their own account.

Audit action `user.password_reset` records the administrator and target without passwords. The response contains only the target ID, username and confirmation message. Existing PATCH-based password edits now also revoke sessions.

Deploy backend and PayPoint frontend. No database migration is required for this change.
