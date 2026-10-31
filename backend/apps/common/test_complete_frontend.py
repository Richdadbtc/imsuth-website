"""Behavioral replacements for retired Django form/template tests (migration documented)."""
from datetime import timedelta
from decimal import Decimal
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient
from apps.accounts.models import User
from apps.billing.models import BillingCorrectionRequest,Invoice
from apps.catalogue.models import Department,Service,TariffVersion
from apps.operations.models import Notification,NotificationRecipient,ReconciliationBatch
from apps.registry.models import Patient,PatientRevision


class CompleteFrontendTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.department=Department.objects.create(code='SYN-FE',name='Synthetic Frontend')
        cls.service=Service.objects.create(department=cls.department,code='SYN-FE-01',name='Synthetic Consultation')
        cls.admin=User.objects.create_user(username='frontend-admin',role='super_admin',is_superuser=True)
        cls.finance=User.objects.create_user(username='frontend-finance',role='finance')
        cls.manager=User.objects.create_user(username='frontend-manager',role='management')
        cls.front_desk=User.objects.create_user(username='frontend-desk',role='front_desk',department=cls.department)
        cls.tariff=TariffVersion.objects.create(service=cls.service,amount='1800',effective_from=timezone.now()-timedelta(hours=1),is_approved=True)
        cls.patient=Patient.objects.create(first_name='Synthetic',last_name='Frontend',registered_by=cls.front_desk)
        cls.invoice=Invoice.create_from_items(patient=cls.patient,department=cls.department,item_requests=[{'service':cls.service}],created_by=cls.front_desk)
    def setUp(self):self.api=APIClient();self.api.force_authenticate(self.front_desk)
    def test_authenticated_catalogue_profile_and_print_screens_render(self):
        for path in ['departments',f'departments/{self.department.pk}','services',f'services/{self.service.pk}','tariffs','profile',f'invoices/{self.invoice.pk}']:
            self.assertEqual(self.api.get('/api/v1/'+path+'/').status_code,200,path)
        self.client.force_login(self.front_desk)
        for name in ['department-list','service-list','tariff-list','profile','password_change']:
            response=self.client.get(reverse(name),follow=True)
            self.assertEqual(response.status_code,200);self.assertContains(response,'name="viewport"')
        # Unpaid invoices have no official paid receipt and old object print form is retired.
        self.assertEqual(self.client.get(reverse('invoice-print',args=[self.invoice.pk])).status_code,410)
    def test_admin_staff_and_catalogue_controls_are_role_restricted(self):
        self.assertEqual(self.api.get('/api/v1/users/').status_code,403)
        self.assertEqual(self.api.post('/api/v1/departments/',{'code':'DENY','name':'Denied'},format='json').status_code,403)
        self.api.force_authenticate(self.admin)
        self.assertEqual(self.api.get('/api/v1/users/').status_code,200)
        result=self.api.post('/api/v1/services/',{'department':str(self.department.pk),'code':'SYN-FE-02','name':'Synthetic Imaging'},format='json')
        self.assertEqual(result.status_code,201,result.data)
    def test_finance_can_create_immutable_tariff_version(self):
        self.api.force_authenticate(self.finance)
        proposal=self.api.post(f'/api/v1/services/{self.service.pk}/tariff-proposals/',{'amount':'2000','effective_from':(timezone.now()+timedelta(days=1)).isoformat(),'reason':'Synthetic tariff policy'},format='json')
        self.assertEqual(proposal.status_code,201,proposal.data)
        url=f"/api/v1/tariff-proposals/{proposal.data['id']}/approve/"
        self.assertEqual(self.api.post(url,{'notes':'Self approval forbidden'},format='json').status_code,403)
        self.api.force_authenticate(self.manager)
        self.assertEqual(self.api.post(url,{'notes':'Independent synthetic review'},format='json').status_code,200)
        self.assertEqual(self.invoice.items.get().unit_amount,Decimal('1800'))
        self.assertEqual(TariffVersion.objects.filter(service=self.service,is_approved=True).count(),2)
    def test_billing_correction_creates_request_without_mutating_invoice(self):
        result=self.api.post(f'/api/v1/invoices/{self.invoice.pk}/corrections/',{'reason':'Synthetic correction request','requested_change':{'requested_action':'void'}},format='json')
        self.assertEqual(result.status_code,201,result.data)
        self.invoice.refresh_from_db();self.assertEqual(self.invoice.total_amount,Decimal('1800'))
        self.assertEqual(BillingCorrectionRequest.objects.filter(invoice=self.invoice).count(),1)
    def test_multi_line_invoice_is_calculated_by_backend_tariffs(self):
        other=Service.objects.create(department=self.department,code='SYN-FE-03',name='Synthetic Lab')
        TariffVersion.objects.create(service=other,amount='700',effective_from=timezone.now()-timedelta(hours=1),is_approved=True)
        result=self.api.post('/api/v1/invoices/',{'patient':str(self.patient.pk),'department':str(self.department.pk),'idempotency_key':'frontend-multiline','items':[{'service':str(self.service.pk),'quantity':2},{'service':str(other.pk),'quantity':3}]},format='json')
        self.assertEqual(result.status_code,201,result.data)
        self.assertEqual(Decimal(result.data['total_amount']),Decimal('5700'))
        self.assertEqual(len(result.data['line_items']),2)
    def test_reconciliation_import_and_notification_are_user_scoped(self):
        alert=Notification.objects.create(event_type='synthetic.alert',subject='Synthetic alert',body='Synthetic only')
        own=NotificationRecipient.objects.create(notification=alert,user=self.finance)
        other=NotificationRecipient.objects.create(notification=alert,user=self.manager)
        self.api.force_authenticate(self.finance)
        self.assertEqual(self.api.get('/api/v1/inbox/').data['count'],1)
        self.assertEqual(self.api.get(f'/api/v1/inbox/{other.pk}/').status_code,404)
        self.assertEqual(self.api.post(f'/api/v1/inbox/{own.pk}/read/').status_code,200)
        own.refresh_from_db();self.assertIsNotNone(own.read_at)
        upload=SimpleUploadedFile('synthetic.csv',b'reference,amount,currency,transaction_date\nUNKNOWN-SYN,100.00,NGN,2026-10-10T12:00:00+01:00\n',content_type='text/csv')
        result=self.api.post('/api/v1/reconciliation-batches/import/',{'source':'synthetic-bank','file':upload},format='multipart')
        self.assertEqual(result.status_code,201,result.data)
        self.assertTrue(ReconciliationBatch.objects.filter(source='synthetic-bank').exists())
    def test_patient_directory_filters_and_metrics_render(self):
        patient=Patient.objects.create(first_name='Filter',last_name='Match',status=Patient.Status.DUPLICATE_REVIEW,registered_by=self.front_desk)
        result=self.api.get('/api/v1/patients/',{'search':'Filter','status':Patient.Status.DUPLICATE_REVIEW})
        self.assertEqual(result.status_code,200);self.assertEqual(result.data['count'],1)
        self.assertEqual(result.data['results'][0]['patient_id'],patient.patient_id)
    def test_patient_edit_creates_audit_revision(self):
        result=self.api.patch(f'/api/v1/patients/{self.patient.pk}/',{'middle_name':'Updated'},format='json')
        self.assertEqual(result.status_code,200,result.data)
        revision=PatientRevision.objects.get(patient=self.patient)
        self.assertEqual(revision.changed_by,self.front_desk);self.assertEqual(revision.before['middle_name'],'');self.assertEqual(revision.after['middle_name'],'Updated')
    def test_management_dashboard_renders_live_native_chart_data(self):
        self.api.force_authenticate(self.finance)
        summary=self.api.get('/api/v1/dashboard/summary/')
        self.assertEqual(summary.status_code,200);self.assertIn('verified_collections',summary.data)
        self.assertEqual(self.api.get('/api/v1/dashboard/trends/').status_code,200)
        self.assertEqual(self.api.get('/api/v1/dashboard/collections-by-department/').status_code,200)
        self.client.force_login(self.finance)
        self.assertRedirects(self.client.get(reverse('management-dashboard')),'/paypoint/#dashboard-overview-preview')
