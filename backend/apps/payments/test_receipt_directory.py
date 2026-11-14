from django.test import TestCase
from rest_framework.test import APIClient
from .models import Payment,Receipt,ReceiptReprint

class ReceiptDirectoryTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        from apps.common.test_revenue_api import RevenueControlTests
        RevenueControlTests.setUpTestData.__func__(cls)
    def setUp(self):
        self.client=APIClient();self.client.force_authenticate(self.admin)
    def test_register_includes_unprinted_receipts_and_searchable_walk_in_names(self):
        self.invoice.patient_name='Walk-in Receipt Example';self.invoice.save()
        result=self.client.get('/api/v1/receipts/')
        self.assertEqual(result.status_code,200,result.data)
        row=next(r for r in result.data['results'] if r['id']==str(self.receipt.pk))
        self.assertEqual(row['patient_name'],'Walk-in Receipt Example')
        self.assertEqual(row['reprint_count'],0)
        self.assertEqual(row['payment_status'],'confirmed')
        self.assertTrue(row['service_summary'])
        search=self.client.get('/api/v1/receipts/?search=Walk-in%20Receipt')
        self.assertEqual(search.data['count'],1)
        self.assertEqual(self.client.get('/api/v1/receipts/?payment='+str(self.payment.pk)).data['count'],1)
        from uuid import uuid4
        self.assertEqual(self.client.get('/api/v1/receipts/?payment='+str(uuid4())).status_code,400)
        pending=Payment.objects.create(invoice=self.invoice,reference='NO-RECEIPT-TEST',idempotency_key='NO-RECEIPT-TEST',channel='cash',amount='100',initiated_by=self.cashier)
        self.assertEqual(self.client.get('/api/v1/receipts/?payment='+str(pending.pk)).data['count'],0)
    def test_reprint_records_history_without_creating_another_receipt(self):
        before=Receipt.objects.count()
        result=self.client.post('/api/v1/receipt-reprints/',{'receipt':str(self.receipt.pk),'reason':'Patient requested another copy','format':'a4'},format='json')
        self.assertEqual(result.status_code,201,result.data)
        self.assertEqual(Receipt.objects.count(),before)
        self.assertEqual(ReceiptReprint.objects.get().printed_by_id,self.admin.pk)
        row=self.client.get('/api/v1/receipts/'+str(self.receipt.pk)+'/').data
        self.assertEqual(row['reprint_count'],1)
        self.assertEqual(self.client.get('/api/v1/receipt-reprints/?receipt='+str(self.receipt.pk)).data['count'],1)
        self.assertEqual(self.client.get('/api/v1/receipts/'+str(self.receipt.pk)+'/print/').status_code,200)
        self.payment.status='reversed';self.payment.save()
        self.assertEqual(self.client.post('/api/v1/receipt-reprints/',{'receipt':str(self.receipt.pk),'reason':'Another copy','format':'a4'},format='json').status_code,400)
    def test_other_department_receipts_remain_out_of_scope(self):
        self.client.force_authenticate(self.supervisor)
        self.invoice.department=self.other;self.invoice.save()
        result=self.client.get('/api/v1/receipts/')
        self.assertEqual(result.data['count'],0)
        self.assertEqual(self.client.get('/api/v1/receipts/'+str(self.receipt.pk)+'/print/').status_code,404)
