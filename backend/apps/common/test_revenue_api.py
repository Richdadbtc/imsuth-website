from datetime import timedelta
from decimal import Decimal
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient
from apps.accounts.models import User
from apps.auditlog.models import AuditEvent
from apps.billing.models import Invoice
from apps.catalogue.models import Department, Service, TariffVersion
from apps.registry.models import Patient
from apps.payments.models import Payment, Receipt
from .models import Alert, CashPoint, CashOrder, CashApprovalLimit, ServiceDelivery


class RevenueControlTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.dep=Department.objects.create(code='SYN',name='Synthetic department')
        cls.other=Department.objects.create(code='OTH',name='Other synthetic department')
        cls.admin=User.objects.create_user(username='synthetic-admin',role='super_admin',is_superuser=True)
        cls.finance=User.objects.create_user(username='synthetic-finance',role='finance',department=cls.dep)
        cls.cashier=User.objects.create_user(username='synthetic-cashier',role='cashier',department=cls.dep)
        cls.supervisor=User.objects.create_user(username='synthetic-supervisor',role='department_supervisor',department=cls.dep)
        cls.patient=Patient.objects.create(first_name='Synthetic',last_name='Patient',registered_by=cls.cashier)
        cls.service=Service.objects.create(code='SYN1',name='Synthetic service',department=cls.dep)
        TariffVersion.objects.create(service=cls.service,amount='100',is_approved=True,effective_from=timezone.now()-timedelta(days=1))
        cls.invoice=Invoice.create_from_items(patient=cls.patient,department=cls.dep,item_requests=[{'service':cls.service}],created_by=cls.cashier)
        cls.payment=Payment.objects.create(invoice=cls.invoice,reference='SYN-PAY',idempotency_key='SYN-PAY',channel='cash',amount='100',status='confirmed',confirmed_at=timezone.now(),initiated_by=cls.cashier)
        cls.invoice.status='paid';cls.invoice.amount_paid='100';cls.invoice.save()
        cls.receipt=Receipt.objects.create(payment=cls.payment,invoice=cls.invoice,receipt_number='SYN-RECEIPT',verification_token='synthetic-token',amount='100')
        cls.point=CashPoint.objects.create(name='Synthetic desk',location='Test block',department=cls.dep,assigned_officer=cls.cashier,daily_limit='1000')
        cls.alert=Alert.objects.create(department=cls.dep,alert_type='unmatched_payment',severity='critical',description='Synthetic alert')
    def setUp(self):
        self.client=APIClient();self.client.force_authenticate(self.finance)
    def path(self,p):return '/api/v1/'+p+'/'
    def post(self,p,data):return self.client.post(self.path(p),data,format='json')
    def test_all_groups_require_authentication(self):
        self.client.force_authenticate(None)
        for p in ['dashboard/summary','department-desk/receipts','cash-points','cash-orders','alerts','users','audit-logs']:
            self.assertIn(self.client.get(self.path(p)).status_code,[401,403],p)
    def test_compatibility_prefix(self):
        self.assertEqual(self.client.get('/paypoint/api/v1/dashboard/summary/').status_code,200)
    def test_pending_not_collected(self):
        Payment.objects.create(invoice=self.invoice,reference='SYN-PENDING',idempotency_key='SYN-PENDING',channel='pos',amount='900',initiated_by=self.cashier)
        data=self.client.get(self.path('dashboard/summary')).data
        self.assertEqual(data['verified_collections'],Decimal('100'))
        self.assertEqual(data['pending_amount'],Decimal('900'))
    def test_department_isolation(self):
        self.client.force_authenticate(self.supervisor)
        Alert.objects.create(department=self.other,alert_type='private',severity='low',description='Other department')
        self.assertEqual(self.client.get(self.path('alerts')).data['count'],1)
        self.assertEqual(self.client.get(self.path(f'departments/{self.other.pk}')).status_code,404)
    def test_alert_resolve_notes_and_no_payment_change(self):
        self.assertEqual(self.post(f'alerts/{self.alert.pk}/resolve',{}).status_code,400)
        self.assertEqual(self.post(f'alerts/{self.alert.pk}/assign',{'assigned_to':self.finance.pk}).status_code,200)
        self.assertEqual(self.post(f'alerts/{self.alert.pk}/start-review',{}).status_code,200)
        self.assertEqual(self.post(f'alerts/{self.alert.pk}/resolve',{'notes':'Matched synthetic evidence'}).status_code,200)
        self.payment.refresh_from_db();self.assertEqual(self.payment.status,'confirmed')
        self.assertEqual(self.post(f'alerts/{self.alert.pk}/start-review',{}).status_code,400)
    def order(self,key='syn-order'):
        return self.post('cash-orders',{'cash_point':str(self.point.pk),'amount':'200','purpose':'Synthetic request','idempotency_key':key})
    def test_cash_idempotency_and_maker_checker(self):
        result=self.order();self.assertEqual(result.status_code,201,result.data)
        self.assertEqual(self.order().data['id'],result.data['id'])
        self.assertEqual(CashOrder.objects.count(),1)
        self.assertEqual(self.post(f"cash-orders/{result.data['id']}/approve",{'notes':'Synthetic approval'}).status_code,403)
        self.client.force_authenticate(self.admin)
        self.assertEqual(self.post(f"cash-orders/{result.data['id']}/approve",{'notes':'Synthetic approval'}).status_code,403)
        CashApprovalLimit.objects.create(role='super_admin',amount='1000',approved_by=self.admin,policy_reference='SYNTHETIC POLICY')
        self.assertEqual(self.post(f"cash-orders/{result.data['id']}/approve",{'notes':'Synthetic approval'}).status_code,200)
        self.assertEqual(self.post(f"cash-orders/{result.data['id']}/reject",{'notes':'Synthetic rejection'}).status_code,400)
    def test_daily_limit_reserves_pending_orders(self):
        self.assertEqual(self.order().status_code,201)
        for i in range(4):self.assertEqual(self.order(str(i)).status_code,201)
        self.assertEqual(self.order('over-limit').status_code,400)
    def test_delivery_requires_paid_receipt_and_no_duplicates(self):
        self.client.force_authenticate(self.supervisor)
        item=self.invoice.items.get();p=f'department-desk/service-items/{item.pk}/deliver'
        self.assertEqual(self.post(p,{'receipt':str(self.receipt.pk)}).status_code,201)
        self.assertEqual(self.post(p,{'receipt':str(self.receipt.pk)}).status_code,400)
        self.assertEqual(ServiceDelivery.objects.count(),1)
    def test_delivery_rejected_for_pending_payment(self):
        self.client.force_authenticate(self.supervisor)
        self.payment.status='pending';self.payment.save()
        self.assertEqual(self.post(f'department-desk/service-items/{self.invoice.items.get().pk}/deliver',{'receipt':str(self.receipt.pk)}).status_code,404)
    def test_tariff_proposal_independent_approval_snapshot(self):
        original=self.invoice.items.get().unit_amount
        result=self.post(f'services/{self.service.pk}/tariff-proposals',{'amount':'200','effective_from':(timezone.now()+timedelta(days=1)).isoformat(),'reason':'Synthetic policy change'})
        self.assertEqual(result.status_code,201,result.data)
        path=f"tariff-proposals/{result.data['id']}/approve"
        self.assertEqual(self.post(path,{'notes':'Independent approval'}).status_code,403)
        self.client.force_authenticate(self.admin)
        self.assertEqual(self.post(path,{'notes':'Independent approval'}).status_code,200)
        self.assertEqual(self.invoice.items.get().unit_amount,original)
    def test_users_audit_are_admin_controlled(self):
        self.assertEqual(self.client.get(self.path('users')).status_code,403)
        self.client.force_authenticate(self.admin)
        user=self.post('users',{'username':'synthetic-new','role':'cashier'})
        self.assertEqual(user.status_code,201,user.data)
        self.assertNotIn('password',user.data)
        self.assertEqual(self.post(f"users/{user.data['id']}/deactivate",{}).status_code,200)
        self.assertEqual(self.client.delete(self.path('audit-logs/'+str(AuditEvent.objects.first().pk))).status_code,405)
    def test_search_pagination_dates(self):
        self.assertEqual(self.client.get(self.path('alerts')+'?search=not-present').data['count'],0)
        self.assertEqual(self.client.get(self.path('alerts')+'?date_from=2027-01-01&date_to=2026-01-01').status_code,400)
        self.assertEqual(self.client.get(self.path('cash-points')+'?page=999').status_code,404)
    def test_cashier_cannot_resolve_alert(self):
        self.client.force_authenticate(self.cashier)
        self.assertEqual(self.post(f'alerts/{self.alert.pk}/resolve',{'notes':'Synthetic note'}).status_code,403)
    def test_unknown_tariff_category_is_not_discounted(self):
        response=self.client.get(self.path(f'services/{self.service.pk}/tariff')+'?patient_category=nhis')
        self.assertEqual(response.status_code,400)

    def test_reference_submission_does_not_confirm(self):
        self.client.force_authenticate(self.cashier)
        invoice=Invoice.create_from_items(patient=self.patient,department=self.dep,item_requests=[{'service':self.service}],created_by=self.cashier)
        response=self.post('payments',{'invoice':str(invoice.pk),'channel':'pos','idempotency_key':'reference-only','submitted_reference':'SYNTHETIC-REFERENCE'})
        self.assertEqual(response.status_code,201,response.data)
        self.assertEqual(response.data['status'],'awaiting_offline_verification')
        self.assertFalse(Receipt.objects.filter(payment_id=response.data['id']).exists())
    def test_cash_evidence_is_explicit_and_not_deposit(self):
        p=f'cash-points/{self.point.pk}/collections'
        result=self.post(p,{'payment':str(self.payment.pk),'evidence_reference':'Synthetic cash ledger entry'})
        self.assertEqual(result.status_code,201,result.data)
        self.assertEqual(self.post(p,{'payment':str(self.payment.pk),'evidence_reference':'Synthetic cash ledger entry'}).status_code,200)
        summary=self.client.get(self.path(f'cash-points/{self.point.pk}/summary')).data
        self.assertEqual(summary['collections'],Decimal('100'))
        self.payment.refresh_from_db();self.assertEqual(self.payment.status,'confirmed')
    def test_dashboard_and_nested_read_contracts(self):
        for metric in ['summary','collections-by-channel','collections-by-department','payment-status','recent-transactions','alerts-summary','trends']:
            self.assertEqual(self.client.get(self.path('dashboard/'+metric)).status_code,200,metric)
        for resource in ['summary','collections','transactions','services','staff','trends']:
            self.assertEqual(self.client.get(self.path(f'departments/{self.dep.pk}/{resource}')).status_code,200,resource)
        self.assertEqual(self.client.get(self.path(f'receipts/{self.receipt.pk}/print')).status_code,200)
    def test_audit_redacts_sensitive_metadata(self):
        event=AuditEvent.record('synthetic.redaction',metadata={'password':'never-store','nested':{'verification_code':'654321','safe':'kept'}})
        self.assertNotIn('never-store',str(event.metadata));self.assertNotIn('654321',str(event.metadata))
    def test_template_is_live_vanilla_client(self):
        result=self.client.get('/paypoint/')
        self.assertEqual(result.status_code,200)
        self.assertContains(result,'static/paypoint/config.js')
        self.assertNotContains(result,'demoMode')
        self.assertNotContains(result,'Synthetic data only')
        self.assertNotContains(result,'src="config.js')

    def test_cash_point_creation_validates_officer_department(self):
        self.assertEqual(self.client.get(self.path('cash-points/officers')).status_code,200)
        bad=self.post('cash-points',{'name':'Other desk','location':'Test block','department':str(self.other.pk),'assigned_officer':self.cashier.pk,'daily_limit':'500'})
        self.assertEqual(bad.status_code,400)
        good=self.post('cash-points',{'name':'Other desk','location':'Test block','department':str(self.dep.pk),'assigned_officer':self.cashier.pk,'daily_limit':'500'})
        self.assertEqual(good.status_code,201,good.data)
    def test_detector_is_idempotent_and_does_not_verify(self):
        from apps.operations.models import ReconciliationBatch, ReconciliationItem
        from .tasks import detect_reconciliation_alerts
        batch=ReconciliationBatch.objects.create(source='Synthetic',period_start=timezone.localdate(),period_end=timezone.localdate(),file_digest='a'*64,imported_by=self.finance)
        ReconciliationItem.objects.create(batch=batch,external_reference='Synthetic-unmatched',amount='150',transaction_date=timezone.now())
        self.assertEqual(detect_reconciliation_alerts.run(),1)
        self.assertEqual(detect_reconciliation_alerts.run(),0)
        self.payment.refresh_from_db();self.assertEqual(self.payment.status,'confirmed')

    def test_overview_coverage_uses_confirmed_channels_and_scoped_statement_rows(self):
        from apps.operations.models import ReconciliationBatch, ReconciliationItem
        batch=ReconciliationBatch.objects.create(source='Synthetic',period_start=timezone.localdate(),period_end=timezone.localdate(),file_digest='synthetic-overview',imported_by=self.finance)
        for reference,state,payment in [('matched','matched',self.payment),('open','unmatched',self.payment),('unlinked','unmatched',None)]:
            ReconciliationItem.objects.create(batch=batch,external_reference=reference,amount='100',transaction_date=timezone.now(),payment=payment,status=state)
        Payment.objects.create(invoice=self.invoice,reference='SYN-COVERAGE-PENDING',idempotency_key='SYN-COVERAGE-PENDING',channel='pos',amount='900',initiated_by=self.cashier)
        result=self.client.get(self.path('dashboard/overview-coverage')).data
        self.assertEqual(result['channels'][0]['amount'],Decimal('100'))
        self.assertEqual(result['daily_channels'][0]['channel'],'cash')
        self.assertEqual(result['reconciliation']['total'],3)
        self.assertEqual(result['reconciliation']['matched'],1)
        self.assertEqual(result['reconciliation']['unmatched_amount'],Decimal('200'))
        self.client.force_authenticate(self.supervisor)
        result=self.client.get(self.path('dashboard/overview-coverage')).data
        self.assertEqual(result['reconciliation']['total'],2)
        self.client.force_authenticate(None)
        self.assertIn(self.client.get(self.path('dashboard/overview-coverage')).status_code,[401,403])

    def test_scheduled_reconciliation_detector_only_alerts_aged_rows_once(self):
        from apps.operations.models import ReconciliationBatch, ReconciliationItem
        from .tasks import detect_reconciliation_alerts
        batch=ReconciliationBatch.objects.create(source='Synthetic',period_start=timezone.localdate(),period_end=timezone.localdate(),file_digest='synthetic-aged-overview',imported_by=self.finance)
        for reference,age in [('old',25),('recent',1)]:
            ReconciliationItem.objects.create(batch=batch,external_reference=reference,amount='100',transaction_date=timezone.now()-timedelta(hours=age),payment=self.payment,status='unmatched')
        self.assertEqual(detect_reconciliation_alerts.run(min_age_hours=24),1)
        self.assertEqual(detect_reconciliation_alerts.run(min_age_hours=24),0)
