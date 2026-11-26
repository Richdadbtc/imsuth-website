from uuid import uuid4
from decimal import Decimal
from django.test import TestCase
from . import test_drf
from .models import RecordedPayment
from apps.billing.models import Invoice

class DepositTests(TestCase):
    @classmethod
    def setUpTestData(cls):test_drf.DRFPaymentTests.setUpTestData.__func__(cls)
    def setUp(self):
        test_drf.DRFPaymentTests.setUp(self)
        self.data.pop('drf_items')
        self.data.update(sub_head='deposit',service_description='Surgery',base_amount='5000',amount='5000')
    def post(self):return self.client.post('/api/v1/record-payment/',self.data,format='json')
    def test_deposit_exact_amount_all_patient_types_receipt_and_retry(self):
        self.assertIn({'value':'deposit','label':'Deposit'},self.client.get('/api/v1/record-payment/').data['sub_heads'])
        for patient_type in ['regular','nhis','imshia']:
            self.data.update(patient_type=patient_type,idempotency_key=str(uuid4()))
            response=self.post();self.assertEqual(response.status_code,201,response.data)
            context=RecordedPayment.objects.get(payment_id=response.data['payment']['id'])
            self.assertEqual(context.discount_total,0);self.assertEqual(context.payment.amount,Decimal('5000'))
            self.assertEqual(context.payment.invoice.items.get().service_code,'DEPOSIT')
            printed=self.client.get(f'/api/v1/receipts/{context.payment.receipt.pk}/print/')
            self.assertContains(printed,'Official deposit receipt');self.assertContains(printed,'Deposit toward: Surgery')
            self.assertEqual(self.post().data['payment']['id'],response.data['payment']['id'])
    def test_invalid_deposits_cannot_create_invoices(self):
        original=self.data.copy();before=Invoice.objects.count()
        for change in [dict(service_description=''),dict(base_amount='0'),dict(amount='4500'),dict(quantity=2),dict(service=str(self.service.pk)),dict(drf_items=[{'name':'Drug','unit_amount':'5000'}])]:
            self.data={**original,**change,'idempotency_key':str(uuid4())}
            response=self.post();self.assertEqual(response.status_code,400,response.data);self.assertEqual(Invoice.objects.count(),before)
