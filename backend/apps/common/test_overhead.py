from decimal import Decimal
from uuid import uuid4
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient
from apps.billing.models import Invoice, InvoiceItem
from apps.payments.models import Receipt
from .models import CashPoint, RecordedPayment, Alert
from .test_revenue_api import RevenueControlTests
from .overhead import CATALOGUE


class OverheadPaymentTests(TestCase):
    @classmethod
    def setUpTestData(cls):RevenueControlTests.setUpTestData.__func__(cls)
    def setUp(self):
        self.client=APIClient();self.client.force_authenticate(self.cashier)
        self.data={'patient_name':'Synthetic Over-head patient','department':str(self.dep.pk),'sub_head':'overhead','cash_point':str(CashPoint.objects.get(name='OPD CASH POINT').pk),'quantity':1,'channel':'cash','amount':'1500','payment_received':True,'overhead_items':[{'code':'consultation','quantity':1}],'reported_paid_at':timezone.now().isoformat(),'idempotency_key':str(uuid4())}
    def post(self):return self.client.post('/api/v1/record-payment/',self.data,format='json')

    def test_catalogue_fixed_prices_multiple_lines_zero_item_and_idempotency(self):
        setup=self.client.get('/api/v1/record-payment/').data
        self.assertEqual(len(setup['overhead_catalogue']['items']),56)
        self.data.update(overhead_items=[{'code':'consultation'},{'code':'folder'},{'code':'report_staff'}],amount='2500')
        result=self.post();self.assertEqual(result.status_code,201,result.data)
        context=RecordedPayment.objects.get();items=list(context.payment.invoice.items.all())
        self.assertEqual(len(items),3)
        self.assertEqual(sum(item.line_total for item in items),Decimal('2500'))
        self.assertEqual(next(item for item in items if item.service_code=='OH-report_staff').unit_amount,0)
        self.assertEqual(context.overhead_breakdown['version'],CATALOGUE['version'])
        self.assertEqual(self.post().data['payment']['id'],result.data['payment']['id'])
        self.assertEqual(RecordedPayment.objects.count(),1)
        printed=self.client.get(f'/api/v1/receipts/{context.payment.receipt.pk}/print/')
        self.assertContains(printed,'Excuse duty for staff')
        self.assertContains(printed,'Over-head subtotal: NGN 2500.00')
        self.assertFalse(Alert.objects.filter(related_id=str(context.payment_id)).exists())

    def test_total_days_tiers_surcharge_and_patient_discount_are_server_calculated(self):
        self.data.update(patient_type='nhis',overhead_items=[{'code':'doctor_ae','quantity':3},{'code':'nursing_ae','quantity':3},{'code':'surcharge'}],amount='31680')
        result=self.post();self.assertEqual(result.status_code,201,result.data)
        context=RecordedPayment.objects.get();snapshot=context.overhead_breakdown
        self.assertEqual(snapshot['subtotal'],'32000.00')
        self.assertEqual(snapshot['surcharge'],'3200.00')
        self.assertEqual(context.base_total,Decimal('35200'))
        self.assertEqual(context.discount_total,Decimal('3520'))
        self.assertEqual(sum(item.line_total for item in context.payment.invoice.items.all()),Decimal('31680'))
        self.assertIn('3 days',context.payment.invoice.items.get(service_code='OH-doctor_ae').description)
        printed=self.client.get(f'/api/v1/receipts/{context.payment.receipt.pk}/print/')
        self.assertContains(printed,'Over-head charges before patient discount')
        self.assertContains(printed,'20000.00')
        self.assertContains(printed,'3200.00')
        self.assertContains(printed,'31680.00')

    def test_editable_prices_quantities_weekly_fees_and_line_rounding(self):
        self.data.update(patient_type='imshia',overhead_items=[{'code':'phototherapy','quantity':3,'unit_amount':'0.05'},{'code':'dustbin','quantity':2}],amount='540.14')
        self.assertEqual(self.post().status_code,400)
        self.data['amount']='540.13'
        result=self.post();self.assertEqual(result.status_code,201,result.data)
        context=RecordedPayment.objects.get()
        self.assertEqual(sum(item.line_total for item in context.payment.invoice.items.all()),Decimal('540.13'))
        self.assertTrue(Alert.objects.filter(related_id=str(context.payment_id)).exists())
        self.assertEqual(context.base_total,Decimal('600.15'))
        self.assertEqual(context.discount_total,Decimal('60.02'))

    def test_rejects_tampering_bad_codes_duplicates_missing_editable_price_and_wrong_head(self):
        cases=[([{'code':'consultation','unit_amount':'1'}],'overhead'),([{'code':'unknown'}],'overhead'),([{'code':'card'},{'code':'card'}],'overhead'),([{'code':'phototherapy'}],'overhead'),([{'code':'consultation'}],'rf'),([{'code':'report_staff'}],'overhead')]
        before=Invoice.objects.count()
        for rows,head in cases:
            self.data.update(overhead_items=rows,sub_head=head,idempotency_key=str(uuid4()))
            response=self.post();self.assertEqual(response.status_code,400,response.data)
            self.assertEqual(Invoice.objects.count(),before)

    def test_operation_fees_are_fixed_and_cs_booked_unbooked_are_receipted(self):
        self.data.update(overhead_items=[{'code':'operation_minor'},{'code':'operation_elective'},{'code':'operation_unbooked'}],amount='190600')
        response=self.post();self.assertEqual(response.status_code,201,response.data)
        context=RecordedPayment.objects.get()
        printed=self.client.get(f'/api/v1/receipts/{context.payment.receipt.pk}/print/')
        self.assertContains(printed,'C/S booked');self.assertContains(printed,'C/S unbooked');self.assertContains(printed,'20600')
        self.data.update(overhead_items=[{'code':'operation_minor','unit_amount':'1'}],amount='1',idempotency_key=str(uuid4()))
        self.assertEqual(self.post().status_code,400)
