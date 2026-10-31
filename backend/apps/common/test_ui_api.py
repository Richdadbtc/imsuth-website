from datetime import timedelta
from decimal import Decimal
from django.test import TestCase
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient
from apps.accounts.models import User
from apps.auditlog.models import AuditEvent
from apps.catalogue.models import Department, Service, TariffVersion
from apps.registry.models import Patient
from apps.billing.models import Invoice
from apps.payments.models import Payment
from apps.operations.models import Settlement, ReconciliationBatch, ReconciliationItem
from apps.common.models import SupportTicket, SystemConfiguration


class ScreenApiTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin=User.objects.create_user(username='admin',role='super_admin',is_superuser=True)
        cls.finance=User.objects.create_user(username='finance',role='finance')
        cls.manager=User.objects.create_user(username='manager',role='management')
        cls.auditor=User.objects.create_user(username='auditor',role='auditor')
        cls.staff=User.objects.create_user(username='staff',role='cashier')
        cls.other=User.objects.create_user(username='other',role='cashier')
        cls.department=Department.objects.create(code='LAB',name='Laboratory')
        cls.service=Service.objects.create(code='TEST',name='Test service',department=cls.department)
        cls.patient=Patient.objects.create(first_name='Test',last_name='Patient',registered_by=cls.staff)
        cls.invoice=Invoice.objects.create(patient=cls.patient,department=cls.department,created_by=cls.staff,total_amount='1000',amount_paid='1000',status='paid')
        cls.payment=Payment.objects.create(invoice=cls.invoice,reference='P-TEST',idempotency_key='KEY-TEST',channel='pos',amount='1000',status='confirmed',initiated_by=cls.staff)
    def setUp(self):
        self.client=APIClient()
        self.client.force_authenticate(self.admin)
    def url(self,path):return '/api/v1/'+path+'/'
    def post(self,path,data):return self.client.post(self.url(path),data,format='json')
    def test_all_screen_directories_and_authentication(self):
        paths=['staff','roles','settings','support-tickets','refunds','reversals','settlements','audit-events','receipt-reprints','notifications','inbox','discrepancies','capabilities','profile','help']
        for path in paths:
            self.assertEqual(self.client.get(self.url(path)).status_code,200,path)
        self.client.force_authenticate(None)
        for path in paths:
            self.assertIn(self.client.get(self.url(path)).status_code,(401,403),path)
    def test_staff_creation_hashed_password_no_disclosure(self):
        response=self.post('staff',{'username':'new','role':'cashier','password':'Secure-New-Staff-2030!'})
        self.assertEqual(response.status_code,201,response.data)
        self.assertNotIn('password',response.data)
        self.assertTrue(User.objects.get(username='new').check_password('Secure-New-Staff-2030!'))
        self.client.force_authenticate(self.staff)
        self.assertEqual(self.client.get(self.url('staff')).status_code,403)
    def test_self_profile_cannot_escalate(self):
        self.client.force_authenticate(self.staff)
        response=self.client.patch(self.url('profile'),{'first_name':'Updated','profile':{'phone':'08012345678','preferences':{'email':True}}},format='json')
        self.assertEqual(response.status_code,200,response.data)
        self.assertEqual(response.data['profile']['phone'],'08012345678')
        self.assertEqual(self.client.patch(self.url('profile'),{'role':'super_admin'},format='json').status_code,400)
    def test_ticket_owner_scope_and_replies(self):
        self.client.force_authenticate(self.staff)
        response=self.post('support-tickets',{'subject':'Cannot print','category':'Payments','message':'Printer does not respond'})
        self.assertEqual(response.status_code,201,response.data)
        pk=response.data['id']
        self.assertEqual(self.post(f'support-tickets/{pk}/reply',{'message':'Additional information'}).status_code,201)
        self.client.force_authenticate(self.other)
        self.assertEqual(self.client.get(self.url(f'support-tickets/{pk}')).status_code,404)
        self.assertEqual(self.client.patch(self.url(f'support-tickets/{pk}'),{'status':'resolved'},format='json').status_code,404)
    def test_settings_reject_secrets(self):
        self.assertEqual(self.post('settings',{'section':'hospital','values':{'name':'Hospital'}}).status_code,201)
        self.assertEqual(self.post('settings',{'section':'payments','values':{'secret':'never'}}).status_code,400)
        self.assertEqual(SystemConfiguration.objects.count(),1)
    def test_refund_approval_maker_checker(self):
        self.client.force_authenticate(self.finance)
        response=self.post('refunds',{'payment':str(self.payment.pk),'amount':'600','reason':'Duplicate charge review'})
        self.assertEqual(response.status_code,201,response.data)
        approval=response.data['approval']
        self.assertEqual(self.post('refunds',{'payment':str(self.payment.pk),'amount':'500','reason':'Second refund request'}).status_code,400)
        self.assertEqual(self.post(f'approvals/{approval}/decide',{'approved':True,'reason':'Checked receipt evidence'}).status_code,403)
        self.client.force_authenticate(self.manager)
        response=self.post(f'approvals/{approval}/decide',{'approved':True,'reason':'Checked receipt evidence'})
        self.assertEqual(response.status_code,200,response.data)
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status,'refund_pending')
        self.assertEqual(self.post(f'approvals/{approval}/decide',{'approved':True,'reason':'Repeated action'}).status_code,400)
    def test_auditor_cannot_mutate_financial_data(self):
        self.client.force_authenticate(self.auditor)
        self.assertEqual(self.post('refunds',{'payment':str(self.payment.pk),'amount':'10','reason':'Test refund request'}).status_code,403)
        self.assertEqual(self.post('tariffs',{'service':str(self.service.pk),'amount':'200','effective_from':timezone.now().isoformat()}).status_code,403)
    def test_tariff_workflow(self):
        self.client.force_authenticate(self.finance)
        response=self.post('tariffs',{'service':str(self.service.pk),'amount':'200','effective_from':timezone.now().isoformat()})
        self.assertEqual(response.status_code,201,response.data)
        pk=response.data['id']
        self.assertEqual(self.post(f'tariffs/{pk}/approve',{}).status_code,403)
        self.client.force_authenticate(self.manager)
        self.assertEqual(self.post(f'tariffs/{pk}/approve',{}).status_code,200)
        self.assertEqual(self.client.patch(self.url(f'tariffs/{pk}'),{'amount':'300'},format='json').status_code,400)
    def test_reports_and_csv(self):
        self.client.force_authenticate(self.finance)
        for name in ['revenue','daily-collection','department-revenue','cashier-collection','payment-channel','outstanding-invoices','settlements','reconciliation','audit','system-activity','patient-registration']:
            response=self.client.get(self.url('reports/'+name))
            self.assertEqual(response.status_code,200,(name,getattr(response,'data',None)))
            self.assertIn('summary',response.data)
        response=self.client.get(self.url('reports/revenue')+'?format=csv')
        self.assertEqual(response.status_code,200)
        self.assertIn('text/csv',response['Content-Type'])
        self.assertEqual(self.client.get(self.url('reports/revenue')+'?from=invalid').status_code,400)
    def test_in_app_notifications_are_owner_scoped(self):
        response=self.post('notifications',{'event_type':'system','subject':'Update','body':'System update','channel':'in_app'})
        self.assertEqual(response.status_code,201,response.data)
        pk=response.data['id']
        self.assertEqual(self.post(f'notifications/{pk}/enqueue',{'users':[self.staff.pk]}).status_code,200)
        self.client.force_authenticate(self.staff)
        inbox=self.client.get(self.url('inbox')).data
        self.assertEqual(inbox['count'],1)
        self.client.force_authenticate(self.other)
        self.assertEqual(self.client.get(self.url('inbox')).data['count'],0)
    def test_audit_readonly_and_password_not_logged(self):
        response=self.post('staff',{'username':'logtest','role':'cashier','password':'Secure-New-Staff-2030!'})
        self.assertEqual(response.status_code,201)
        self.assertNotIn('Secure-New-Staff-2030!',str(list(AuditEvent.objects.values())))
        self.assertEqual(self.post('audit-events',{}).status_code,405)
    def test_provider_verification_fails_closed(self):
        self.payment.status='pending';self.payment.save()
        self.staff.department=self.department;self.staff.save(update_fields=['department'])
        self.client.force_authenticate(self.staff)
        self.assertEqual(self.post(f'payments/{self.payment.pk}/verify',{}).status_code,503)
        self.payment.refresh_from_db();self.assertEqual(self.payment.status,'pending')
    def test_import_and_resolution_require_independent_approval(self):
        self.client.force_authenticate(self.finance)
        file=SimpleUploadedFile('statement.csv',b'reference,amount,currency,transaction_date\nUNKNOWN,100.00,NGN,2026-10-17T10:00:00+01:00\n',content_type='text/csv')
        response=self.client.post(self.url('reconciliation-batches/import'),{'file':file,'source':'Test bank'},format='multipart')
        self.assertEqual(response.status_code,201,response.data)
        item=ReconciliationItem.objects.get(batch_id=response.data['id'])
        response=self.post(f'discrepancies/{item.pk}/request_resolution',{'reason':'Reviewed bank evidence'})
        self.assertEqual(response.status_code,201,response.data)
        approval=response.data['approval']
        self.client.force_authenticate(self.manager)
        self.assertEqual(self.post(f'approvals/{approval}/decide',{'approved':True,'reason':'Independent evidence review'}).status_code,200)
        item.refresh_from_db();self.assertEqual(item.status,'resolved')
    def test_private_attachment_access(self):
        self.client.force_authenticate(self.staff)
        response=self.post('support-tickets',{'subject':'Evidence','category':'Payments','message':'Document for investigation'})
        ticket=response.data['id']
        file=SimpleUploadedFile('evidence.pdf',b'%PDF-1.7\nexample',content_type='application/pdf')
        response=self.client.post(self.url(f'support-tickets/{ticket}/attachments'),{'file':file},format='multipart')
        self.assertEqual(response.status_code,201,response.data)
        pk=response.data['id']
        self.assertEqual(self.client.get(self.url(f'attachments/{pk}')).status_code,200)
        self.client.force_authenticate(self.other)
        self.assertEqual(self.client.get(self.url(f'attachments/{pk}')).status_code,404)
    def test_profile_photo_validation_and_private_reencoding(self):
        from PIL import Image
        import io
        out=io.BytesIO();Image.new('RGB',(20,20)).save(out,format='PNG')
        self.client.force_authenticate(self.staff)
        response=self.client.post(self.url('profile/photo'),{'file':SimpleUploadedFile('photo.png',out.getvalue(),content_type='image/png')},format='multipart')
        self.assertEqual(response.status_code,201,response.data)
        response=self.client.get(self.url('profile/photo'))
        self.assertEqual(response['Content-Type'],'image/jpeg')
        self.client.force_authenticate(self.other)
        self.assertEqual(self.client.get(self.url('profile/photo')).status_code,404)
    def test_settlement_manual_recording_and_report(self):
        self.client.force_authenticate(self.finance)
        response=self.post('settlements',{'provider':'Bank','settlement_reference':'TEST-SET-1','settlement_date':str(timezone.localdate()),'amount':'1200','currency':'NGN'})
        self.assertEqual(response.status_code,201,response.data)
        self.assertEqual(self.post('settlements',{'provider':'Bank','settlement_reference':'TEST-SET-1','settlement_date':str(timezone.localdate()),'amount':'1200'}).status_code,400)
        self.assertEqual(self.client.get(self.url('reports/settlements')).data['summary']['records'],1)
