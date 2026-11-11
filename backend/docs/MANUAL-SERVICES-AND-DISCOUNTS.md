# Manual payment services and patient types

Record Payment now accepts a typed service description and full service price for one service. Regular patients pay 100%; NHIS and IMSHIA receive 10% off the entered full price. Discounts round half up to the nearest kobo on the backend. The frontend displays the full price, discount, and net amount due. This is a recorded patient-type choice, not a verification of insurance membership.

The manual API payload uses `service_description`, `base_amount`, `patient_type` (`regular`, `nhis`, `imshia`), and `amount` (net). Omit `service`. The server rejects an altered net amount. Manual entries are immutable invoice line snapshots with `is_manual=true` and no catalogue service or tariff links. They create no permanent catalogue records or approved tariffs. Every manual entry creates a review alert and records full price, discount, patient type, operator and description in the audit history. A submitted reference never verifies payment or issues a paid receipt.

Existing service-ID requests continue to work. For them the server takes the full price from the approved current tariff rather than the supplied base amount; existing explicit price override review rules remain.

Deploy the backend first, apply the new billing and common migrations, and deploy the frontend. The frontend checks the backend capability before enabling this new flow. In the updated web container:

```sh
docker exec imsuth-paypoint-web-1 python manage.py migrate --plan
docker exec imsuth-paypoint-web-1 python manage.py migrate --noinput
```

Back up the database using the existing deployment procedure first. Do not reverse the nullable service/tariff fields after manual invoice items exist without a reviewed data compatibility plan. Existing invoice items and historical payments are unchanged.
