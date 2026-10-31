"""Synthetic acceptance sequences A–H. Provider evidence is deterministic, never live banking."""
import hashlib,hmac,json
from datetime import timedelta
from unittest.mock import patch
from django.test import TestCase,override_settings
from django.utils import timezone
from rest_framework.test import APIClient
from apps.accounts.models import User
from apps.auditlog.models import AuditEvent
from apps.billing.models import Invoice
from apps.payments.models import Payment,Receipt
from apps.operations.models import ReconciliationItem
from . import test_revenue_api as fixtures
from .models import CashApprovalLimit,ServiceDelivery
from .tasks import detect_reconciliation_alerts


@override_settings(ENVIRONMENT='development',PAYMENT_TEST_MODE=True,TEST_WEBHOOK_SECRET='phase-j-synthetic-secret')
class PhaseJFinancialWorkflows(TestCase):
    @classmethod
    def setUpTestData(cls):fixtures.RevenueControlTests.setUpTestData.__func__(cls)
    def setUp(self):self.api=APIClient();self.api.force_authenticate(self.cashier)
    def post(self,path,data):return self.api.post('/api/v1/'+path+'/',data,format='json')
    def intent(self,key='phase-j-intent'):
        invoice=self.post('invoices',{'patient':str(self.patient.pk),'department':str(self.dep.pk),'items':[{'service':str(self.service.pk)}],'idempotency_key':key+'-invoice'})
        self.assertEqual(invoice.status_code,201,invoice.data)
        result=self.post('payments',{'invoice':invoice.data['id'],'channel':'online','idempotency_key':key})
        self.assertEqual(result.status_code,201,result.data);return result.data
    def evidence(self,payment):
        body=json.dumps({'event_id':'phase-j-'+payment['id'],'payment_reference':payment['reference'],'provider_reference':'SYNTHETIC-'+payment['id'],'status':'successful','amount':payment['amount'],'currency':'NGN'},separators=(',',':')).encode()
        signature=hmac.new(b'phase-j-synthetic-secret',body,hashlib.sha256).hexdigest()
        client=APIClient()
        return client.post('/api/v1/payments/test-webhook/',body,content_type='application/json',HTTP_X_TEST_SIGNATURE=signature)
    def test_A_patient_tariff_invoice_pending(self):
        self.assertEqual(self.api.get('/api/v1/patients/search/',{'search':self.patient.patient_id}).data['count'],1)
        self.assertEqual(str(self.api.get(f'/api/v1/services/{self.service.pk}/tariff/').data['amount']),'100.00')
        payment=self.intent();self.assertEqual(payment['status'],'pending')
        self.assertFalse(Receipt.objects.filter(payment_id=payment['id']).exists())
    def test_B_D_confirm_receipt_deliver_once(self):
        payment=self.intent();self.assertEqual(self.evidence(payment).status_code,200)
        receipt=Receipt.objects.get(payment_id=payment['id'])
        self.assertEqual(self.api.get(f'/api/v1/receipts/{receipt.pk}/print/').status_code,200)
        self.api.force_authenticate(self.supervisor)
        checked=self.post(f'department-desk/receipts/{receipt.receipt_number}/verify',{})
        self.assertTrue(checked.data['eligible_for_delivery'])
        item=checked.data['items'][0]['id'];path=f'department-desk/service-items/{item}/deliver'
        self.assertEqual(self.post(path,{'receipt':str(receipt.pk),'notes':'Synthetic service delivered'}).status_code,201)
        self.assertEqual(self.post(path,{'receipt':str(receipt.pk)}).status_code,400)
        self.assertEqual(ServiceDelivery.objects.filter(item_id=item).count(),1)
    def test_C_duplicate_intent_and_provider_evidence(self):
        payment=self.intent()
        again=self.post('payments',{'invoice':payment['invoice'],'channel':'online','idempotency_key':'phase-j-intent'})
        self.assertEqual(again.status_code,201,again.data)
        self.assertEqual(again.data['id'],payment['id'])
        self.assertTrue(self.evidence(payment).data['processed'])
        self.assertFalse(self.evidence(payment).data['processed'])
        self.assertEqual(Receipt.objects.filter(payment_id=payment['id']).count(),1)
    def test_E_future_tariff_independent_and_historical_snapshot(self):
        self.api.force_authenticate(self.finance);effective=timezone.now()+timedelta(days=1)
        proposal=self.post(f'services/{self.service.pk}/tariff-proposals',{'amount':'200','effective_from':effective.isoformat(),'reason':'Synthetic approved policy'})
        path=f"tariff-proposals/{proposal.data['id']}/approve"
        self.assertEqual(self.post(path,{'notes':'Self approval rejected'}).status_code,403)
        self.api.force_authenticate(self.admin);self.assertEqual(self.post(path,{'notes':'Independent review complete'}).status_code,200)
        with patch('django.utils.timezone.now',return_value=effective+timedelta(minutes=1)):
            result=self.api.get(f'/api/v1/services/{self.service.pk}/tariff/')
            self.assertEqual(str(result.data['amount']),'200.00')
            self.assertEqual(self.invoice.items.get().unit_amount,100)
    def test_F_order_approval_collection_is_not_deposit(self):
        order=self.post('cash-orders',{'cash_point':str(self.point.pk),'amount':'50','purpose':'Synthetic cash authorization','idempotency_key':'phase-j-cash'})
        self.assertEqual(order.status_code,201,order.data)
        CashApprovalLimit.objects.create(role='finance',amount='500',approved_by=self.admin,policy_reference='SYNTHETIC UAT ONLY')
        self.api.force_authenticate(self.finance)
        self.assertEqual(self.post(f"cash-orders/{order.data['id']}/approve",{'notes':'Independent synthetic evidence'}).status_code,200)
        evidence=self.post(f'cash-points/{self.point.pk}/collections',{'payment':str(self.payment.pk),'evidence_reference':'Synthetic ledger entry'})
        self.assertEqual(evidence.status_code,201)
        result=self.api.get(f'/api/v1/cash-points/{self.point.pk}/collections/').data['results'][0]
        self.assertIsNone(result['bank_settled']);self.assertEqual(self.payment.status,'confirmed')
    def test_G_reconciliation_alert_review_resolution(self):
        from apps.operations.models import ReconciliationBatch
        batch=ReconciliationBatch.objects.create(source='Synthetic',period_start=timezone.localdate(),period_end=timezone.localdate(),file_digest='b'*64,imported_by=self.finance)
        row=ReconciliationItem.objects.create(batch=batch,external_reference='UNKNOWN-SYNTHETIC',amount='50',transaction_date=timezone.now())
        self.assertEqual(detect_reconciliation_alerts.run(),1)
        self.api.force_authenticate(self.finance)
        alert=self.api.get('/api/v1/alerts/',{'alert_type':'reconciliation_discrepancy'}).data['results'][0]
        for action,data in [('assign',{'assigned_to':self.finance.pk}),('start-review',{}),('resolve',{'notes':'Documented synthetic review, underlying reconciliation remains separate'})]:
            self.assertEqual(self.post(f"alerts/{alert['id']}/{action}",data).status_code,200)
        row.refresh_from_db();self.assertEqual(row.status,'unmatched')
    def test_H_user_role_login_audit(self):
        self.api.force_authenticate(self.admin)
        result=self.post('users',{'username':'phase-j-new-user','first_name':'Synthetic','last_name':'User','role':'cashier','department':str(self.dep.pk),'password':'Synthetic-UAT-Login-2026!'})
        self.assertEqual(result.status_code,201,result.data)
        client=APIClient();login=client.post('/api/v1/session/login/',{'username':'phase-j-new-user','password':'Synthetic-UAT-Login-2026!'},format='json')
        self.assertEqual(login.status_code,200);self.assertEqual(login.data['user']['role'],'cashier')
        self.assertTrue(AuditEvent.objects.filter(actor_id=result.data['id'],action='account.login').exists())
        self.assertNotIn('Synthetic-UAT-Login-2026!',str(list(AuditEvent.objects.values('metadata','reason'))))
