# Shared hospital cash points

The requested collection points are `Main cash-point 1`, `Main cash-point 2`, and `A&E Cash-point`.

Common migrations 0008 and 0009 support and provision these as active, hospital-wide points with no daily collection limit. A null department means shared; a null daily limit means unlimited. Existing points outside these three names keep their assignments and limits. Existing matching names are reused and their prior department/limit configuration is recorded in the audit log. No staff accounts, departments, prices or payments are created.

The signed-in collection officer remains recorded on every payment. Shared points do not widen patient, service, invoice, receipt or payment visibility. Standing order approval and order capacity checks remain in force. Non-global users see only their own orders at shared points.

Deploy the backend source and image through the existing isolated PayPoint Compose configuration. Take a database backup first. Apply migrations in the updated PayPoint web container:

```sh
docker exec imsuth-paypoint-web-1 python manage.py migrate --plan
docker exec imsuth-paypoint-web-1 python manage.py migrate --noinput
```

Verify the three named points in Record Payment after refreshing the page. The new names become available only after backend deployment and migrations; pushing the frontend alone does not create live database records. Do not restart or replace shared host proxies, databases or unrelated applications.

The provisioning migration does not delete cash points on reversal because payments may reference them. Restoring older code with non-null assumptions requires a reviewed data compatibility plan; do not blindly reverse nullable fields once shared points exist.
