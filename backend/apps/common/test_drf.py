from decimal import Decimal
from uuid import uuid4
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient
from apps.billing.models import Invoice
from .models import CashPoint, RecordedPayment
from .test_revenue_api import RevenueControlTests
from .drf import CATALOGUE

class DRFPaymentTests(TestCase):
    @classmethod
    def setUpTestData(cls):RevenueControlTests.setUpTestData.__func__(cls)
    def setUp(self):
        self.client=APIClient();self.client.force_authenticate(self.cashier)
        self.data={'patient_name':'Synthetic pharmacy patient','department':str(self.dep.pk),'sub_head':'drf','cash_point':str(CashPoint.objects.get(name='OPD CASH POINT').pk),'quantity':1,'channel':'cash','amount':'1700','payment_received':True,'drf_items':[{'code':'pharmacy_001','quantity':2},{'code':'pharmacy_322','quantity':1}],'reported_paid_at':timezone.now().isoformat(),'idempotency_key':str(uuid4())}
    def post(self):return self.client.post('/api/v1/record-payment/',self.data,format='json')
    def test_complete_source_catalogue(self):
        rows=self.client.get('/api/v1/record-payment/').data['drf_catalogue']['items']
        self.assertEqual([r['source_number'] for r in rows],list(range(1,323)))
        self.assertEqual(sum(Decimal(r['amount']) for r in rows),Decimal('382290'))
        self.assertEqual(rows[0]['name'],'Cap Amoxil 500mg')
        self.assertEqual(rows[-1]['name'],'Sachet Floranorm')
        self.assertEqual(rows[75]['name'],rows[162]['name']) # Preserve duplicate source entries.
        self.assertTrue(all(r['kind']=='fixed' for r in rows))
    def test_multiple_items_discounts_receipt_and_idempotency(self):
        self.data.update(patient_type='nhis',amount='1530')
        response=self.post();self.assertEqual(response.status_code,201,response.data)
        context=RecordedPayment.objects.get();snapshot=context.drf_breakdown
        self.assertFalse(context.overhead_breakdown)
        self.assertEqual(snapshot['subtotal'],'1700.00');self.assertEqual(snapshot['surcharge'],'0.00')
        self.assertEqual(snapshot['discount_total'],'170.00')
        self.assertEqual(sum(i.line_total for i in context.payment.invoice.items.all()),Decimal('1530'))
        self.assertEqual(context.payment.invoice.items.count(),2)
        printed=self.client.get(f'/api/v1/receipts/{context.payment.receipt.pk}/print/')
        for text in ['DRF pharmacy charges','Cap Amoxil 500mg','Sachet Floranorm','1530.00']:self.assertContains(printed,text)
        self.assertNotContains(printed,'Over-head charges');self.assertNotContains(printed,'Surcharge (10%')
        self.assertEqual(self.post().data['payment']['id'],response.data['payment']['id'])
        self.assertEqual(RecordedPayment.objects.count(),1)
    def test_reject_tampered_prices_mixed_heads_unknown_duplicate_and_wrong_amount(self):
        before=Invoice.objects.count()
        for change in [dict(drf_items=[{'code':'pharmacy_001','quantity':1,'unit_amount':'1'}]),dict(drf_items=[{'code':'surcharge','quantity':1}]),dict(overhead_items=[{'code':'card'}]),dict(sub_head='rf'),dict(drf_items=[]),dict(drf_items=[{'code':'pharmacy_001'},{'code':'pharmacy_001'}]),dict(amount='1')]:
            original=self.data.copy();self.data.update(change,idempotency_key=str(uuid4()))
            result=self.post();self.assertEqual(result.status_code,400,result.data);self.assertEqual(Invoice.objects.count(),before);self.data=original
