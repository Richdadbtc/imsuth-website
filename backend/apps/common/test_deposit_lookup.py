from django.test import TestCase
from rest_framework.test import APIClient
from . import test_revenue_api
from .models import RecordedPayment

class DepositLookupTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        test_revenue_api.RevenueControlTests.setUpTestData.__func__(cls)
        RecordedPayment.objects.create(payment=cls.payment,cash_point=cls.point,created_by=cls.cashier,idempotency_key='deposit-test',fingerprint='test',sub_head='deposit',approved_total=100,entered_total=100)
    def setUp(self):
        self.client=APIClient();self.client.force_authenticate(self.admin)
    def test_confirmed_deposit_amount_and_invalid_receipts(self):
        response=self.client.get('/api/v1/record-payment/',{'deposit_reference':self.receipt.receipt_number})
        self.assertEqual(response.status_code,200,response.data)
        self.assertEqual(str(response.data['amount']),'100.00')
        for reference in ['','missing']:
            self.assertEqual(self.client.get('/api/v1/record-payment/',{'deposit_reference':reference}).status_code,400)
        self.payment.status='pending';self.payment.save()
        self.assertEqual(self.client.get('/api/v1/record-payment/',{'deposit_reference':self.receipt.receipt_number}).status_code,400)
    def test_non_deposit_and_outside_department_are_rejected(self):
        self.supervisor.department=self.other;self.supervisor.save()
        self.client.force_authenticate(self.supervisor)
        self.assertEqual(self.client.get('/api/v1/record-payment/',{'deposit_reference':self.receipt.receipt_number}).status_code,400)
        self.client.force_authenticate(self.admin)
        RecordedPayment.objects.update(sub_head='rf')
        self.assertEqual(self.client.get('/api/v1/record-payment/',{'deposit_reference':self.receipt.receipt_number}).status_code,400)

    def test_payment_requires_valid_deposit_reference_and_saves_link(self):
        from . import test_record_payment
        from uuid import uuid4
        test_record_payment.RecordPaymentTests.setUp(self)
        self.data.update(override_reason='Initial deposit')
        url='/api/v1/record-payment/'
        self.assertEqual(self.client.post(url,self.data,format='json').status_code,400)
        self.data['deposit_reference']='not-a-receipt'
        self.assertEqual(self.client.post(url,self.data,format='json').status_code,400)
        self.data['deposit_reference']=self.receipt.receipt_number
        response=self.client.post(url,self.data,format='json')
        self.assertEqual(response.status_code,201,response.data)
        context=RecordedPayment.objects.get(payment_id=response.data['payment']['id'])
        self.assertEqual(context.deposit_receipt_id,self.receipt.pk)
        self.data.update(idempotency_key=str(uuid4()),override_reason='Discharge')
        self.assertEqual(self.client.post(url,self.data,format='json').status_code,400)
