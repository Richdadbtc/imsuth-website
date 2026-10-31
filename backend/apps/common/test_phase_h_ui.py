"""Phase H behavior retained through current APIs after documented static-UI migration."""
from datetime import timedelta
from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient
from apps.accounts.models import User
from apps.billing.models import Invoice
from apps.catalogue.models import Department,Service,TariffVersion
from apps.registry.models import Patient


class PhaseHUITests(TestCase):
    def setUp(self):
        self.department=Department.objects.create(code='SYN-UI',name='Synthetic UI Department')
        self.service=Service.objects.create(department=self.department,code='SYN-UI-01',name='Synthetic service')
        self.front_desk=User.objects.create_user(username='ui-front-desk',password='safe-test-password',role='front_desk',department=self.department)
        self.cashier=User.objects.create_user(username='ui-cashier',password='safe-test-password',role='cashier',department=self.department)
        self.finance=User.objects.create_user(username='ui-finance',password='safe-test-password',role='finance')
        TariffVersion.objects.create(service=self.service,amount='2500',effective_from=timezone.now()-timedelta(hours=1),is_approved=True)
        self.patient=Patient.objects.create(first_name='Synthetic',last_name='Patient',registered_by=self.front_desk)
        self.api=APIClient()
    def test_login_and_password_reset_templates_render(self):
        self.assertRedirects(self.client.get(reverse('login')),'/paypoint/')
        self.assertRedirects(self.client.get(reverse('password_reset')),'/paypoint/#forgot-password')
        self.assertContains(self.client.get('/paypoint/'),'Welcome Back')
        self.assertFalse(self.api.get('/api/v1/session/').data['authenticated'])
    def test_login_remember_me_controls_session_lifetime(self):
        for remembered in (True,False):
            result=self.api.post('/api/v1/session/login/',{'username':self.front_desk.username,'password':'safe-test-password','remember_me':remembered},format='json')
            self.assertEqual(result.status_code,200)
            self.assertEqual(self.api.session.get_expire_at_browser_close(),not remembered)
            self.api.post('/api/v1/session/logout/')
    def test_front_desk_can_register_patient_and_generate_invoice(self):
        self.api.force_authenticate(self.front_desk)
        result=self.api.post('/api/v1/patients/',{'first_name':'Synthetic','last_name':'Registrant'},format='json')
        self.assertEqual(result.status_code,201)
        result=self.api.post('/api/v1/invoices/',{'patient':str(self.patient.pk),'department':str(self.department.pk),'items':[{'service':str(self.service.pk),'quantity':2}],'idempotency_key':'ui-invoice'},format='json')
        self.assertEqual(result.status_code,201,result.data)
        self.assertEqual(Decimal(result.data['total_amount']),Decimal('5000'))
        self.assertEqual(self.api.get(f"/api/v1/invoices/{result.data['id']}/").status_code,200)
    def test_cashier_can_initiate_but_not_confirm_payment(self):
        invoice=Invoice.create_from_items(patient=self.patient,department=self.department,item_requests=[{'service':self.service}],created_by=self.front_desk)
        self.api.force_authenticate(self.cashier)
        result=self.api.post('/api/v1/payments/',{'invoice':str(invoice.pk),'channel':'online','idempotency_key':'ui-payment'},format='json')
        self.assertEqual(result.status_code,201,result.data)
        self.assertEqual(result.data['status'],'pending')
        self.assertEqual(self.api.post(f"/api/v1/payments/{result.data['id']}/verify/").status_code,503)
        self.assertFalse(invoice.receipts.exists())
    def test_role_restricted_screens_are_enforced_server_side(self):
        self.client.force_login(self.cashier)
        self.assertEqual(self.client.get(reverse('patient-list')).status_code,403)
        self.assertEqual(self.client.get(reverse('management-dashboard')).status_code,403)
        self.client.force_login(self.finance)
        self.assertRedirects(self.client.get(reverse('finance-workspace')),'/paypoint/#finance')
        self.assertRedirects(self.client.get(reverse('audit-log')),'/paypoint/#admin-audit')
    def test_core_templates_render_at_mobile_safe_markup(self):
        self.client.force_login(self.front_desk)
        for name in ['dashboard','patient-list','patient-create','invoice-list','invoice-create']:
            result=self.client.get(reverse(name),follow=True)
            self.assertEqual(result.status_code,200,name)
            self.assertContains(result,'name="viewport"');self.assertContains(result,'Skip to content')
    def test_retired_form_posts_do_not_mutate_or_bypass_csrf(self):
        from django.test import Client
        self.client.force_login(self.front_desk)
        before=Invoice.objects.count()
        self.assertEqual(self.client.post(reverse('invoice-create'),{}).status_code,410)
        self.assertEqual(Invoice.objects.count(),before)
        secured=Client(enforce_csrf_checks=True);secured.force_login(self.front_desk)
        self.assertEqual(secured.post(reverse('invoice-create'),{}).status_code,403)
