# Staff login readiness

Staff creation now requires an initial password. Password fields preserve leading/trailing spaces exactly rather than silently trimming them. Updating an account without a password still preserves the current hash. Admin staff responses expose only a has_usable_password boolean, never the password or hash; the editor requires setting a password on an existing unusable account and identifies inactive accounts.

PayPoint sign-in accepts capitalization differences only if the identifier has one case-insensitive match. Exact username matches remain authoritative. Ambiguous matches, wrong passwords and inactive accounts retain the same generic failure response.

Existing accounts are not automatically activated or assigned passwords. For a live account such as PRISCAEZE, an administrator should check the saved username, active status and password readiness, then set a fresh password privately through Users and Audit or Django's interactive changepassword command. Never send passwords in chat or command arguments.

Deploy backend and frontend. No database migrations required.
