"""Contracts used by the live-only staff interface; no demo responder required."""
from django.test import TestCase
from rest_framework.test import APIClient
from apps.accounts.models import User
from apps.catalogue.models import Department
from apps.registry.models import Patient
from apps.billing.models import Invoice
from apps.payments.models import Payment,Receipt,ReceiptReprint
from .models import PrivateAttachment,CashCollectionEvidence
from . import test_revenue_api as fixtures

class LiveUiContracts(TestCase):
    @classmethod
    def setUpTestData(cls):fixtures.RevenueControlTests.setUpTestData.__func__(cls)
    def setUp(self):self.api=APIClient();self.api.force_authenticate(self.admin)
    def test_staff_phone_persists_on_create_and_edit(self):
        response=self.api.post('/api/v1/users/',{'username':'live-ui-staff','role':'cashier','phone':'08000000123'},format='json')
        self.assertEqual(response.status_code,201,response.data);pk=response.data['id']
        self.assertEqual(response.data['phone'],'08000000123')
        result=self.api.patch(f'/api/v1/users/{pk}/',{'phone':'08000000456'},format='json')
        self.assertEqual(result.status_code,200,result.data)
        self.assertEqual(self.api.get(f'/api/v1/users/{pk}/').data['phone'],'08000000456')
    def test_permission_choices_do_not_offer_django_admin_delegation(self):
        result=self.api.get('/api/v1/roles/permission-choices/')
        self.assertEqual(result.status_code,200,result.data)
        from django.contrib.auth.models import Permission
        ids=[r['id'] for r in result.data['results']]
        self.assertFalse(Permission.objects.filter(pk__in=ids,content_type__app_label__in=['auth','accounts']).exists())
        self.api.force_authenticate(self.cashier)
        self.assertEqual(self.api.get('/api/v1/roles/permission-choices/').status_code,403)
    def test_photo_removal_never_removes_cash_evidence_attachment(self):
        attachment=PrivateAttachment.objects.create(owner=self.finance,filename='cash-evidence',content_type='application/pdf',content=b'%PDF-SYNTHETIC')
        evidence=CashCollectionEvidence.objects.create(cash_point=self.point,payment=self.payment,recorded_by=self.finance,evidence_reference='Synthetic preserved evidence',attachment=attachment)
        self.api.force_authenticate(self.finance)
        self.assertEqual(self.api.get('/api/v1/profile/photo/').status_code,404)
        self.assertFalse(self.api.get('/api/v1/profile/').data['has_photo'])
        self.assertEqual(self.api.delete('/api/v1/profile/photo/').status_code,204)
        self.assertTrue(PrivateAttachment.objects.filter(pk=attachment.pk).exists())
        evidence.refresh_from_db();self.assertEqual(evidence.attachment_id,attachment.pk)
    def test_patient_billing_filters_do_not_mix_patients(self):
        another=Patient.objects.create(first_name='Other',last_name='Synthetic',registered_by=self.cashier)
        invoice=Invoice.objects.create(patient=another,department=self.dep,created_by=self.cashier,total_amount='100',status='issued')
        Payment.objects.create(invoice=invoice,reference='OTHER-LIVE-UI',idempotency_key='OTHER-LIVE-UI',amount='100',channel='pos',initiated_by=self.cashier)
        self.api.force_authenticate(self.finance)
        self.assertEqual(self.api.get('/api/v1/invoices/',{'patient':str(another.pk)}).data['count'],1)
        result=self.api.get('/api/v1/payments/',{'invoice__patient':str(another.pk)})
        self.assertEqual(result.data['count'],1);self.assertEqual(result.data['results'][0]['reference'],'OTHER-LIVE-UI')
        self.assertEqual(self.api.get('/api/v1/invoices/',{'status__in':'issued,partially_paid'}).data['count'],1)
    def test_receipt_verification_and_reprint_are_department_scoped(self):
        other=User.objects.create_user(username='other-department-live',role='cashier',department=self.other)
        self.api.force_authenticate(other)
        response=self.api.post('/api/v1/receipts/verify/',{'receipt_number':self.receipt.receipt_number},format='json')
        self.assertEqual(response.status_code,200);self.assertFalse(response.data['valid']);self.assertIsNone(response.data['receipt'])
        response=self.api.post('/api/v1/receipt-reprints/',{'receipt':str(self.receipt.pk),'reason':'Synthetic scope check','format':'a4'},format='json')
        self.assertEqual(response.status_code,403)
        self.assertFalse(ReceiptReprint.objects.exists())
    def test_live_shell_has_no_demo_switch(self):
        html=self.api.get('/paypoint/').content.decode()
        self.assertNotIn('demoMode',html);self.assertNotIn('Synthetic data only',html)
        self.assertIn('static/paypoint/config.js',html);self.assertNotIn('<script>window.PAYPOINT_CONFIG',html)

    def test_reported_payment_fields_persist_without_confirming(self):
        from django.utils import timezone
        from datetime import timedelta
        invoice=Invoice.create_from_items(patient=self.patient,department=self.dep,item_requests=[{'service':self.service}],created_by=self.cashier)
        self.api.force_authenticate(self.cashier)
        body={'invoice':str(invoice.pk),'channel':'online','idempotency_key':'reported-live-ui','submitted_reference':'SYNTHETIC-REPORTED','reported_paid_at':(timezone.now()-timedelta(minutes=2)).isoformat(),'remarks':'Synthetic UI remarks'}
        first=self.api.post('/api/v1/payments/',body,format='json')
        self.assertEqual(first.status_code,201,first.data)
        self.assertEqual(first.data['status'],'pending');self.assertEqual(first.data['remarks'],body['remarks'])
        again=self.api.post('/api/v1/payments/',body,format='json')
        self.assertEqual(again.status_code,201,again.data);self.assertEqual(again.data['id'],first.data['id'])
        body['remarks']='Changed request'
        self.assertEqual(self.api.post('/api/v1/payments/',body,format='json').status_code,400)
        body['idempotency_key']='future-live-ui';body['reported_paid_at']=(timezone.now()+timedelta(days=1)).isoformat()
        self.assertEqual(self.api.post('/api/v1/payments/',body,format='json').status_code,400)

    def test_receipt_paper_format_is_explicit(self):
        response=self.api.get(f'/api/v1/receipts/{self.receipt.pk}/print/',{'paper':'thermal'})
        self.assertEqual(response.status_code,200);self.assertContains(response,'size:80mm auto')
        self.assertEqual(self.api.get(f'/api/v1/receipts/{self.receipt.pk}/print/',{'paper':'unsupported'}).status_code,400)
