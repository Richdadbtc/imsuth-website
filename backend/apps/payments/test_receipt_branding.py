import base64
import re
from io import BytesIO
from django.test import TestCase
from rest_framework.test import APIClient
from PIL import Image
from apps.common.test_revenue_api import RevenueControlTests

class ReceiptBrandingTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        RevenueControlTests.setUpTestData.__func__(cls)

    def test_a4_and_thermal_receipts_embed_logo_and_qr_without_external_images(self):
        client=APIClient();client.force_authenticate(self.admin)
        for paper in ['a4','thermal']:
            with self.subTest(paper=paper):
                response=client.get(f'/api/v1/receipts/{self.receipt.pk}/print/?paper={paper}')
                self.assertEqual(response.status_code,200)
                html=response.content.decode()
                self.assertLess(html.index('hospital-logo" src='),html.index('Official paid receipt'))
                self.assertGreater(html.index('receipt-qr" src='),html.index('Payment:'))
                images=re.findall(r'src="data:image/png;base64,([^"]+)"',html)
                self.assertEqual(len(images),2)
                for image in images:Image.open(BytesIO(base64.b64decode(image))).verify()
                self.assertIn('Authorised staff sign-in required.',html)
                self.assertEqual(response['Cache-Control'],'private, no-store')

    def test_qr_destination_is_the_scoped_receipt_view_without_patient_details(self):
        from .receipt_assets import receipt_images
        assets=receipt_images(self.receipt)
        self.assertEqual(assets['receipt_view_url'],f'https://www.imsuth.site/paypoint/api/v1/receipts/{self.receipt.pk}/print/')
        self.assertNotIn(self.patient.patient_id,assets['receipt_view_url'])
        client=APIClient();self.assertIn(client.get(f'/api/v1/receipts/{self.receipt.pk}/print/').status_code,[401,403])

    def test_receipt_shows_paid_department_cash_point_and_recording_officer(self):
        from apps.common.models import RecordedPayment
        from uuid import uuid4
        self.cashier.first_name='Recording';self.cashier.last_name='Officer';self.cashier.save()
        self.point.assigned_officer=self.finance;self.point.save()
        self.payment.cash_receiver='Nwaele Juliet';self.payment.save()
        RecordedPayment.objects.create(idempotency_key=str(uuid4()),fingerprint='receipt-context-test',created_by=self.cashier,cash_point=self.point,payment=self.payment,approved_total='100',entered_total='100')
        client=APIClient();client.force_authenticate(self.admin)
        for paper in ['a4','thermal']:
            response=client.get(f'/api/v1/receipts/{self.receipt.pk}/print/?paper={paper}')
            self.assertContains(response,'Department paid for: '+self.dep.name)
            self.assertContains(response,'Cash point: '+self.point.name)
            self.assertContains(response,'Recorded by: Recording Officer')
            self.assertContains(response,'Cash received by: Nwaele Juliet')

    def test_legacy_receipt_does_not_invent_a_cash_point(self):
        client=APIClient();client.force_authenticate(self.admin)
        response=client.get(f'/api/v1/receipts/{self.receipt.pk}/print/')
        self.assertContains(response,'Cash point: Not recorded')
        self.assertContains(response,'Recorded by: '+self.cashier.username)
