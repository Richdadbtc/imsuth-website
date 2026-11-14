from django.test import TestCase
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from apps.auditlog.models import AuditEvent
from .page_access import allowed_pages
User=get_user_model()

class PageAccessTests(TestCase):
    def setUp(self):
        self.admin=User.objects.create_superuser(username='page-admin',password='Synthetic-Page-Secret-29!',role='super_admin')
        self.cashier=User.objects.create_user(username='page-cashier',password='Synthetic-Page-Secret-29!',role='cashier')
        self.client=APIClient();self.client.force_login(self.admin)
    def test_admin_creates_edits_and_audits_restricted_page_access(self):
        result=self.client.post('/api/v1/users/',{'username':'limited-page','role':'cashier','page_access':['dashboard-record-payment'],'password':'Synthetic-Page-Secret-29!'},format='json')
        self.assertEqual(result.status_code,201,result.data)
        user=User.objects.get(pk=result.data['id']);self.assertEqual(user.page_access,['dashboard-record-payment'])
        self.assertTrue(AuditEvent.objects.filter(action='user.page_access_created',object_id=str(user.pk)).exists())
        result=self.client.patch(f'/api/v1/users/{user.pk}/',{'page_access':[]},format='json')
        self.assertEqual(result.status_code,200,result.data)
        self.assertTrue(AuditEvent.objects.filter(action='user.page_access_changed',object_id=str(user.pk)).exists())
    def test_invalid_pages_and_role_escalation_rejected(self):
        for pages in [['admin-settings'],['not-a-page'],'dashboard',{'bad':True}]:
            result=self.client.patch(f'/api/v1/users/{self.cashier.pk}/',{'page_access':pages},format='json')
            self.assertEqual(result.status_code,400,result.data)
    def test_session_and_api_deny_hidden_pages_without_client_headers(self):
        self.cashier.page_access=['dashboard-record-payment'];self.cashier.save()
        self.client.force_login(self.cashier)
        session=self.client.get('/api/v1/session/').data
        self.assertIn('dashboard-record-payment',session['user']['allowed_pages'])
        self.assertNotIn('reports',session['user']['allowed_pages'])
        self.assertEqual(self.client.get('/api/v1/session/?page=reports').status_code,403)
        self.assertEqual(self.client.get('/api/v1/session/?page=dashboard-record-payment').status_code,200)
        for prefix in ['/api/v1/','/paypoint/api/v1/']:
            self.assertEqual(self.client.get(prefix+'reports/revenue/').status_code,403)
            self.assertEqual(self.client.get(prefix+'users/').status_code,403)
            self.assertEqual(self.client.get(prefix+'record-payment/').status_code,200)
            self.assertEqual(self.client.post(prefix+'departments/',{'name':'Denied'}).status_code,403)
        self.cashier.page_access=[];self.cashier.save()
        self.assertEqual(self.client.get('/api/v1/record-payment/').status_code,403)
        self.assertEqual(self.client.get('/api/v1/profile/').status_code,200)
        self.assertEqual(self.client.post('/api/v1/users/',{},format='json').status_code,403)
    def test_role_defaults_and_reset_and_superadmin_protection(self):
        self.assertIn('dashboard-record-payment',allowed_pages(self.cashier))
        self.assertNotIn('users-audit',allowed_pages(self.cashier))
        self.cashier.page_access=[];self.cashier.save()
        result=self.client.patch(f'/api/v1/users/{self.cashier.pk}/',{'page_access':None},format='json')
        self.assertEqual(result.status_code,200,result.data)
        self.cashier.refresh_from_db();self.assertIn('dashboard-record-payment',allowed_pages(self.cashier))
        result=self.client.patch(f'/api/v1/users/{self.admin.pk}/',{'page_access':[]},format='json')
        self.assertEqual(result.status_code,400,result.data)
        self.assertEqual(self.client.get('/api/v1/users/page_choices/').status_code,200)
